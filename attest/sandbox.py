"""Hardened sandbox runner.

Every execution of untrusted code happens in a disposable container that is
locked down as tightly as the kernel allows:

  * no network namespace at all
  * read-only root filesystem, writable tmpfs workdir only
  * all capabilities dropped, no-new-privileges, non-root uid
  * hard caps on memory, CPU, PIDs, wall clock, stdout size and artifact size
  * no host mounts, no environment inherited, no Docker socket

The literal `docker run` invocation is captured in the result so the security
claim is auditable rather than asserted.

Runtime is gVisor (`runsc`) when the host provides it, falling back to `runc`.
"""

from __future__ import annotations

import base64
import io
import json
import os
import shutil
import subprocess
import tarfile
import time
from dataclasses import dataclass, field

DEFAULT_IMAGE = "python:3.12-slim"
DEFAULT_RUNTIME = "runsc"  # gVisor
FALLBACK_RUNTIME = "runc"

# Resource caps (tuned for a vc2-2c-4gb control plane).
MEMORY_LIMIT = "512m"
MEMORY_SWAP = "512m"  # equal to memory => swap disabled
CPU_QUOTA = 100000  # 1.0 CPU
CPU_PERIOD = 100000
PIDS_LIMIT = 128
NPROC_ULIMIT = 64
FSIZE_ULIMIT = 10 * 1024 * 1024  # 10 MiB per-file
NOFILE_ULIMIT = 256
WALL_CLOCK_SECONDS = 20
MAX_STDOUT_BYTES = 256 * 1024
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024
MAX_ARTIFACTS = 25
WORKDIR = "/work"
TMPFS = "/tmp:rw,noexec,nosuid,size=64m,mode=1777"
# The workdir must be writable by the unprivileged uid we run as.
WORKDIR_TMPFS = f"{WORKDIR}:rw,exec,size=64m,mode=1777"

# Sentinel that separates the task's stdout from the artifact dump.
ARTIFACT_SENTINEL = "__ARTIFACT_SENTINEL__"

# Runs inside the container. It executes the untrusted program, then dumps the
# workdir as a gzipped tarball on stdout. `docker cp` cannot see a tmpfs mount,
# so the container has to hand its own artifacts back.
_WRAPPER = r'''
import base64, io, os, sys, tarfile

_src = sys.stdin.read()
_work = "/work"
try:
    _g = {"__name__": "__main__", "__file__": _work + "/_task.py", "__builtins__": __builtins__}
    exec(compile(_src, _work + "/_task.py", "exec"), _g)
    _code = 0
except SystemExit as _e:
    _code = _e.code if isinstance(_e.code, int) else 0
except BaseException as _e:
    _code = 1
    sys.stderr.write("%s: %s\n" % (type(_e).__name__, _e))
    sys.stderr.flush()

_buf = io.BytesIO()
try:
    with tarfile.open(fileobj=_buf, mode="w:gz") as _tf:
        for _name in sorted(os.listdir(_work)):
            _p = os.path.join(_work, _name)
            if _name == "_task.py" or not os.path.isfile(_p):
                continue
            try:
                _tf.add(_p, arcname=_name)
            except Exception:
                pass
except Exception:
    pass

sys.stdout.write("\n" + "__ARTIFACT_SENTINEL__" + base64.b64encode(_buf.getvalue()).decode() + "\n")
sys.stdout.flush()
os._exit(_code if isinstance(_code, int) and 0 <= _code < 256 else 1)
'''


@dataclass
class Artifact:
    path: str
    size: int
    sha256: str
    truncated: bool = False

    def to_dict(self) -> dict:
        return {"path": self.path, "size": self.size, "sha256": self.sha256, "truncated": self.truncated}


