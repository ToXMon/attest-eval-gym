# Bring an existing agent: deadline plan

Date: 2026-11-08, 04:02 UTC inspection · POC: ticket 7 / BYO agent proposal

TL;DR: Keep the canonical Vultr endpoint allowlist. Label today's integration as **model-to-Python evaluation**, not full-agent onboarding. If time permits, add an invite-only, judge-run CLI that invokes an existing local agent wrapper and returns Python source for ATTEST to execute and grade. Target under 30 seconds to connect an already-installed wrapper and receive the first task; do not promise a completed evaluation in 30 seconds. No implementation or deployment is included in this plan.

## What works today

A base URL plus key is appropriate for an OpenAI-compatible **model**, not a general agent with tools, state, credentials, and its own orchestration. `server._agent_for` builds an `AgentSpec`; `agent.solve` asks for fenced Python, executes it through `sandbox.run_code`, and optionally repairs it. There is no remote-agent invocation protocol or arbitrary tool adapter.

Public custom evals accept only `https://api.vultrinference.com/v1` over HTTPS with a visitor key. Do not loosen this restriction. The proposed CLI sends no provider URL or model key to ATTEST; its outbound destination is the ATTEST service, not an additional inference provider.

Fast Eval selects `t01`, `t02`, `t05`, and `t08`: two useful coding tasks, an injected exfiltration instruction, and an `/etc/shadow` probe. The attack corpus is separate. The frozen task contract already carries `request`, `context_records`, `expected_oracle`, `variant`, and `family`; the current task objects also expose legacy prompt/oracle fields.

At inspection, about 19 hours remain before Nov 8, 23:00 UTC. Concurrent admission/deployment hardening changes are present. Coordinate with their owner and do not replace them.

## Options and recommendation

| Option | Judge effort | What is actually evaluated | Deadline/security cost | Decision |
|---|---|---|---|---|
| Keep endpoint-only, improve labels | Very low for someone with a Vultr model/key; not a connection to an existing agent | ATTEST's coding loop using that model | Small copy change; existing credential-custody limits remain | Ship as the guaranteed fallback |
| Judge-run CLI plus local wrapper | One command if a compatible wrapper already exists; otherwise a small integration | Existing agent's ability to return a Python artifact, then ATTEST's execution of that artifact | Moderate: authenticated session queue, wrapper, solver seam, tests; no arbitrary server-side HTTP destinations | Recommended bounded beta, only if acceptance gates pass |
| Host a full-agent worker/container | Agent packaging, dependencies, secrets, tools, state, network configuration | Potentially a complete agent, with much wider execution scope | Large new execution/security boundary; resource and provider-routing complexity | Defer beyond hackathon |

Do not call a generic CLI universal support. Provide one tested stdin/stdout wrapper example and an honest unsupported-agent message. Agents that cannot return a standalone Python artifact need adaptation or a later benchmark mode. No framework-specific integrations or live SDK research are assumed here.

## Judge journey

1. Choose **Test my existing agent (local beta)**. Read: “Your agent runs on your machine. Only the returned Python runs inside ATTEST's sandbox.” The default is a benign `t01` smoke test.
2. Explicitly opt into the four-task suite. Warn that tasks contain hostile instructions. Use an agent configured for code generation only, with destructive/network tools disabled in a disposable local environment. The CLI cannot enforce this inside an arbitrary agent.
3. The browser creates a short-lived session and displays a copyable command. Illustrative, not available today:
   `python3 scripts/byo_agent.py --server https://<ATTEST-host> -- python3 my_agent_wrapper.py`
   The CLI prompts privately for the pairing token; do not put tokens in process arguments, URL query strings, or shell history. Use a pinned local release/checkout, not curl-to-shell.
4. CLI pairs outbound over HTTPS, validates the manifest, and shows “Connected; task 1/4 dispatched.” With Python and the wrapper already installed, this is the under-30-second onboarding target. Installation, wrapper development, agent latency, and sandbox time are excluded.
5. Agent keys stay in the judge's environment. The CLI invokes the local wrapper with a JSON task on stdin and expects a JSON Python/refusal response on stdout. It does not execute returned Python locally. It uploads only the selected artifact/refusal, not logs, repository contents, conversation history, tool traces, or local stdout/stderr from other processes.
6. Browser shows queued/generating/executing/complete states and a session-scoped scorecard. Publishing is a separate explicit action. Report “artifact evaluated,” never “your whole agent contained.”

If the wrapper is not ready, offer built-in Fast Eval or **Use a Vultr model**. Do not imply pasting an arbitrary URL will connect the agent.

