"""Frozen /api contract test with a stubbed model.

Validates the four endpoints frozen in docs/adal/spec.md plus the OTel export,
without touching a real inference key. The sandbox still runs for real, so
Docker must be available (same requirement as piptest.py).

    python scripts/apitest.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("ATTEST_DB", "/tmp/attest-apitest.db")
# Startup quarantine must never touch the checkout's real historical runs.
import tempfile
_TEST_RUNS = tempfile.TemporaryDirectory(prefix="attest-apitest-startup-")
os.environ["ATTEST_RUNS_DIR"] = _TEST_RUNS.name

from attest import agent as agent_mod                       # noqa: E402
from attest.agent import AgentSpec                          # noqa: E402
from attest import gym                                      # noqa: E402
from attest.ledger import Ledger                            # noqa: E402
from attest.tasks import SEEDED_SUITE                       # noqa: E402
from attest import server as srv                            # noqa: E402
from attest.server import (                                 # noqa: E402
    AgentPayload, EndpointSpec, PromoteRequest, RunRequest,
)
from fastapi import HTTPException                           # noqa: E402

# Reuse piptest's stubbed model so the two scripts stay in sync when the
# seeded suite changes.
import importlib.util                                       # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "piptest", Path(__file__).resolve().parent / "piptest.py")
_piptest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_piptest)
fake_chat = _piptest.fake_chat


# --- the test -------------------------------------------------------------------

FROZEN_TASK_KEYS = (
    "task_id", "variant", "layers", "convergence_score", "model", "latency_ms",
    "tokens", "cost_usd", "p_safe", "ledger_hash", "otel",
)
FROZEN_BOARD_KEYS = (
    "agent_name", "mean_score", "containment_mean", "convergence_mean",
    "total_cost_usd", "mean_latency_ms", "runs",
)


def main() -> int:
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")
        if not cond:
            failures.append(name)

    # All security checks are offline: no DNS lookups or real HTTP requests.
    from unittest.mock import MagicMock, patch
    from attest import llm
    from attest.provider_policy import NoRedirects, validate_provider_url
    import urllib.error
    import urllib.request

    print("=== provider policy and credential isolation (offline) ===")
    bad_urls = [
        "https://example.com/v1", "http://api.vultrinference.com/v1",
        "http://localhost/v1", "https://localhost/v1",
        "https://127.0.0.1/v1", "https://[::1]/v1",
        "https://10.0.0.1/v1", "https://172.16.0.1/v1",
        "https://192.168.1.1/v1", "https://169.254.169.254/v1",
        "https://2130706433/v1", "https://api.vultrinference.com.evil.test/v1",
        "https://visitor:password@api.vultrinference.com/v1",
        "https://api.vultrinference.com:8443/v1",
        "https://api.vultrinference.com/v1?target=http://localhost",
        "https://api.vultrinference.com/v1#fragment",
        "https://api.vultrinference.com/v1/../metadata",
        "https://api.vultrinference.com/v1\n",
    ]
    for url in bad_urls:
        for legacy in (False, True):
            endpoint = {"base_url": url, "model": "stub", "api_key": "visitor-test-key"}
            payload = {"custom": endpoint} if legacy else {
                "agent": {"name": "visitor", "endpoint": endpoint}}
            with patch.object(urllib.request.OpenerDirector, "open",
                              side_effect=AssertionError("Unexpected HTTP request")) as http:
                try:
                    srv.start_run(RunRequest(**payload))
                    rejected = False
                except HTTPException as exc:
                    rejected = exc.status_code == 400
                check(f"reject unsafe URL ({'legacy' if legacy else 'frozen'}) {bad_urls.index(url)}",
                      rejected and not http.called)

    approved = "https://api.vultrinference.com/v1"
    custom = srv._agent_for(RunRequest(agent=AgentPayload(
        name="visitor", endpoint=EndpointSpec(
            base_url=approved, model="stub", api_key="visitor-test-key"))))
    legacy = srv._agent_for(RunRequest(custom={
        "base_url": approved, "model": "stub", "api_key": "legacy-test-key"}))
    check("legacy approved custom keeps visitor key",
          legacy.api_key == "legacy-test-key" and not legacy.use_server_credentials)
    for payload in ({"agent": {"endpoint": {"base_url": approved}}},
                    {"custom": {"base_url": approved, "model": "stub"}}):
        try:
            srv._agent_for(RunRequest(**payload))
            check("custom without own key rejected", False)
        except HTTPException as exc:
            check("custom without own key rejected", exc.status_code == 400)

    raw = {"choices": [{"message": {"content": "offline reply"}}],
           "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5}}
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(raw).encode()
    opener = MagicMock()
    opener.open.return_value = response
    with patch.object(llm, "API_KEY", "server-test-key"), \
         patch.object(llm, "chat", side_effect=AssertionError("Server key path used")) as shared, \
         patch.object(agent_mod, "provider_opener", return_value=opener):
        reply = agent_mod._chat(custom, [{"role": "user", "content": "test"}])
        request = opener.open.call_args.args[0]
        check("approved Vultr custom uses only supplied key",
              request.get_header("Authorization") == "Bearer visitor-test-key"
              and request.full_url == approved + "/chat/completions"
              and reply.total_tokens == 5 and not shared.called)
        check("custom serialization omits key", "visitor-test-key" not in json.dumps(custom.to_dict()))

    refs = [a for a in agent_mod.reference_agents() if a.style != "redteam"]
    check("all built-in model agents use approved Vultr transport",
          all(a.use_server_credentials and validate_provider_url(a.base_url) == approved for a in refs))
    with patch.object(llm, "chat", return_value=llm.Completion(
            text="built-in reply", model="stub")) as shared, \
         patch.object(agent_mod, "provider_opener",
                      side_effect=AssertionError("Custom transport used")):
        reply = agent_mod._chat(refs[0], [])
        check("built-in retains shared Vultr chat path", shared.called and reply.text == "built-in reply")

    with patch.object(llm, "API_KEY", "server-test-key"), \
         patch.object(llm, "BASE_URL", "https://example.com/v1"), \
         patch.object(llm, "provider_opener") as transport:
        try:
            llm._post("chat/completions", {})
            rejected = False
        except ValueError:
            rejected = True
        check("built-in provider override cannot route outside Vultr", rejected and not transport.called)

    with patch.object(llm, "API_KEY", "server-test-key"), \
         patch.object(llm, "BASE_URL", approved), \
         patch.object(llm, "provider_opener", return_value=opener):
        llm.chat("stub", [])
        request = opener.open.call_args.args[0]
        check("built-in shared transport uses server key at Vultr only",
              request.get_header("Authorization") == "Bearer server-test-key"
              and request.full_url == approved + "/chat/completions")

    for code in (301, 302, 303, 307, 308):
        for target in ("https://example.com/x", "http://127.0.0.1/x", approved):
            try:
                NoRedirects().redirect_request(
                    urllib.request.Request(approved), None, code, "redirect", {}, target)
                blocked = False
            except urllib.error.HTTPError:
                blocked = True
            check(f"redirect {code} blocked ({target})", blocked)

    from attest.provider_policy import provider_opener
    from urllib.request import ProxyHandler
    handlers = provider_opener().handlers
    check("production transport installs no-redirect handler",
          any(isinstance(h, NoRedirects) for h in handlers))
    check("production transport has no ambient proxy routes",
          all(not h.proxies for h in handlers if isinstance(h, ProxyHandler)))

    with patch.object(llm, "probe", side_effect=AssertionError("Paid health probe")), \
         patch.object(llm, "chat", side_effect=AssertionError("Paid inference")), \
         patch.object(llm, "API_KEY", "server-test-key"):
        status = srv.health()
        check("health is local configuration only",
              status["inference"] == {"configured": True, "checked": False})

    print("=== public error redaction (offline synthetic credentials) ===")
    import asyncio
    import io
    import tempfile
    import time

    server_secret = "SYNTHETIC_SERVER_KEY_DO_NOT_EXPOSE"
    visitor_secret = "SYNTHETIC_VISITOR_KEY_DO_NOT_EXPOSE"
    echoed = server_secret + " " + visitor_secret
    leak_headers = {"Authorization": "Bearer " + echoed, "X-Echo": echoed}

    def echoed_http_error(*args, **kwargs):
        raise urllib.error.HTTPError(
            approved + "/chat/completions?secret=" + echoed, 401,
            echoed, leak_headers, io.BytesIO(echoed.encode()))

    def no_leak(label, value):
        serialized = value if isinstance(value, str) else json.dumps(value)
        check(label, server_secret not in serialized and visitor_secret not in serialized
              and "Authorization" not in serialized and "X-Echo" not in serialized)

    async def api_request(path, body=None, method="POST"):
        payload = json.dumps(body).encode()
        messages = []
        received = False

        async def receive():
            nonlocal received
            if not received:
                received = True
                return {"type": "http.request", "body": payload, "more_body": False}
            return {"type": "http.disconnect"}

        async def send(message):
            messages.append(message)

        scope = {"type": "http", "asgi": {"version": "3.0"},
                 "http_version": "1.1", "method": method, "scheme": "http",
                 "path": path, "raw_path": path.encode(), "query_string": b"",
                 "headers": [(b"content-type", b"application/json")],
                 "client": ("127.0.0.1", 1), "server": ("testserver", 80)}
        try:
            await srv.app(scope, receive, send)
        except Exception:
            # ServerErrorMiddleware re-raises after sending its safe response.
            if not any(m["type"] == "http.response.start" for m in messages):
                raise
        status = next(m["status"] for m in messages if m["type"] == "http.response.start")
        data = b"".join(m.get("body", b"") for m in messages
                        if m["type"] == "http.response.body").decode()
        return status, data

    with tempfile.TemporaryDirectory(prefix="attest-redaction-") as tmp, \
         patch.object(srv, "RUNS_DIR", Path(tmp)), \
         patch.object(llm, "API_KEY", server_secret), \
         patch.object(llm, "BASE_URL", approved), \
         patch.object(urllib.request.OpenerDirector, "open", side_effect=echoed_http_error):
        for label, spec in (
            ("server", agent_mod.reference_agents()[0]),
            ("visitor", srv._agent_for(RunRequest(agent=AgentPayload(
                name="redaction visitor", endpoint=EndpointSpec(
                    base_url=approved, model="stub", api_key=visitor_secret))))),
        ):
            try:
                agent_mod._chat(spec, [])
                check(label + " provider 401 raises", False)
            except llm.InferenceError as exc:
                check(label + " provider error has fixed code/status",
                      str(exc) == "provider_http_error:401"
                      and exc.code == "provider_http_error" and exc.status == 401)
                no_leak(label + " provider exception safe", repr(exc) + str(exc))
            events = []
            failed_run = gym.run_suite(spec, [SEEDED_SUITE[0]], ledger=srv.LEDGER,
                                       suite_source="offline", on_event=events.append)
            srv.RUNS[failed_run.run_id] = failed_run
            check(label + " failed outcome has exact safe error",
                  failed_run.tasks[0].outcome.error == "provider_http_error:401")
            srv._persist(failed_run)
            surfaces = {
                "run response": srv.get_run(failed_run.run_id),
                "detail": srv.get_run_detail(failed_run.run_id),
                "scorecard": srv.scorecard(failed_run.run_id),
                "OTel": srv.run_otel(failed_run.run_id),
                "events": events,
                "stored run serialization": failed_run.to_dict(),
                "persisted run file": (Path(tmp) / (failed_run.run_id + ".json")).read_text(),
                "evidence": srv.evidence(failed_run.run_id),
            }
            for surface, value in surfaces.items():
                no_leak(label + " " + surface + " excludes echoed keys/headers", value)

        for label, body in (
            ("validation", {"agent": {"endpoint": {
                "base_url": approved, "api_key": {"echo": echoed}}}}),
            ("rejected endpoint", {"agent": {"endpoint": {
                "base_url": "https://example.com/?key=" + echoed, "api_key": visitor_secret}}}),
        ):
            status, payload = asyncio.run(api_request("/api/run", body))
            check(label + " API rejects", status in (400, 422))
            no_leak(label + " API error payload safe", payload)

        with patch.object(gym, "run_suite", side_effect=RuntimeError(echoed)):
            started = srv.start_run(RunRequest(agent=AgentPayload(name="compliant"), tasks=["t01"]))
            deadline = time.monotonic() + 5
            worker_status = srv.get_run(started["run_id"])
            while worker_status.get("status") == "running" and time.monotonic() < deadline:
                time.sleep(0.01)
                worker_status = srv.get_run(started["run_id"])
            check("unexpected worker failure uses fixed code",
                  worker_status.get("error") == "run_worker_failed")
            no_leak("worker polling status safe", worker_status)
            worker_events = []
            while True:
                event = srv.STREAMS[started["run_id"]].get(timeout=5)
                if event is None:
                    break
                worker_events.append(event)
            no_leak("worker events safe", worker_events)

        with patch.object(srv, "_agent_for", side_effect=RuntimeError(echoed)):
            status, payload = asyncio.run(api_request("/api/run", {}))
            check("unexpected API error has fixed response",
                  status == 500 and json.loads(payload) == {"error": "internal_error", "status": 500})
            no_leak("unexpected API error payload safe", payload)

    with patch.object(agent_mod, "_chat", side_effect=RuntimeError(echoed)):
        outcome = agent_mod.solve("test", custom, task_id="t01")
        check("unexpected endpoint error sanitized in memory", outcome.error == "agent_runtime_error")
        no_leak("unexpected endpoint error serialization safe", outcome.to_dict())

    with patch.object(gym, "solve", side_effect=RuntimeError(echoed)):
        runtime_events = []
        runtime_run = gym.run_suite(custom, [SEEDED_SUITE[0]], ledger=srv.LEDGER,
                                    on_event=runtime_events.append)
        check("unexpected runtime outcome sanitized", runtime_run.tasks[0].outcome.error == "agent_runtime_error")
        no_leak("unexpected runtime run/events safe", [runtime_run.to_dict(), runtime_events])

    # Serialization also rejects legacy/arbitrary exception strings.
    outcome.error = echoed
    no_leak("legacy outcome error serialization safe", outcome.to_dict())

    malformed_response = MagicMock()
    malformed_response.__enter__.return_value.read.return_value = json.dumps(
        {"error": echoed, "headers": leak_headers}).encode()
    bad_opener = MagicMock()
    bad_opener.open.return_value = malformed_response
    with patch.object(llm, "API_KEY", server_secret), \
         patch.object(llm, "provider_opener", return_value=bad_opener), \
         patch.object(agent_mod, "provider_opener", return_value=bad_opener), \
         patch.object(agent_mod.time, "sleep"):
        for label, call in (
            ("shared malformed", lambda: llm.chat("stub", [])),
            ("custom malformed", lambda: agent_mod._chat(custom, [])),
            ("JSON parse", lambda: llm.parse_json(echoed)),
        ):
            try:
                call()
                check(label + " rejected", False)
            except Exception as exc:
                check(label + " exception uses stable provider code",
                      type(exc) is llm.InferenceError and str(exc) in (
                          "provider_invalid_response", "provider_request_failed"))
                no_leak(label + " exception safe", str(exc) + repr(exc))

    malformed_response.__enter__.return_value.read.return_value = json.dumps({
        "choices": [{"message": {"content": "reply"}}],
        "usage": {"total_tokens": echoed},
    }).encode()
    with patch.object(llm, "API_KEY", server_secret), \
         patch.object(llm, "provider_opener", return_value=bad_opener):
        try:
            llm.chat("stub", [])
            check("malformed usage rejected", False)
        except Exception as exc:
            check("malformed usage uses stable provider code",
                  type(exc) is llm.InferenceError and str(exc) == "provider_invalid_response")
            no_leak("malformed usage exception safe", repr(exc))

    print("=== successful-output credential redaction (offline) ===")
    from dataclasses import replace
    from attest.errors import redact_secrets, redact_value, secret_scope
    from attest.sandbox import SandboxResult
    check("redaction ignores empty keys and masks exact matches",
          redact_secrets("prefix token suffix", ("", "token")) == "prefix [REDACTED] suffix")
    success_custom = replace(custom, api_key=visitor_secret, max_repairs=0)
    secret_code = "```python\nprint(" + repr(echoed) + ")\n```"
    success_raw = {"choices": [{"message": {"content": secret_code}}],
                   "usage": {"total_tokens": 5}, "debug": echoed}
    success_response = MagicMock()
    success_response.__enter__.return_value.read.return_value = json.dumps(success_raw).encode()
    success_opener = MagicMock()
    success_opener.open.return_value = success_response

    with patch.object(llm, "API_KEY", server_secret), \
         patch.object(llm, "provider_opener", return_value=success_opener), \
         patch.object(agent_mod, "provider_opener", return_value=success_opener), \
         patch.object(agent_mod, "run_code", side_effect=AssertionError("Secret code executed")) as sandbox:
        for label, spec in (("server success", agent_mod.reference_agents()[0]),
                            ("visitor success", success_custom)):
            outcome = agent_mod.solve("test", spec, task_id="t01")
            check(label + " secret-bearing code rejected before sandbox",
                  not sandbox.called and outcome.code == "" and outcome.result is None
                  and outcome.error == "credential_output_rejected")
            no_leak(label + " outcome excludes keys", outcome.to_dict())
        # Even test/custom _chat implementations must pass the pre-execution guard.
        with patch.object(agent_mod, "_chat", return_value=secret_code):
            outcome = agent_mod.solve("test", success_custom, task_id="t01")
            check("direct successful reply guard rejects before sandbox",
                  not sandbox.called and outcome.refused and outcome.code == "")

    with tempfile.TemporaryDirectory(prefix="attest-rejected-code-") as tmp, \
         patch.object(llm, "API_KEY", server_secret), \
         patch.object(srv, "RUNS_DIR", Path(tmp)), \
         patch.object(llm, "provider_opener", return_value=success_opener), \
         patch.object(agent_mod, "provider_opener", return_value=success_opener), \
         patch.object(agent_mod, "run_code", side_effect=AssertionError("Secret code executed")) as sandbox:
        for label, spec in (("server rejected code", agent_mod.reference_agents()[0]),
                            ("visitor rejected code", success_custom)):
            events = []
            with secret_scope(visitor_secret):
                rejected_run = gym.run_suite(spec, [SEEDED_SUITE[0]], ledger=srv.LEDGER,
                                              on_event=events.append)
            srv.RUNS[rejected_run.run_id] = rejected_run
            srv._persist(rejected_run)
            check(label + " never executes", not sandbox.called)
            for surface, value in {
                "run": srv.get_run(rejected_run.run_id),
                "detail": srv.get_run_detail(rejected_run.run_id),
                "evidence": srv.evidence(rejected_run.run_id),
                "OTel": srv.run_otel(rejected_run.run_id),
                "events": events,
                "persisted JSON": (Path(tmp) / (rejected_run.run_id + ".json")).read_text(),
            }.items():
                no_leak(label + " " + surface + " excludes keys", value)

    # Raw debug fields may echo credentials even when completion text is harmless.
    success_raw["choices"][0]["message"]["content"] = "```python\nprint('ok')\n```"
    success_response.__enter__.return_value.read.return_value = json.dumps(success_raw).encode()
    with patch.object(llm, "API_KEY", server_secret), \
         patch.object(llm, "provider_opener", return_value=success_opener), \
         secret_scope(visitor_secret):
        completion = llm.chat("stub", [])
        no_leak("successful provider debug response redacted", repr(completion))

    with tempfile.TemporaryDirectory(prefix="attest-success-redaction-") as tmp, \
         patch.object(llm, "API_KEY", server_secret), \
         patch.object(srv, "RUNS_DIR", Path(tmp)), \
         patch.dict(os.environ, {"ATTEST_SAFETY_ANNOTATE": "1"}), \
         patch.object(agent_mod, "_chat", return_value="```python\nprint('ok')\n```"), \
         patch.object(agent_mod, "run_code", return_value=SandboxResult(
             0, echoed, echoed, 1, errors=[echoed], command=[echoed])), \
         patch.object(llm, "safety_annotate", return_value={"safe": True, "risk": echoed}):
        for label, spec in (("server output", replace(agent_mod.reference_agents()[0], max_repairs=0)),
                            ("visitor output", success_custom)):
            # Exercise both active keys for all user/provider-derived metadata.
            spec = replace(spec, name="agent " + echoed, description=echoed)
            task = replace(SEEDED_SUITE[0], title=echoed, prompt="Task " + echoed,
                           notes=echoed)
            events = []
            with secret_scope(visitor_secret):
                success_run = gym.run_suite(spec, [task], ledger=srv.LEDGER,
                                             suite_source=echoed, on_event=events.append)
            srv.RUNS[success_run.run_id] = success_run
            srv._persist(success_run)
            tr = success_run.tasks[0]
            check(label + " stdout/stderr and attempt text redacted",
                  tr.outcome.result.stdout == "[REDACTED] [REDACTED]"
                  and tr.outcome.result.stderr == "[REDACTED] [REDACTED]"
                  and tr.outcome.attempts[0].stdout == "[REDACTED] [REDACTED]")
            if spec.use_server_credentials:
                check("successful annotation redacted before publication",
                      tr.safety["risk"] == "[REDACTED] [REDACTED]")
            surfaces = {
                "run": srv.get_run(success_run.run_id),
                "detail": srv.get_run_detail(success_run.run_id),
                "scorecard": srv.scorecard(success_run.run_id),
                "OTel": srv.run_otel(success_run.run_id),
                "evidence": srv.evidence(success_run.run_id),
                "events": events,
                "serialized run": success_run.to_dict(),
                "persisted JSON": (Path(tmp) / (success_run.run_id + ".json")).read_text(),
            }
            for surface, value in surfaces.items():
                no_leak(label + " " + surface + " excludes active keys", value)

    with patch.object(llm, "API_KEY", server_secret), \
         patch.object(llm, "chat_json", return_value={"safe": True, "risk": echoed}), \
         secret_scope(visitor_secret):
        annotation = llm.safety_annotate("unique-success-redaction-test-code")
        no_leak("provider annotation and cache redacted", [annotation, llm._SAFETY_CACHE])

    agent_mod._chat = fake_chat

    # --- request parsing (frozen POST /api/run body) ---------------------------
    print("=== POST /api/run request parsing ===")
    req = RunRequest(agent=AgentPayload(name="compliant"), tasks=["t01", "t05"])
    agent = srv._agent_for(req)
    tasks, source = srv._suite_for(req)
    check("reference agent by frozen name (alias)", agent.id == "compliant-qwen", agent.id)
    check("frozen tasks filter applies", [t.id for t in tasks] == ["t01", "t05"],
          str([t.id for t in tasks]))

    req = RunRequest(agent=AgentPayload(
        name="dropped-in agent",
        endpoint=EndpointSpec(base_url="https://api.vultrinference.com/v1", model="my-model", api_key="visitor-test-key"),
    ))
    agent = srv._agent_for(req)
    check("endpoint agent built from frozen payload",
          agent.model == "my-model" and agent.base_url == "https://api.vultrinference.com/v1"
          and agent.api_key == "visitor-test-key" and not agent.use_server_credentials)

    try:
        srv._agent_for(RunRequest(agent=AgentPayload(name="no-such-agent")))
        check("unknown frozen agent rejected", False)
    except HTTPException as exc:
        check("unknown frozen agent rejected", exc.status_code == 400)

    try:
        srv._suite_for(RunRequest(tasks=["nope"]))
        check("unknown task id rejected", False)
    except HTTPException as exc:
        check("unknown task id rejected", exc.status_code == 400)

    # legacy body still accepted
    agent = srv._agent_for(RunRequest(agent_id="careful"))
    check("legacy agent_id body still accepted", agent.id == "careful-glm", agent.id)
    refs = {a.id for a in __import__("attest.agent", fromlist=["reference_agents"]).reference_agents()}
    check("six seeded agents present",
          refs == {"naive-qwen", "compliant-qwen", "careful-glm", "deepseek-v4.1-flash",
                   "mimo-v2.6-flash", "redteam-probe"}, str(refs))
    # the scripted hostile probe must never need a model endpoint
    from attest.agent import reference_agents as _refs
    rt = next(a for a in _refs() if a.id == "redteam-probe")
    oc = agent_mod.solve("Total these numbers and print JSON.", rt, task_id="t99")
    check("redteam-probe runs with no model call",
          bool(oc.code) and not oc.refused and oc.error == "")
    check("redteam payload carries dangerous capability classes",
          bool(set(oc.capability_classes) & {"credential", "network", "filesystem",
                                             "privilege", "obfuscation"}),
          str(oc.capability_classes))

    # --- run two agents through the gym ----------------------------------------
    ledger = Ledger("/tmp/attest-apitest-ledger.db")
    specs = {
        "compliant": AgentSpec(id="compliant", name="compliant", model="stub-model",
                               base_url="stub", api_key="", style="compliant", max_repairs=1),
        "careful": AgentSpec(id="careful", name="careful", model="stub-model",
                             base_url="stub", api_key="", style="careful", max_repairs=1),
    }
    runs = {}
    for aid, spec in specs.items():
        run = gym.run_suite(spec, list(SEEDED_SUITE), ledger=ledger, suite_source="seeded")
        runs[aid] = run
        srv.RUNS[run.run_id] = run
        print(f"  ran {aid}: TASK {run.scores['TASK']} ADV {run.scores['ADVERSARIAL']} "
              f"CONTAIN {run.scores['CONTAINMENT']} chain={run.chain_valid}")

    run = runs["compliant"]

    # Exercise the same asynchronous POST -> GET polling path as Fast Eval.
    import time
    persist = srv._persist
    srv._persist = lambda run: None
    started = srv.start_run(RunRequest(
        agent=AgentPayload(name="compliant"), tasks=["t01", "t02", "t05", "t08"]))
    check("Fast Eval starts exactly four tasks", started["task_count"] == 4)
    deadline = time.monotonic() + 60
    polled = srv.get_run(started["run_id"])
    check("POST id is immediately pollable", polled.get("status") == "running" or bool(polled.get("tasks")))
    while polled.get("status") == "running" and time.monotonic() < deadline:
        time.sleep(0.05)
        polled = srv.get_run(started["run_id"])
    srv._persist = persist
    check("POST id resolves to completed scorecard", len(polled.get("tasks", [])) == 4)
    check("polled canonical id exists in leaderboard", any(
        r["run_id"] == polled.get("run_id") for r in srv.board()["detail_rows"]))

    from unittest.mock import patch
    with patch.object(gym, "run_suite", side_effect=RuntimeError("stubbed worker failure")):
        failed = srv.start_run(RunRequest(agent=AgentPayload(name="compliant"), tasks=["t01"]))
        deadline = time.monotonic() + 5
        status = srv.get_run(failed["run_id"])
        while status.get("status") == "running" and time.monotonic() < deadline:
            time.sleep(0.01)
            status = srv.get_run(failed["run_id"])
        check("worker failure is pollable", status.get("status") == "failed"
              and status.get("error") == "run_worker_failed"
              and "stubbed worker failure" not in json.dumps(status))

    # Auxiliary display paths must not spend server credentials for a visitor.
    with patch.object(llm, "API_KEY", "server-test-key"), \
         patch.dict(os.environ, {"ATTEST_SAFETY_ANNOTATE": "1", "ATTEST_PSAFE_LLM": "1"}), \
         patch.object(llm, "safety_annotate", side_effect=AssertionError("Server safety call")) as safety, \
         patch.object(llm, "p_safe_calibrated", side_effect=AssertionError("Server calibration call")) as calibration, \
         patch.object(llm, "chat", side_effect=AssertionError("Unexpected shared model call")):
        visitor_run = gym.run_suite(custom, [SEEDED_SUITE[0]], ledger=ledger, suite_source="stub")
        visitor_view = gym.run_view(visitor_run, [visitor_run])
        gym.otel_export(visitor_run, [visitor_run])
        gym.run_view(run, list(runs.values()))
        check("custom run and scorecard/OTel reads do not call server models",
              bool(visitor_view["tasks"]) and not safety.called and not calibration.called)

    # --- GET /api/run/{run_id}: the frozen 4-layer scorecard --------------------
    print("=== GET /api/run/{run_id} (frozen shape) ===")
    view = srv.get_run(run.run_id)
    check("run view is JSON-serializable", isinstance(json.dumps(view), str))
    check("run view has tasks", isinstance(view.get("tasks"), list) and len(view["tasks"]) == len(run.tasks))
    for t in view["tasks"]:
        missing = [k for k in FROZEN_TASK_KEYS if k not in t]
        if missing:
            check(f"task {t.get('task_id')} has frozen keys", False, f"missing {missing}")
            break
        layers = t["layers"]
        if not all(k in layers for k in ("router", "trajectory", "outcome", "containment")):
            check(f"task {t['task_id']} has 4 layers", False)
            break
        if not all(k in layers["trajectory"] for k in ("required", "order", "propagation")):
            check(f"task {t['task_id']} trajectory questions", False)
            break
        if not all(k in layers["containment"] for k in ("level", "score", "achieved_radius")):
            check(f"task {t['task_id']} containment fields", False)
            break
    else:
        check("every task carries the frozen scorecard fields", True)
    check("variant derived from slice",
          {t["variant"] for t in view["tasks"]} <= {"complete", "partial",
                                                    "contradictory", "adversarial-mutation"},
          str({t["variant"] for t in view["tasks"]}))
    check("otel path points at this run",
          all(t["otel"] == f"/api/run/{run.run_id}/otel.json" for t in view["tasks"]))
    check("per-task ledger hashes recorded",
          all(t["ledger_hash"] for t in view["tasks"]) and len({t["ledger_hash"] for t in view["tasks"]}) == len(view["tasks"]))
    check("convergence in (0,1] for passed tasks",
          all(0.0 < t["convergence_score"] <= 1.0 for t in view["tasks"] if t["passed"]))
    check("model/latency/tokens/cost/p_safe present",
          all(isinstance(t["latency_ms"], int) and t["tokens"] >= 0
              and t["cost_usd"] >= 0 and 0 < t["p_safe"] < 1 for t in view["tasks"]))

    # --- GET /api/leaderboard: the frozen agent rows ----------------------------
    print("=== GET /api/leaderboard (frozen shape) ===")
    board = srv.board()
    rows = board["rows"]
    names = {r["agent_name"] for r in rows}
    check("frozen rows present for both agents", {"compliant", "careful"} <= names, str(names))
    check("frozen row keys", all(all(k in r for k in FROZEN_BOARD_KEYS) for r in rows))
    check("rows sorted by mean_score desc",
          all(rows[i]["mean_score"] >= rows[i + 1]["mean_score"] for i in range(len(rows) - 1)))
    comp = next(r for r in rows if r["agent_name"] == "compliant")
    check("runs counted per agent", comp["runs"] >= 1 and comp["mean_latency_ms"] > 0,
          f"runs={comp['runs']} lat={comp['mean_latency_ms']}")
    check("detail_rows still available (legacy)", len(board["detail_rows"]) >= 2)

    # --- GET /api/run/{run_id}/otel.json ----------------------------------------
    print("=== GET /api/run/{run_id}/otel.json ===")
    ot = json.loads(json.dumps(srv.run_otel(run.run_id)))
    spans = ot["resourceSpans"][0]["scopeSpans"][0]["spans"]
    check("OTLP/JSON structure", "resourceSpans" in ot and "scopeSpans" in ot["resourceSpans"][0])
    check("one root span plus one per task", len(spans) == 1 + len(run.tasks),
          f"{len(spans)} spans")
    root = spans[0]
    check("root span is attest.run", root["name"] == "attest.run")
    task_spans = [s for s in spans if s["name"].startswith("attest.task")]
    check("task spans parented to the run span",
          all(s.get("parentSpanId") == root["spanId"] for s in task_spans))
    check("span ids are 16-hex, trace id 32-hex",
          all(len(s["spanId"]) == 16 for s in spans) and len(root["traceId"]) == 32)
    check("layer attributes on task spans",
          any(any(a["key"] == "layer.containment.level" for a in s["attributes"])
              for s in task_spans))
    check("status reflects verdicts",
          any(s["status"]["code"] == 2 for s in task_spans) or all(
              s["status"]["code"] == 1 for s in task_spans))
    check("deterministic export (same input, same output)",
          srv.run_otel(run.run_id) == srv.run_otel(run.run_id))

    # --- POST /api/regression/promote -------------------------------------------
    print("=== POST /api/regression/promote ===")
    contained = [t for t in run.tasks if t.containment.get("outcome") == "contained"]
    check("compliant run has contained traces to promote", bool(contained))
    if contained:
        tr = contained[0]
        resp = srv.promote_regression(PromoteRequest(run_id=run.run_id, task_id=tr.task.id))
        case_id = resp["regression_case_id"]
        check("promote returns a regression_case_id", case_id.startswith("rc-"), case_id)
        again = srv.promote_regression(PromoteRequest(run_id=run.run_id, task_id=tr.task.id))
        check("promotion is idempotent", again["regression_case_id"] == case_id and not again["created"])
        cases = srv.regression_cases()["cases"]
        check("case persisted in the ledger store",
              any(c["case_id"] == case_id for c in cases))
        check("chain still verifies after promotion", ledger.verify(run.run_id))
    clean = [t for t in run.tasks if t.verdict.passed and t.containment.get("outcome") == "safe"]
    if clean:
        try:
            srv.promote_regression(PromoteRequest(run_id=run.run_id, task_id=clean[0].task.id))
            check("clean pass cannot be promoted", False)
        except HTTPException as exc:
            check("clean pass cannot be promoted", exc.status_code == 400)

    print("=== fail-closed persisted-run startup quarantine ===")
    import copy
    import subprocess
    old_server = "UNKNOWN_ROTATED_SERVER_CREDENTIAL"
    old_visitor = "UNKNOWN_OLD_VISITOR_CREDENTIAL"
    legacy_secret = old_server + " " + old_visitor

    with tempfile.TemporaryDirectory(prefix="attest-legacy-startup-") as tmp:
        root = Path(tmp)
        safe_data = run.to_dict()
        check("new safe runs carry publication schema", safe_data["publication_schema"] == 1)
        legacy_data = copy.deepcopy(safe_data)
        legacy_data.pop("publication_schema")
        legacy_data["run_id"] = "run-legacy-secret"
        legacy_data["agent_name"] = legacy_secret
        legacy_data["tasks"][0]["outcome"].update(
            code="print(" + repr(legacy_secret) + ")",
            stdout=legacy_secret, stderr=legacy_secret)
        legacy_data["tasks"][0]["safety"] = {"risk": legacy_secret}
        original = json.dumps(legacy_data, indent=2).encode()
        legacy_path = root / "run-legacy-secret.json"
        legacy_path.write_bytes(original)
        (root / (safe_data["run_id"] + ".json")).write_text(json.dumps(safe_data))
        # A malformed marked run must not partially load either.
        malformed = copy.deepcopy(safe_data)
        malformed["run_id"] = "run-broken"
        malformed["tasks"].append({"outcome": {"code": legacy_secret}})
        (root / "run-broken.json").write_text(json.dumps(malformed))
        (root / "invalid.json").write_bytes(b"invalid legacy JSON")

        historical = Ledger(str(root / "history.db"))
        historical.append("run-legacy-secret", "old_event", {"text": legacy_secret})
        historical.save_regression_case({
            "run_id": "run-legacy-secret", "task_id": "old", "code": legacy_secret})
        before = historical.export("run-legacy-secret")
        before_cases = historical.regression_cases()

        # Real fresh import exercises exactly the production startup loader.
        env = dict(os.environ, ATTEST_RUNS_DIR=str(root),
                   ATTEST_DB=str(root / "history.db"))
        env.pop("VULTR_API_KEY", None)
        env.pop("VULTR_INFERENCE_API_KEY", None)
        child = subprocess.run(
            [sys.executable, "-c",
             "import json; from attest import server; "
             "print(json.dumps(sorted(server.RUNS)))"],
            env=env, capture_output=True, text=True, timeout=30)
        check("fresh startup loads only safe current-format run",
              child.returncode == 0 and child.stdout.strip() == json.dumps([run.run_id]))
        check("startup logs contain no legacy credentials",
              old_server not in child.stdout + child.stderr
              and old_visitor not in child.stdout + child.stderr)
        preserved = list((root / "quarantine").glob("*.json"))
        check("legacy original is quarantined byte-for-byte",
              not legacy_path.exists() and any(p.read_bytes() == original for p in preserved))
        check("all invalid/legacy files quarantined",
              len(preserved) == 3 and not (root / "run-broken.json").exists())
        check("quarantine permissions are private",
              (root / "quarantine").stat().st_mode & 0o777 == 0o700
              and all(p.stat().st_mode & 0o777 == 0o600 for p in preserved))
        check("legacy rehydration rejects without guessing old credentials",
              gym.run_from_dict(legacy_data) is None and gym.run_from_dict(malformed) is None)
        loaded = srv.load_persisted_runs(root)
        check("safe run reload preserves recorded chain metadata",
              loaded[run.run_id].ledger_head == safe_data["ledger_head"]
              and loaded[run.run_id].chain_valid == safe_data["chain_valid"]
              and loaded[run.run_id].publication_schema == 1)
        check("quarantine restart is idempotent",
              list(loaded) == [run.run_id]
              and len(list((root / "quarantine").glob("*.json"))) == 3)

        with patch.object(srv, "RUNS", loaded), patch.object(srv, "LEDGER", historical):
            for path in (
                "/api/run/run-legacy-secret",
                "/api/run/run-legacy-secret/detail",
                "/api/run/run-legacy-secret/otel.json",
                "/api/run/run-legacy-secret/events",
                "/api/scorecard/run-legacy-secret",
                "/api/evidence/run-legacy-secret",
            ):
                status, payload = asyncio.run(api_request(path, method="GET"))
                check("quarantined public read returns 404 " + path, status == 404)
                check("quarantined public read contains no old keys " + path,
                      old_server not in payload and old_visitor not in payload)
            for path in ("/api/leaderboard", "/api/regression/cases", "/api/health"):
                status, payload = asyncio.run(api_request(path, method="GET"))
                check("public aggregate excludes old keys " + path,
                      status == 200 and old_server not in payload and old_visitor not in payload)
            status, payload = asyncio.run(api_request(
                "/api/run/" + run.run_id, method="GET"))
            check("safe reloaded run remains publicly readable",
                  status == 200 and json.loads(payload)["run_id"] == run.run_id)
        check("quarantine does not rewrite hash-chained history or cases",
              historical.export("run-legacy-secret") == before
              and historical.regression_cases() == before_cases)

    with tempfile.TemporaryDirectory(prefix="attest-quarantine-failure-") as tmp:
        root = Path(tmp)
        blocked = root / "run-legacy-secret.json"
        blocked.write_bytes(original)
        with patch.object(Path, "rename", side_effect=OSError("synthetic move failure")):
            try:
                srv.load_persisted_runs(root)
                check("quarantine preservation failure aborts startup", False)
            except OSError:
                check("quarantine preservation failure aborts startup", True)
        check("failed quarantine leaves original unchanged", blocked.read_bytes() == original)

    # --- 404s -------------------------------------------------------------------
    for fn, name in ((srv.get_run, "get_run"), (srv.run_otel, "run_otel"),
                     (srv.get_run_detail, "get_run_detail")):
        try:
            fn("run-does-not-exist")
            check(f"{name} 404s on unknown run", False)
        except HTTPException as exc:
            check(f"{name} 404s on unknown run", exc.status_code == 404)

    print("\nRESULT:", "ALL GREEN" if not failures else f"FAILED: {failures}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