@dataclass
class SandboxResult:
    """Everything the control plane needs to judge one execution."""

    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False
    oom_killed: bool = False
    pids_exhausted: bool = False
    output_truncated: bool = False
    artifacts: list[Artifact] = field(default_factory=list)
    artifacts_dropped: int = 0
    image: str = DEFAULT_IMAGE
    runtime: str = DEFAULT_RUNTIME
    command: list[str] = field(default_factory=list)
    docker_args: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out and not self.oom_killed

    def to_dict(self) -> dict:
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "timed_out": self.timed_out,
            "oom_killed": self.oom_killed,
            "pids_exhausted": self.pids_exhausted,
            "output_truncated": self.output_truncated,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "artifacts_dropped": self.artifacts_dropped,
            "image": self.image,
            "runtime": self.runtime,
            "command": self.command,
            "docker_args": self.docker_args,
            "errors": self.errors,
        }


class SandboxError(RuntimeError):
    pass


def detect_runtime() -> str:
    """Prefer gVisor's runsc; fall back to runc if the host cannot provide it."""
    if shutil.which("docker") is None:
        raise SandboxError("docker CLI not found on PATH")
    try:
        out = subprocess.run(
            ["docker", "info", "--format", "{{json .Runtimes}}"],
            capture_output=True, text=True, timeout=20, check=True,
        ).stdout
        runtimes = json.loads(out or "{}")
    except Exception:
        return FALLBACK_RUNTIME
    if DEFAULT_RUNTIME in runtimes:
        return DEFAULT_RUNTIME
    return FALLBACK_RUNTIME