## Proposed minimal protocol

New additive `/api/byo/*` routes require an ADR before implementation; leave frozen `/api/run`, task schemas, and provider allowlist unchanged. One browser-issued session, one bound CLI, fixed server-selected suite, at most four artifacts. No callback URL, repository upload, package install, or worker image.

- `POST /api/byo/sessions`: operator-issued demo invitation, suite choice, display name. Return opaque session ID, one-time pairing secret, and a distinct read capability. Expire unused sessions after 5 minutes. Never persist secrets or include them in evidence. Public anonymous creation is not required for this beta.
- `POST /api/byo/sessions/{id}/pair`: pairing secret in Authorization; consume once and return a short-lived worker bearer. Worker and reader permissions are distinct. Rate-limit attempts; store token digests, not raw tokens.
- `GET /api/byo/sessions/{id}/next`: worker authorization; bounded outbound polling, around 1 second with backoff. `204` means waiting; a task response contains `{protocol_version:1, task_id, attempt_id, suite_version, request, context_records, variant, family, deadline}`. Server binds the expected Oracle internally; never accept grading rules from the client. Omit the expected answer from worker input, while documenting that seeded fixtures are public, not cheat-resistant.
- Wrapper stdin uses that task object. Wrapper stdout is exactly `{task_id, attempt_id, status:"code", code:"..."}` or `{task_id, attempt_id, status:"refused"}`. Unknown/missing fields or non-JSON output are a local protocol error. No model keys, endpoint fields, or telemetry required.
- `POST /api/byo/sessions/{id}/results`: worker bearer plus the same envelope. Accept only the outstanding task/attempt. One artifact per task, no repair loop for v1. Limit code to 16 KiB UTF-8, body to the existing admission limit, and reject oversized input before parsing. Duplicate identical submissions return the previous receipt; different content for the same attempt returns `409`. Never execute twice on retries or reconnection.
- A task deadline of 60 seconds and total session lifetime of 5 minutes are proposed caps, not an SLA. Missing/refused/invalid artifacts are explicit statuses, never invented successful executions. Late results are rejected. Worker crash/cancel releases pending state; session expiry releases capacity.
- `GET /api/byo/sessions/{id}`: reader authorization; progress plus completed scorecard or a capability-gated reference. Existing evidence/OTel/detail endpoints must not become a privacy bypass. Keep drafts outside public `RUNS`; publish a sanitized result only after consent. Return fixed errors without echoed bodies/tokens. Revoke worker tokens on completion and expire read access explicitly.

Separate artifact waiting from sandbox admission. Do not hold a container/execution lease for the entire human pairing interval. Session count and pending queues need their own small caps. Apply `AdmissionMiddleware` body limits to all new write routes; current path matching does not protect them automatically. Reuse execution admission when an artifact is ready. No server inference or model annotation calls for this mode.

## Reuse and minimal implementation seam

The work is mostly transport and state, not new graders:

| File | Proposed change/reuse |
|---|---|
| `attest/byo.py` (new) | Session state machine, token digests, bounded queue, replay receipts, expiry; no network callbacks |
| `scripts/byo_agent.py` (new) | Standard-library HTTPS client and subprocess wrapper; explicit argv after `--`, `shell=False`, timeout, output cap, no raw log uploads |
| `examples/byo_wrapper.py` (new) | Tested JSON stdin/stdout example; judge replaces one local agent call, no credential upload |
| `attest/server.py` | Add protected routes, finalize with existing safe persistence; separate draft/read capability checks |
| `attest/gym.py` | Add an explicit optional task solver callable; default remains current `solve`. BYO solver waits for artifact and returns `AgentOutcome`; no process-global monkeypatch |
| `attest/agent.py` | Extract a small shared code-artifact executor using existing source analysis, credential rejection, `run_code`, and Attempt construction; endpoint solve and BYO use it |
| `attest/admission.py` | Protect new writes, bound pending sessions and ready execution; preserve recent hardening |
| `attest/web/index.html` | Pairing instructions, warning/consent, progress and scoped result labels; keep existing model mode |
| `attest/errors.py`, `attest/sandbox.py`, `attest/oracles.py`, `attest/ledger.py` | Reuse redaction, isolation, deterministic grading, evidence; do not fork implementations |
| `scripts/byotest.py` (new), `scripts/apitest.py` | Offline wrapper/protocol, replay, disclosure and compatibility tests |
| `docs/adr/` | Next available ADR number: additive protocol, external-agent boundary, read capabilities and routing scope |

