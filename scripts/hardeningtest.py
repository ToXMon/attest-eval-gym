"""Offline deploy and public-admission regression tests; never reads .env."""
from __future__ import annotations

import asyncio
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_TEMP = tempfile.TemporaryDirectory(prefix="attest-hardening-")
os.environ["ATTEST_DB"] = str(Path(_TEMP.name) / "test.db")
os.environ["ATTEST_RUNS_DIR"] = str(Path(_TEMP.name) / "runs")

from attest import admission, llm, sandbox, server
from types import SimpleNamespace


class TestClient:
    def __init__(self, app):
        self.app = app

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def request(self, method, path, json=None, content=None, headers=None):
        payload = content if content is not None else globals()["json"].dumps(json).encode()
        messages = []
        delivered = False

        async def receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": payload}
            await asyncio.sleep(0.01)
            return {"type": "http.disconnect"}

        async def send(message):
            messages.append(message)

        scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
                 "method": method, "scheme": "http", "path": path, "raw_path": path.encode(),
                 "query_string": b"", "root_path": "", "server": ("local", 80),
                 "client": ("192.0.2.1", 1234), "headers": [(b"content-type", b"application/json")]
                 + [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]}
        asyncio.run(self.app(scope, receive, send))
        return SimpleNamespace(status_code=next(m["status"] for m in messages
                                               if m["type"] == "http.response.start"))


