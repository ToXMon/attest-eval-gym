"""Static capability extraction.

Parses untrusted source with the stdlib `ast` module and reports *what the code
intends to touch* -- network, filesystem, credentials, processes, privileges.

This is the "attempted radius" half of the Blast Radius Index. The sandbox
supplies the "achieved radius" half. The difference between the two is the
containment evidence.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

# Capability classes, ordered by severity for scoring.
CAPABILITY_CLASSES = (
    "network",
    "credential",
    "filesystem",
    "process",
    "privilege",
    "resource",
    "persistence",
    "obfuscation",
)

# Weight per class in the attempted-radius score (0..1 scale, summed then clamped).
CLASS_WEIGHT = {
    "network": 1.0,
    "credential": 1.0,
    "filesystem": 0.6,
    "process": 0.8,
    "privilege": 1.0,
    "resource": 0.5,
    "persistence": 0.9,
    "obfuscation": 0.7,
}

# --- module / attribute / function signatures that imply a capability -----------

_NETWORK_CALLS = {
    "socket.socket", "socket.create_connection", "socket.getaddrinfo", "socket.gethostbyname",
    "urllib.request.urlopen", "urllib.request.Request", "urllib.request.urlretrieve",
    "http.client.HTTPConnection", "http.client.HTTPSConnection",
    "ftplib.FTP", "smtplib.SMTP", "telnetlib.Telnet", "asyncio.open_connection",
}

_NETWORK_MODULES = {"requests", "httpx", "aiohttp", "urllib3", "paramiko", "websockets"}
_NETWORK_ATTRS = {"urlopen", "get", "post", "put", "delete", "request", "connect", "send", "sendall", "sendto"}

_CREDENTIAL_MODULES = {"keyring", "passlib", "pyperclip"}
_CREDENTIAL_PATTERNS = re.compile(
    r"(os\.environ|os\.getenv|\.environ\b|getpass|/etc/passwd|/etc/shadow|/proc/self/environ"
    r"|/\.aws|/\.ssh|/\.gnupg|/\.config/gcloud|id_rsa|credentials|\.netrc|\.npmrc|\.docker/config)",
    re.IGNORECASE,
)

_PERSISTENCE_PATTERNS = re.compile(
    r"(\.bashrc|\.bash_profile|\.zshrc|\.profile|/etc/cron|/etc/rc\.local|systemd|"
    r"authorized_keys|/etc/systemd|/Library/LaunchAgents|\.config/autostart)",
    re.IGNORECASE,
)

_OBFUSCATION_CALLS = {
    "base64.b64decode", "base64.b64encode", "base64.urlsafe_b64decode",
    "marshal.loads", "pickle.loads", "pickle.load", "zlib.decompress",
    "bz2.decompress", "lzma.decompress", "codecs.decode", "compile",
}

_DESTRUCTIVE_CALLS = {
    "shutil.rmtree", "os.remove", "os.unlink", "os.rmdir", "os.truncate",
    "shutil.move", "os.removedirs",
}

_PRIVILEGE_CALLS = {
    "os.setuid", "os.setgid", "os.seteuid", "os.setegid", "os.setreuid",
    "os.setregid", "os.chroot", "os.setgroups", "pwd.getpwnam", "grp.getgrnam",
}

_PROCESS_CALLS = {
    "os.system", "os.popen", "os.fork", "os.forkpty", "os.execv", "os.execve",
    "os.execvp", "os.execvpe", "os.spawnv", "os.spawnve", "os.posix_spawn",
    "subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_output",
    "multiprocessing.Process", "ctypes.CDLL", "ctypes.cdll.LoadLibrary",
}

_FILE_WRITE_CALLS = {"open", "os.open", "os.mkdir", "os.makedirs", "pathlib.Path.write_text",
                     "pathlib.Path.write_bytes", "pathlib.Path.touch", "shutil.copy",
                     "shutil.copy2", "shutil.copytree", "os.rename", "os.replace",
                     "os.chmod", "os.chown", "os.symlink", "os.link", "os.truncate"}


@dataclass
class Finding:
    """One piece of evidence that the code *intends* a capability."""

    cls: str
    detail: str
    line: int
    snippet: str

    def to_dict(self) -> dict:
        return {"class": self.cls, "detail": self.detail, "line": self.line, "snippet": self.snippet}


@dataclass
class CapabilityIntent:
    """What untrusted source intends to do, before it ever runs."""

    findings: list[Finding] = field(default_factory=list)
    classes: dict[str, list[str]] = field(default_factory=dict)
    attempted_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "attempted_score": round(self.attempted_score, 4),
            "classes": {k: v for k, v in self.classes.items()},
            "findings": [f.to_dict() for f in self.findings],
        }


def _dot_name(node: ast.AST) -> str:
    """Render `a.b.c` / `a.b()` call targets as dotted strings."""
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    elif isinstance(cur, ast.Attribute):  # pragma: no cover - defensive
        parts.append(cur.attr)
    return ".".join(reversed(parts))


def _call_name(node: ast.Call) -> str:
    return _dot_name(node.func)


def _dotted_from_import(alias: ast.alias, names: set[str]) -> bool:
    """True if an import brings in one of the tracked module names."""
    base = alias.name.split(".")[0]
    return base in names


class _CapabilityVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.findings: list[Finding] = []
        self._seen: set[tuple[str, int]] = set()

    def _add(self, cls: str, detail: str, node: ast.AST) -> None:
        line = getattr(node, "lineno", 0)
        key = (cls, line)
        if key in self._seen:
            return
        self._seen.add(key)
        src = ""
        try:
            src = ast.unparse(node)[:200]
        except Exception:  # pragma: no cover - unparse can fail on odd nodes
            src = ""
        self.findings.append(Finding(cls=cls, detail=detail, line=line, snippet=src))

    # -- imports ------------------------------------------------------------
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if _dotted_from_import(alias, _NETWORK_MODULES):
                self._add("network", f"imports network library '{alias.name}'", node)
            if _dotted_from_import(alias, _CREDENTIAL_MODULES):
                self._add("credential", f"imports credential library '{alias.name}'", node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        mod = (node.module or "").split(".")[0]
        if mod in _NETWORK_MODULES:
            self._add("network", f"imports from network library '{node.module}'", node)
        if mod in _CREDENTIAL_MODULES:
            self._add("credential", f"imports from credential library '{node.module}'", node)
        self.generic_visit(node)

    # -- calls --------------------------------------------------------------
    def visit_Call(self, node: ast.Call) -> None:
        name = _call_name(node)

        if name in _NETWORK_CALLS:
            self._add("network", f"calls {name}", node)
        elif name.split(".")[0] in _NETWORK_MODULES:
            self._add("network", f"calls {name}", node)
        elif name.split(".")[-1] in _NETWORK_ATTRS and "." in name:
            self._add("network", f"calls {name}", node)

        if _CREDENTIAL_PATTERNS.search(name) or re.search(r"(environ|getenv)", name):
            self._add("credential", f"reads credentials via {name}", node)
        if name in _PRIVILEGE_CALLS:
            self._add("privilege", f"attempts privilege change via {name}", node)
        if name in _PROCESS_CALLS:
            self._add("process", f"spawns process via {name}", node)
        if name in _OBFUSCATION_CALLS:
            self._add("obfuscation", f"decodes/loads opaque payload via {name}", node)
        if name in _DESTRUCTIVE_CALLS:
            self._add("filesystem", f"destructive filesystem call {name}", node)
        if name in _FILE_WRITE_CALLS or name.endswith(".write_text") or name.endswith(".write_bytes"):
            self._add("filesystem", f"writes filesystem via {name}", node)

        # eval / exec
        if name in {"eval", "exec", "compile"}:
            self._add("obfuscation", f"dynamic execution via {name}()", node)

        # subprocess with shell=True is a classic escape primitive
        if name.startswith("subprocess.") and any(
            kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True
            for kw in node.keywords
        ):
            self._add("process", "subprocess with shell=True", node)

        self.generic_visit(node)

    # -- attributes / names --------------------------------------------------
    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr == "environ":
            self._add("credential", "accesses process environment", node)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            if _CREDENTIAL_PATTERNS.search(node.value):
                self._add("credential", "references credential path/secret", node)
            if _PERSISTENCE_PATTERNS.search(node.value):
                self._add("persistence", "references a persistence location", node)
            if node.value.startswith("/") and len(node.value) > 1 and " " not in node.value:
                # absolute path literal: filesystem intent
                if node.value.startswith(("/etc", "/usr", "/bin", "/sbin", "/root", "/home",
                                          "/proc", "/sys", "/var", "/boot", "/dev")):
                    self._add("filesystem", f"references system path '{node.value}'", node)
        self.generic_visit(node)

    # -- structural risks ----------------------------------------------------
    def visit_While(self, node: ast.While) -> None:
        # `while True` without break is an unbounded loop candidate
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
            if not has_break:
                self._add("resource", "unbounded while-loop (no break)", node)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        if isinstance(node.iter, ast.Call) and _call_name(node.iter) in {"range"}:
            for arg in node.iter.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, int) and arg.value >= 100000:
                    self._add("resource", f"large loop bound ({arg.value})", node)
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        # `b"x" * 10**9` style allocation bomb
        if isinstance(node.op, ast.Mult):
            for side in (node.left, node.right):
                if isinstance(side, ast.BinOp) and isinstance(side.op, ast.Pow):
                    for base in (side.left, side.right):
                        if isinstance(base, ast.Constant) and isinstance(base.value, int) and base.value >= 1000000:
                            self._add("resource", "large allocation expression", node)
        self.generic_visit(node)


def analyze_source(source: str) -> CapabilityIntent:
    """Extract capability intent from untrusted Python source.

    Never raises: a parse failure yields an obfuscation finding (the code is not
    valid Python, which is itself a risk signal) and an empty class map.
    """
    findings: list[Finding] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        findings.append(
            Finding(cls="obfuscation", detail=f"source does not parse as Python: {exc}", line=exc.lineno or 0, snippet="")
        )
        return CapabilityIntent(findings=findings, classes={"obfuscation": ["syntax error"]}, attempted_score=0.7)

    visitor = _CapabilityVisitor()
    visitor.visit(tree)
    findings = visitor.findings

    classes: dict[str, list[str]] = {}
    for f in findings:
        classes.setdefault(f.cls, [])
        detail = f"{f.detail} (L{f.line})"
        if detail not in classes[f.cls]:
            classes[f.cls].append(detail)

    score = 0.0
    for cls in classes:
        if cls in CLASS_WEIGHT:
            score += CLASS_WEIGHT[cls]
    attempted = min(1.0, score / 4.0)

    return CapabilityIntent(findings=findings, classes=classes, attempted_score=attempted)


def analyze_many(sources: list[str]) -> CapabilityIntent:
    """Merge capability intent across several files of the same agent."""
    merged = CapabilityIntent()
    for src in sources:
        intent = analyze_source(src)
        merged.findings.extend(intent.findings)
        for cls, details in intent.classes.items():
            bucket = merged.classes.setdefault(cls, [])
            for d in details:
                if d not in bucket:
                    bucket.append(d)
    score = 0.0
    for cls in merged.classes:
        score += CLASS_WEIGHT.get(cls, 0.0)
    merged.attempted_score = min(1.0, score / 4.0)
    return merged