`gym.run_suite` already creates/redacts records, grades, emits task events, and writes ledger evidence. Preserve that path and its safe publication marker/quarantine behavior. One-shot artifact submission avoids reproducing the existing model repair conversation. `scripts/piptest.py:fake_chat` supplies deterministic fixture artifacts for offline tests; use a subprocess fixture instead of real agent calls.

## Threat model and truthful claims

- **External tool actions:** ATTEST cannot stop an external agent reading local files, browsing, exfiltrating, or spending money while generating an artifact. The outbound-only channel protects ATTEST from server-side callback SSRF; it does not contain the judge's agent. Reject the “my agent is sandboxed” claim. Never auto-run hostile probes without consent.
- **Secrets and custody:** pairing/read tokens are credentials but not provider keys. Do not ship arbitrary API-key fields. Locally scan artifacts for exact values of user-designated credential environment variables and refuse before upload; never transmit the values. Apply server-side active-key rejection/redaction again. Unknown, encoded, or fragmented secrets remain a risk; use synthetic data. Raw wrapper logs stay local and are not printed by default.
- **Untrusted artifacts:** server runs Python only through the existing sandbox, never in the control plane. No pickle/eval/import hooks, archive expansion, mounts, dependencies, or arbitrary executable uploads. No returned client stdout or claimed verdict is accepted as execution evidence.
- **Score meaning:** Oracles grade server-observed returned-code execution. Router / Tool Selection Layer and Trajectory & Convergence Layer remain artifact-execution proxies; they do not verify external tool selection, external step order, propagation, or complete-agent convergence. Scope or mark unavailable fields instead of presenting synthetic counts as full-agent traces. Containment Layer and Achieved Radius refer only to the returned artifact and existing limited classifiers. P(safe) remains a classifier-derived display estimate.
- **Metrics/provenance:** identify `external-artifact` origin. Measure server sandbox latency separately from wall-clock generation wait. External tokens/model/cost are unknown unless explicitly self-reported; never display zero or server price-table estimates as real external usage. Do not rank one-shot external artifacts as directly equivalent to built-in repair-enabled agents without a mode badge/separate board.
- **Vultr gate:** the external wrapper's own inference routing cannot be verified by this protocol. Do not claim it satisfies the “all agent LLM calls through Vultr” gate. Keep the official judged baseline on verified built-in Vultr routes; label external-artifact beta separately, pending organizer acceptance. No server-side endpoint-policy exception.
- **Public-demo abuse:** invites, TTLs, admission limits and capability checks are mandatory, not a deferred polish item. The current API's `public:false` flag alone does not provide privacy. If protecting draft/evidence reads cannot be finished, do not ship this hosted beta; offer a local-only adapter proof of concept instead.

## Delivery gates and fallback

Proposed engineering budget: 1 hour for protocol/ADR and tested local wrapper; 2–3 hours for session/auth/admission; 2–3 hours for solver seam, scoped metrics and UI; 2 hours for tests and review. This is an estimate, not a commitment. Reserve the rest of the deadline window for existing hardening and demo rehearsal. Stop if the protected read path or shared executor requires a broad rewrite.

Acceptance before enabling the beta:

1. Already-installed fake agent pairs and receives a task in under 30 seconds on a measured local rehearsal; capture actual timing. Four tasks complete through real sandbox/Oracle/ledger execution with no model calls in the test.
2. Command wrapper sees canonical request/context/variant/family and returns code or refusal. Test wrong IDs, malformed JSON, timeout, output flooding, unavailable command, and cancel. No local execution of returned code.
3. No SSRF input, server provider call, key upload, or transport-policy weakening. Spy on outbound networking and inference entry points in tests.
4. Token guessing/reuse/wrong role, expired sessions, unauthenticated draft/detail/evidence/OTel reads, oversized bodies and quota exhaustion fail closed. Retried submissions execute exactly once.
5. Synthetic server and wrapper credentials in generated source, output, metadata, exceptions, events, annotation and saved JSON are rejected/redacted. Retain all existing success/error redaction and legacy quarantine tests.
6. External latency/cost/tokens/trajectory labels reflect provenance; no unsupported full-agent sandbox claim. Built-in Fast Eval remains unchanged. Run selftest, piptest, apitest, hardening tests, plus byotest with Vultr credentials unset.

Immediate recommendation: improve existing labels regardless. Build the outbound-only artifact adapter only behind an invitation and the gates above. It is the lowest-friction truthful route for an existing agent that can emit code; a base URL/key box is not a substitute for that integration.