class HardeningTests(unittest.TestCase):
    def shell(self, code):
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(("VULTR_", "ATTEST_"))}
        return subprocess.run(
            ["bash", "-c", 'source scripts/deploy.sh; ' + code],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=20)

    def preflight(self, extra=""):
        return self.shell("""
SSH_KEY_FILE=scripts/deploy.sh
SSH_KEY_ID=key-1
vultr() {
  if [[ "$2" == /account ]]; then
    printf '%s' '{"account":{"email":"contact@bullynothub.com"}}'
  else
    printf '%s' '{"ssh_key":{"id":"key-1","ssh_key":"ssh-ed25519 AAAA comment"}}'
  fi
}
ssh-keygen() { printf '%s\\n' 'ssh-ed25519 AAAA local-comment'; }
""" + extra + "; preflight")

    def test_preflight(self):
        self.assertEqual(self.preflight().returncode, 0)
        self.assertNotEqual(self.preflight("SSH_KEY_ID=''").returncode, 0)
        self.assertNotEqual(self.preflight("SSH_KEY_ID=wrong").returncode, 0)
        self.assertNotEqual(self.preflight("EXPECTED_EMAIL=wrong@example.com").returncode, 0)
        self.assertEqual(self.preflight("EXPECTED_EMAIL=contact@bullynothub.com").returncode, 0)
        self.assertNotEqual(self.preflight(
            "ssh-keygen() { printf 'ssh-ed25519 BBBB'; }").returncode, 0)
        self.assertNotEqual(self.preflight(
            """vultr() { printf '{"account":{}}'; }""").returncode, 0)

    def test_account_email_without_acct_id(self):
        result = self.preflight()
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.preflight(
            """vultr() { printf '%s' '{"account":{"email":"other@example.com"}}'; }""")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("account email missing or mismatched", result.stderr)

    def test_required_account(self):
        for config in ("EXPECTED_EMAIL=''", "unset EXPECTED_EMAIL",
                       "EXPECTED_EMAIL=other@example.com"):
            result = self.preflight(config + "; vultr() { exit 99; }")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("expected account must be contact@bullynothub.com", result.stderr)
        for account in (
            {"acct_id": 1},
            {"acct_id": 1, "email": None},
            {"acct_id": 1, "email": ""},
            {"acct_id": 1, "email": "other@example.com"},
            {"acct_id": 1, "email": "CONTACT@bullynothub.com"},
            {"acct_id": 1, "email": "contact@bullynothub.com "},
        ):
            payload = json.dumps({"account": account})
            result = self.preflight(
                "vultr() { printf '%s' '" + payload + "'; }")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("account email missing or mismatched", result.stderr)

    def test_required_account_dry_run(self):
        # Remote functions are traps: even an attempted call fails this test.
        traps = "curl() { exit 99; }; ssh() { exit 99; }; vultr() { exit 99; }; "
        result = self.shell(traps + "main --dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("GET /v2/account must return email exactly contact@bullynothub.com (mandatory)",
                      result.stdout)
        self.assertIn("no credentials read", result.stdout)
        for configured in ("", "other@example.com"):
            result = self.shell(traps + "ATTEST_EXPECTED_ACCOUNT_EMAIL='" + configured
                                + "' bash scripts/deploy.sh --dry-run")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("expected account must be contact@bullynothub.com", result.stderr)

    def test_reuse_ownership(self):
        setup = """REUSE_ID=vm-1; vultr() { printf '%s' '{"instance":{"id":"vm-1","main_ip":"192.0.2.1","tags":["attest-ctrl-plane"]}}'; }; """
        valid = """'[{"id":"vm-1","main_ip":"192.0.2.1"}]'"""
        self.assertEqual(self.shell(setup + "verify_reuse " + valid).returncode, 0)
        for bad in ("'[]'", """'[{"id":"other","main_ip":"192.0.2.1"}]'""",
                    """'[{"id":"vm-1","main_ip":"192.0.2.2"}]'""",
                    """'[{"id":"vm-1"},{"id":"vm-2"}]'"""):
            self.assertNotEqual(self.shell(setup + "verify_reuse " + bad).returncode, 0)
        self.assertNotEqual(self.shell(setup + 'REUSE_ID=""; verify_reuse ' + valid).returncode, 0)
        self.assertNotEqual(self.shell(setup + "vultr() { return 1; }; verify_reuse " + valid).returncode, 0)

    def test_bootstrap_and_https(self):
        self.assertNotEqual(self.shell("vm() { return 1; }; verify_bootstrap").returncode, 0)
        self.assertNotEqual(self.shell("""vm() { printf '{"status":"running"}'; }; verify_bootstrap""").returncode, 0)
        self.assertNotEqual(self.shell("""vm() { printf '{"status":"done","runc":{}}'; }; verify_bootstrap""").returncode, 0)
        self.assertEqual(self.shell("""vm() { printf '{"status":"done","runsc":{}}'; }; verify_bootstrap""").returncode, 0)
        self.assertNotEqual(self.shell("curl() { return 1; }; public_health https://demo.trycloudflare.com").returncode, 0)
        self.assertNotEqual(self.shell("""curl() { printf '{"ok":true,"runtime":"runc"}'; }; public_health https://demo.trycloudflare.com""").returncode, 0)
        self.assertNotEqual(self.shell("curl() { return 0; }; public_health http://demo.trycloudflare.com").returncode, 0)
        self.assertEqual(self.shell("""curl() { printf '{"ok":true,"runtime":"runsc"}'; }; public_health https://demo.trycloudflare.com""").returncode, 0)

    def test_seed_gate(self):
        self.assertNotEqual(self.shell("""vm() { printf '{"rows":[]}'; }; verify_seed""").returncode, 0)

    def test_health_fail_closed(self):
        result = self.shell("vm() { return 1; }; sleep() { :; }; wait_health")
        self.assertNotEqual(result.returncode, 0)
        result = self.shell("""vm() { printf '{"ok":true,"runtime":"runc"}'; }; sleep() { :; }; wait_health""")
        self.assertNotEqual(result.returncode, 0)
        result = self.shell("""vm() { printf '{"ok":true,"runtime":"runsc"}'; }; wait_health""")
        self.assertEqual(result.returncode, 0)

    def test_manifest_exclusions(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            target = Path(directory) / "target"
            source.mkdir()
            target.mkdir()
            names = ["attest/good.py", "requirements.txt", ".env", "attest/a.db",
                     "attest/a.db-wal", "attest/a.db-shm", "attest/a.sqlite3-wal",
                     "attest/runs/old.json", "attest/quarantine/old.json",
                     "attest/screenshots/old.png", "attest/__pycache__/x.pyc",
                     ".agents/state", "attest/secret.key", "other.txt"]
            for name in names:
                file = source / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text("SYNTHETIC_SECRET_CONTENT")
            (source / "attest/link.py").symlink_to(source / ".env")
            result = self.shell(
                f'rsync "${{RSYNC_ARGS[@]}}" --dry-run --out-format="%n" "{source}/" "{target}/"')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("attest/good.py", result.stdout)
            self.assertIn("requirements.txt", result.stdout)
            self.assertNotIn("SYNTHETIC_SECRET_CONTENT", result.stdout)
            for forbidden in names[2:]:
                self.assertNotIn(forbidden, result.stdout)
            self.assertNotIn("attest/link.py", result.stdout.splitlines())
            self.assertIn('skipping non-regular file "attest/link.py"', result.stdout)

    def test_gvisor_requirement(self):
        with patch.dict(os.environ, {"REQUIRE_GVISOR": "1"}), \
             patch.object(sandbox, "detect_runtime", return_value="runc"), \
             patch.object(sandbox.subprocess, "run") as execute:
            with self.assertRaises(sandbox.SandboxError):
                sandbox.run_code("print(1)")
            with self.assertRaises(sandbox.SandboxError):
                sandbox.run_code("print(1)", runtime="runc")
            execute.assert_not_called()

    def test_atomic_concurrency_and_rate(self):
        guard = admission.Admission(concurrent=2, per_minute=3)
        barrier = threading.Barrier(20)

        def attempt(i):
            barrier.wait()
            try:
                return guard.acquire(str(i))
            except admission.LimitError:
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
            leases = [v for v in pool.map(attempt, range(20)) if v]
        self.assertEqual(len(leases), 2)
        for lease in leases:
            lease.release()
            lease.release()
        self.assertEqual(guard.active, 0)
        for _ in range(3):
            guard.acquire("same").release()
        with self.assertRaises(admission.LimitError):
            guard.acquire("same")
        daily = admission.Admission(daily_jobs=1)
        daily.acquire("a").release()
        with self.assertRaises(admission.LimitError):
            daily.acquire("b")

    def test_spend_atomic_and_actual(self):
        budget = admission.SpendBudget(0.1, 0.1)

        def attempt(_):
            try:
                budget.reserve(0.03)
                return True
            except admission.LimitError:
                return False

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
            self.assertEqual(sum(pool.map(attempt, range(20))), 3)
        budget = admission.SpendBudget(0.1, 0.1)
        ticket = budget.reserve(0.01)
        budget.settle(ticket, 0.2)
        with self.assertRaises(admission.LimitError):
            budget.reserve(0.001)
        for bad in (float("nan"), float("inf"), -1):
            with self.assertRaises(ValueError):
                admission.SpendBudget(bad, 1)

    def test_transport_reserves_each_retry(self):
        import urllib.error
        budget = admission.SpendBudget(1, 1)
        with patch.object(admission, "SPEND", budget), \
             patch.object(llm, "API_KEY", "synthetic"), \
             patch.object(llm, "provider_opener") as opener, \
             patch.object(llm.time, "sleep"):
            opener.return_value.open.side_effect = urllib.error.URLError("offline")
            with self.assertRaises(Exception):
                llm._post("chat/completions", {"model": llm.MODEL_SUITE}, retries=3)
            self.assertEqual(opener.return_value.open.call_count, 3)
            estimate = llm.estimate_cost_usd(llm.MODEL_SUITE, len(json.dumps(
                {"model": llm.MODEL_SUITE, "max_tokens": 4096}).encode()) + 4096)
            self.assertAlmostEqual(budget.total, estimate * 3)
        with patch.object(admission, "SPEND", admission.SpendBudget(0, 0)), \
             patch.object(llm, "API_KEY", "synthetic"), patch.object(llm, "provider_opener") as opener:
            with self.assertRaises(admission.LimitError):
                llm._post("chat/completions", {})
            opener.assert_not_called()

    def test_http_hostile_inputs_and_rate(self):
        with patch.object(admission, "ADMISSION", admission.Admission(per_minute=50)), \
             patch.object(llm, "chat", side_effect=AssertionError("no inference")), \
             TestClient(server.app) as client:
            self.assertEqual(client.post("/api/run", json={"tasks": ["x"] * 17}).status_code, 422)
            self.assertEqual(client.post("/api/run", json={"tasks": ["task-sum"] * 12}).status_code, 400)
            self.assertEqual(client.post("/api/suite", json={"generate": True, "n_task": 12,
                "n_adversarial": 12, "n_containment": 12}).status_code, 400)
            self.assertEqual(client.post("/api/run", content=b"x" * 32769).status_code, 413)
            self.assertEqual(client.post("/api/run", content=b"{bad").status_code, 422)
            self.assertEqual(admission.ADMISSION.active, 0)
        with patch.object(admission, "ADMISSION", admission.Admission(per_minute=1)), \
             TestClient(server.app) as client:
            self.assertEqual(client.post("/api/suite", json={}).status_code, 200)
            self.assertEqual(client.post("/api/suite", json={}, headers={
                "X-Forwarded-For": "different"}).status_code, 429)
            self.assertEqual(client.get("/api/selftest").status_code, 429)

    def test_background_lease(self):
        entered, finish = threading.Event(), threading.Event()

        def slow(*args, **kwargs):
            entered.set()
            finish.wait(5)
            raise RuntimeError("offline stub")

        guard = admission.Admission(concurrent=1, per_minute=50)
        with patch.object(admission, "ADMISSION", guard), \
             patch.object(server.gym, "run_suite", side_effect=slow), \
             TestClient(server.app) as client:
            try:
                self.assertEqual(client.post("/api/run", json={}).status_code, 200)
                self.assertTrue(entered.wait(2))
                self.assertEqual(guard.active, 1)
                self.assertEqual(client.post("/api/run", json={}).status_code, 429)
            finally:
                finish.set()
        import time
        for _ in range(100):
            if guard.active == 0:
                break
            time.sleep(0.01)
        self.assertEqual(guard.active, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