def _sha256(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def _run(cmd: list[str], timeout: int) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def _decode_artifacts(blob_b64: str) -> tuple[list[Artifact], int]:
    """Decode the gzipped tarball the wrapper produced."""
    artifacts: list[Artifact] = []
    dropped = 0
    try:
        raw = base64.b64decode(blob_b64)
        if not raw:
            return artifacts, dropped
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tf:
            for member in tf.getmembers():
                if not member.isfile():
                    continue
                if member.size > MAX_ARTIFACT_BYTES:
                    dropped += 1
                    continue
                if len(artifacts) >= MAX_ARTIFACTS:
                    dropped += 1
                    continue
                fh = tf.extractfile(member)
                if fh is None:
                    dropped += 1
                    continue
                data = fh.read()
                artifacts.append(Artifact(path=member.name, size=len(data), sha256=_sha256(data)))
    except Exception:
        pass
    artifacts.sort(key=lambda a: a.path)
    return artifacts, dropped


def _inspect(container: str) -> dict:
    try:
        code, out, _ = _run(
            ["docker", "inspect", container, "--format",
             "{{.State.OOMKilled}} {{.State.ExitCode}} {{.State.Error}}"],
            timeout=15,
        )
        if code != 0:
            return {}
        parts = out.strip().split(None, 2)
        return {
            "oom_killed": parts[0].lower() == "true",
            "exit_code": int(parts[1]) if len(parts) > 1 and parts[1].lstrip("-").isdigit() else -1,
            "error": parts[2] if len(parts) > 2 else "",
        }
    except Exception:
        return {}


def run_code(
    source: str,
    *,
    timeout: int = WALL_CLOCK_SECONDS,
    image: str = DEFAULT_IMAGE,
    runtime: str | None = None,
    extra_args: list[str] | None = None,
) -> SandboxResult:
    """Run untrusted Python source in a disposable, locked-down container.

    The source arrives on stdin; nothing is mounted from the host and no
    environment is inherited.
    """
    runtime = runtime or detect_runtime()
    if os.environ.get("REQUIRE_GVISOR") == "1" and runtime != DEFAULT_RUNTIME:
        raise SandboxError("gVisor is required; refusing fallback runtime")
    container = f"attest-run-{os.getpid()}-{int(time.time() * 1000) % 100000}"

    docker_args = [
        "docker", "run",
        "-i",  # keep stdin attached: the program arrives there
        "--name", container,
        "--network", "none",
        "--read-only",
        "--tmpfs", TMPFS,
        "--tmpfs", WORKDIR_TMPFS,
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges:true",
        "--user", "65534:65534",
        "--memory", MEMORY_LIMIT,
        "--memory-swap", MEMORY_SWAP,
        "--cpu-quota", str(CPU_QUOTA),
        "--cpu-period", str(CPU_PERIOD),
        "--pids-limit", str(PIDS_LIMIT),
        "--ulimit", f"nproc={NPROC_ULIMIT}:{NPROC_ULIMIT}",
        "--ulimit", f"fsize={FSIZE_ULIMIT}:{FSIZE_ULIMIT}",
        "--ulimit", f"nofile={NOFILE_ULIMIT}:{NOFILE_ULIMIT}",
        "--workdir", WORKDIR,
        "--env", "HOME=/nonexistent",
        "--env", "PATH=/usr/local/bin:/usr/bin:/bin",
        "--env", "PYTHONDONTWRITEBYTECODE=1",
        "--env", "PYTHONUNBUFFERED=1",
        "--runtime", runtime,
        image, "python", "-I", "-u", "-c", _WRAPPER,
    ]
    if extra_args:
        docker_args += extra_args

    started = time.time()
    timed_out = False
    stdout = stderr = ""
    exit_code = -1

    try:
        proc = subprocess.Popen(
            docker_args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception as exc:  # pragma: no cover - docker missing
        raise SandboxError(f"failed to start container: {exc}") from exc

    try:
        out_b, err_b = proc.communicate(input=source, timeout=timeout)
        stdout, stderr = out_b or "", err_b or ""
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        # Force-kill the container: the wall-clock cap is enforced by us, not by hope.
        _run(["docker", "kill", container], timeout=10)
        try:
            out_b, err_b = proc.communicate(timeout=10)
            stdout, stderr = out_b or "", err_b or ""
        except Exception:
            pass
        exit_code = proc.returncode if proc.returncode is not None else 124
    finally:
        _run(["docker", "rm", "-f", container], timeout=20)

    duration_ms = int((time.time() - started) * 1000)

    # Split the artifact dump off the task's stdout.
    artifacts: list[Artifact] = []
    dropped = 0
    if ARTIFACT_SENTINEL in stdout:
        head, _, tail = stdout.rpartition(ARTIFACT_SENTINEL)
        stdout = head
        b64 = tail.strip().splitlines()[0] if tail.strip() else ""
        artifacts, dropped = _decode_artifacts(b64)
    else:
        # No dump: the program may have hard-exited. Anything left in /work is
        # unreachable, which we report honestly rather than faking.
        dropped = 1

    output_truncated = len(stdout.encode()) > MAX_STDOUT_BYTES
    if output_truncated:
        stdout = stdout.encode()[:MAX_STDOUT_BYTES].decode("utf-8", "replace")
    if len(stderr.encode()) > MAX_STDOUT_BYTES:
        stderr = stderr.encode()[:MAX_STDOUT_BYTES].decode("utf-8", "replace")

    oom = exit_code == 137 and not timed_out
    pids_exhausted = "pids" in (stderr or "").lower() and "limit" in (stderr or "").lower()

    return SandboxResult(
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        duration_ms=duration_ms,
        timed_out=timed_out,
        oom_killed=oom,
        pids_exhausted=pids_exhausted,
        output_truncated=output_truncated,
        artifacts=artifacts,
        artifacts_dropped=dropped,
        image=image,
        runtime=runtime,
        command=docker_args[docker_args.index(image):] if image in docker_args else [],
        docker_args=docker_args,
    )


def probe_self_test() -> list[dict]:
    """Run the built-in attack corpus and report whether each attempt was contained.

    This is the regression suite. It is also what the demo video shows.
    """
    from .attacks import ATTACK_CORPUS

    results: list[dict] = []
    for attack in ATTACK_CORPUS:
        res = run_code(attack.source, timeout=attack.get("timeout", 15))
        contained, evidence = attack.detector(res)
        results.append({
            "id": attack.id,
            "title": attack.title,
            "class": attack.cls,
            "contained": contained,
            "evidence": evidence,
            "exit_code": res.exit_code,
            "duration_ms": res.duration_ms,
        })
    return results
