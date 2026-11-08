# Test your agent locally: one-day MVP implementation plan

Date: 2026-11-08 · POC: ATTEST BYO adapter, implementation proposal only

TL;DR: Build an invitation-gated CLI that runs a user-supplied local command, collects four bounded Python artifacts/refusals, then submits one batch. ATTEST executes the returned source in its existing sandbox, grades it, persists a safe Run, and exposes an explicitly labeled external-artifact row on the live leaderboard. No provider keys, callback URLs, hosted agent workers, or per-task server queue. Keep the existing Vultr provider allowlist unchanged.

## 1. Decision and evidence

This narrows [the earlier proposal](byo-agent-plan.md): replace browser/worker pairing and `/next` polling with **manifest → local generation → single submission → run-status polling**. A one-shot benchmark does not need a server waiting for each external tool call. Optional repair, private hosted drafts, trace ingestion, generic SDK integrations, and full-agent workers are excluded.

The assessment supplied in the conversation establishes the critical distinction: today's code evaluates a model-generated Python artifact, not a judge's complete agent/tools/state. No separate adapter-specific evaluator report was found in project docs. `eval_gym_product_assessment.md` is earlier product research with stale arbitrary-endpoint and full-agent claims; those claims are not implementation authority. This plan uses the current code and the review constraints rather than assuming undocumented evaluator approval.

Inspected interfaces:

- `server.start_run`: threaded evaluation, admission lease transfer, pending status and request-to-canonical-Run alias. `board` reads `RUNS` through `gym.agent_leaderboard`/`gym.leaderboard`. A submitted file alone does not join the leaderboard.
- `gym.run_suite`: run-scoped redaction and safe publication schema; `_run_suite` currently hardcodes `solve`, estimated tokens/cost, annotation eligibility, ledger writes, and events. A solver hook alone is insufficient: external metering and scoring scope need a mode branch.
- `agent.solve`: model conversation, source extraction/rejection, source analysis, sandbox execution and repairs. Factor the single-artifact execution portion; do not monkeypatch the process-global solver.
- `sandbox.run_code(source, timeout=..., ...)`: source via stdin, isolated container, no inherited host environment, bounded execution. Respect `REQUIRE_GVISOR`; never add a fallback to control-plane execution.
- `task_layer_view`: router/trajectory fields are outcome proxies; external traces are not captured. `agent_leaderboard` groups by display name and estimates cost/convergence. Neither behavior can be reused blindly for external agents.
- `AdmissionMiddleware`: exact-path protection for current run/suite/selftest routes, 32 KiB body cap, 2 concurrent jobs, 6/minute per client and 100/day process-local defaults. New routes need explicit coverage; no reset-proof quotas are currently provided.

## 2. User journey and CLI contract

UI label: **Test your agent locally — returned-code evaluation**. Subtitle: “Your agent runs on your machine. ATTEST sandboxes only the Python you submit, not your agent's own tools or actions.”

Illustrative command, not implemented:

```text
python3 scripts/byo_agent.py --server https://<ATTEST-host> --name "My agent" -- python3 my_wrapper.py
```

1. Judge obtains a short-lived, single-run invitation from the operator and enters it through a hidden CLI prompt. No tokens in argv, query strings, shell history, or model inputs. A pinned checkout/release is required; no curl-to-shell.
2. CLI asks for explicit publication consent: submitted source, observed outputs, scores, and evidence will be public after successful grading. Private hosted runs are **not** promised in this MVP. Cancel means no generation/upload. Model keys stay local.
3. CLI requests a fixed task manifest. Default is the benign `t01` smoke test; `--suite fast4 --allow-hostile-tasks` explicitly selects `t01,t02,t05,t08`. Warn before invoking the local agent: t05/t08 contain hostile instructions. Require a disposable, tool-restricted agent environment; the adapter cannot enforce this inside an arbitrary command.
4. For each task, spawn the supplied argv with `shell=False`. Stdin is one JSON object with `{protocol_version, task_id, request, context_records, variant, family, output_contract}`. Stdout must be exactly `{status:"code", code:"..."}` or `{status:"refused"}`. The wrapper invokes the judge's existing agent; the adapter binds task IDs itself. No raw fenced-text heuristic, stdout-as-verdict, returned files, arbitrary executable, or tool logs are uploaded.
5. Each invocation is isolated at the process level, not claimed to be sandboxed: fresh process, explicit timeout (60s), bounded output (32 KiB captured across stdout/stderr), process-group termination on timeout/overflow/cancel where supported. Local stderr is discarded from automatic reporting; print a fixed diagnostic, not raw logs. Windows process-tree termination requires a tested implementation or an explicit unsupported-platform notice for v1.
6. Validate/refuse credential-bearing artifacts locally using exact values of explicitly named secret environment variables (`--secret-env NAME`, repeatable), never their values on argv. Keep ATTEST invitation/session tokens out of the child environment; inherit the agent's own environment only with the warning above. Never execute the returned Python locally. Show a bounded submission summary and confirm publication; only then upload.
7. Poll status every 1s with backoff and print the canonical scorecard URL. The existing page's next leaderboard refresh shows a new **External artifact / one-shot** row. Optional UI auto-refresh while the connection panel is open is enough; no websocket work.

Target: under 30 seconds from command launch to first task dispatch **with Python, wrapper and invitation already available**. Agent runtime, installation, wrapper development, sandbox queueing and total completion time are excluded. An arbitrary existing agent without a wrapper is not a zero-setup integration.

## 3. Minimal additive API

All endpoints below are proposed. Register an ADR before implementation; do not overload `agent.endpoint` or relax the frozen `/api/run` provider policy. Reject unknown request fields, especially `endpoint`, `api_key`, `url`, `callback`, `oracle` and client-supplied scores.

### Create manifest: `POST /api/byo/sessions`

Authorization: operator-created single-run invitation, 256-bit random bearer, preinstalled digest with expiry. Body: `{protocol_version:1, name, suite:"smoke"|"fast4", allow_hostile_tasks, publish:true}`. Name ≤80 characters, sanitized/HTML-escaped as data. Validate consent/suite and admit before consuming the invitation atomically.

Response `201`: `{session_id, session_token, expires_at, suite_version, tasks:[{task_id, request, context_records, variant, family}], limits:{code_bytes:4096, body_bytes:32768, artifacts:4}}`. Smoke has one task. Keep server-selected expected Oracles internally; do not accept modified grading criteria from the client. Public seeded tasks are not a cheating-resistant benchmark. An ambiguous create response may consume an invitation; issue a replacement rather than adding pairing/recovery machinery on day one.

### Submit: `POST /api/byo/sessions/{id}/submit`

Authorization: session bearer. Body: `{protocol_version:1, suite_version, artifacts:[{task_id,status:"code",code:"..."}|{task_id,status:"refused"}]}`. Exactly one entry for every manifest task, no duplicates/extras, fixed server order. Strict UTF-8 source ≤4 KiB per task and actual encoded HTTP body ≤32 KiB; JSON escaping can hit the body limit before per-code limits. CLI checks both and refuses oversize instead of truncating executable code. No local stdout/stderr, model usage, provider key or agent endpoint fields.

Under a session lock, authenticate, check TTL, bind suite, validate batch, hash canonical content, acquire execution admission, and transition to `accepted`. Return `202 {session_id,status:"accepted"}`. Do not accept into an unbounded execution queue. A busy response is `429` plus `Retry-After`; a rejected/busy batch has not consumed the execution slot. Never log tokens or request bodies.

Replay rule: same session and same batch digest returns the previous receipt/status, without another execution or budget charge; changed content returns `409`. Concurrent duplicate requests must observe the same acceptance. Invalid auth `401`, unsupported/malformed data `400/422`, too large `413`, expired session `410`, fixed-code failure `500`. No raw exceptions or provider text.

### Poll: `GET /api/byo/sessions/{id}`

Session bearer required, response `Cache-Control: no-store`. States: `collecting → accepted → running → complete | failed`; collecting expires after 10 minutes. Accepted work has a bounded execution deadline independent of generation TTL. Complete returns `{status:"complete",run_id,scorecard_url}` only after safe persistence and insertion into `RUNS`. Failed returns a stable code, never partial source/output. Completed/failed receipt TTL: 1 hour, then discard private session state. At most 16 pending sessions; bounded receipt cache. No SSE or per-task polling endpoint.

One session bearer is sufficient because the CLI is the sole session reader/writer. Browser sees only the final public scorecard, so separate browser read/worker capabilities and private draft authorization are unnecessary. Session IDs remain opaque but are not authentication. Tokens are stored as digests and compared in constant time; raw invitation/session tokens never enter task inputs, ledger evidence or persisted Runs. Include the presented bearer in the transient redaction scope; reject its appearance in submitted code. Per-run process memory only, no token persistence on day one.

## 4. Replay, admission and restart semantics

- Invitations require operator authorization; do not add an anonymous source-execution endpoint. Apply request-rate/body/slow-upload checks to manifest/submit, cheap auth/rate checks to status reads, and preserve existing proxy trust rules.
- Separate pending-session limits from sandbox execution leases. Local generation holds no container/concurrency lease. Accepted submission reserves one existing execution job for the whole batch, at most four executions, one per task, 25s sandbox cap each, no repairs, no model annotations.
- Server inference cost for this mode is zero by construction. Container/CPU cost is not zero: enforce the existing global concurrent/job quotas plus one submission per invitation/session and a bounded end-to-end execution watchdog. External-agent costs are paid and controlled by the judge; ATTEST cannot budget them.
- MVP runs one Uvicorn worker. Session locks and quotas are process-local. A restart invalidates session tokens/receipts; the CLI must not recreate and automatically resubmit an ambiguous accepted job. It reports “status unavailable; inspect the board or contact the operator.” Newly graded public Runs reload through current safe persistence; sessions do not.
- This gives at-most-once dispatch **within the process lifetime**, not durable exactly-once execution across crashes. Cancellation stops local generation; already accepted server execution may finish and publish under prior consent. Document this. Durable replay recovery and multiworker coordination are deferred, not claimed solved.

## 5. Integrate with the live leaderboard, truthfully

The server creates its own `AgentSpec` with an opaque external ID and `use_server_credentials=False`; never accept that flag from a client. Add a `solver(task, agent, timeout) -> AgentOutcome` hook to the gym (default current behavior). The external solver looks up the accepted artifact by task ID, invokes the shared source executor or creates a genuine refusal outcome. It never accepts client stdout, claimed execution, Oracle verdicts or containment scores.

Run the same server grading, source analysis, sandbox, ledger, redaction, safe-publication schema and quarantine path. Reuse persistence/finalization from `start_run` rather than copy-pasting it. Require `_persist` to confirm success for the new route: currently it can swallow write failures; do not report `complete` and publish before durable serialization succeeds. Do not change original ledger hashes or advertise a new chain after rewriting content. Rejected source must not be recorded raw.

Minimal metadata: `evaluation_mode:"external-artifact-v1"`, `suite_profile:"smoke"|"fast4"`, `execution_policy:"one-shot"`, `metrics_scope:"server-artifact"`, and opaque `submission_id`. Persist/reload it and carry it through run/detail/OTel/leaderboard. Additive response metadata plus external-mode nullable metrics require an ADR and tests; keep built-in payload behavior intact.

Concrete board integration:

- Completed consented runs enter the existing `RUNS`/leaderboard data path, not a disconnected upload-results screen.
- Group external rows by opaque submission ID, mode and suite, not caller-chosen `agent_name`. A visitor cannot merge with or impersonate a built-in agent by typing its name. One row per external submission is enough; no cross-version aggregation in MVP.
- Render an **External artifacts** section/tab within the same live leaderboard, with smoke and fast4 visibly distinct. Existing built-in ranking remains unchanged. Only rank within identical suite/mode/policy. Links open the normal run scorecard and evidence routes after publication.
- Outcome and Containment scores are server-observed artifact results, not the safety of the entire external agent. Containment Layer: refused/safe/contained/escaped ladder remains unchanged and qualified as applying to submitted artifacts only. Transport failures or secret rejection must not become rewarded agent refusals.
- Router / Tool Selection Layer, external trajectory questions and external Convergence Score are **not observed**: return null/unavailable for external mode rather than synthesizing full-agent behavior from success or single-attempt counts. Retain four card headings with an explanation. P(safe) remains classifier-derived artifact display data, not model judgment.
- `latency_ms` for external mode measures server artifact execution/processing; label it **server execution latency**. Tokens, external inference cost and model are unknown, not zero/stub model usage or the current fallback char estimate. Suppress `_estimate_tokens`/price-table computation for this mode, return null metrics consistently in task/run/board, omit unavailable numeric OTel attributes, and render em dashes. The UI must not sum nulls into a false $0 total. No external wall-clock/token cost claims in v1.
- Every external scorecard starts with: “Your agent generated this code locally. ATTEST executed and graded only the submitted artifact. External tools, network actions, state and inference routing were not observed or contained.” Model-backed baseline rows must remain clearly distinct.

## 6. Files and order of work

| File | Minimal proposed work |
|---|---|
| `attest/byo.py` (new) | Strict models, invitation/session auth, bounded state, canonical batch digest, atomic replay/expiry and external solver mapping |
| `scripts/byo_agent.py` (new) | Standard-library HTTPS JSON client; hidden token input; bounded subprocess stdin/stdout contract, validation and safe polling |
| `examples/byo_wrapper.py` (new) | Small documented integration template and deterministic fixture; no framework dependency or model key handling on server |
| `attest/agent.py` | Extract shared `execute_source` from current solve path; credential rejection precedes execution; reuse analysis/Attempt/sandbox |
| `attest/gym.py` | Injectable solver and explicit external mode; disable paid helpers/estimated metering, scope fields, persist/reload mode metadata |
| `attest/server.py` | Three additive routes, shared safe finalization, board grouping/provenance; no arbitrary HTTP fetch |
| `attest/admission.py` | New-route body/rate/session controls, execution lease transfer; preserve concurrent hardening |
| `attest/web/index.html` | Command/consent instructions, external board grouping and metric labels, existing run detail reuse |
| `scripts/byotest.py` (new), `scripts/apitest.py`, `scripts/hardeningtest.py` | Offline wrapper, API, concurrency/replay, provenance and compatibility gates |
| `docs/adr/` and `README.md` | Additive API/null metric contract, public submission consent, trust boundary and restart limits; choose next ADR number at implementation |

Leave `attest/tasks.py`, `attest/provider_policy.py`, and sandbox isolation flags unchanged. Reuse `errors.py` redaction/secret scopes, `oracles.grade`, `gym.assess_containment`, `ledger.append/verify`, and existing safe-run loading. Never globally monkeypatch `solve` in production; deterministic subprocess fixtures may reuse `scripts/piptest.py` task-code examples.

## 7. Acceptance tests before enabling the route

All fixtures offline, Vultr compute/inference credentials unset. Spy on shared/custom inference transports and server HTTP clients: no calls permitted. Sandbox execution itself is real where indicated.

1. **Happy path:** local fixture command receives correct canonical task context; returns code/refusal; real sandbox/Oracles grade a four-task batch; persisted Run appears in live `/api/leaderboard` external group; UI link, detail/evidence/OTel and restart reload work. Smoke is not ranked as fast4.
2. **Auth/protocol:** missing/wrong/expired invitations and bearers, guessed IDs, wrong suite, missing/duplicate/extra task IDs, unknown fields, source/body/output caps, slow upload and poll flood fail closed. Callback/endpoint/key/oracle fields rejected. No provider allowlist changes.
3. **Replay/budget:** simultaneous identical submissions execute once; conflicting replay `409`; identical retry returns receipt; admission exhaustion `429` consumes no execution; expiry releases pending capacity; worker startup/finalization failures release leases. Restart invalidates session and never auto-dispatches cached work. Assert process-local limits, not durable guarantees.
4. **Local safety:** `shell=False`; explicit command only; timeout/overflow kills process tree on supported OS; returned code never executed locally; hostile suite requires opt-in. Child never receives invitation/session bearer. Invalid wrapper output fails without uploading logs or marking agent refusal.
5. **Secrets:** synthetic server, session and locally designated agent keys in source are rejected before sandbox; stdout/stderr/annotation/metadata/errors/events/persisted JSON redact known active keys. No raw provider debug/log upload. Unknown/encoded secrets are documented limitations. Keep all existing HTTP-error, successful-output, and legacy-quarantine tests.
6. **Truthful metrics:** cannot collide with built-in display name; external fields survive reload; no fake zero cost/tokens, fabricated convergence or model-call spans; no paid helpers; no client-submitted execution evidence. Secret/protocol rejection is not scored as a safe agent refusal.
7. **Compatibility:** selftest, piptest, apitest, hardeningtest, byotest plus `git diff --check`; local browser checks show a real external row and clear scope at desktop/mobile. Measure onboarding-to-first-task under 30s with a prepared wrapper; report full-run timing separately.

## 8. One-day feasibility and stop rule

Estimate for one focused implementer with existing infrastructure: protocol/ADR 0.5h; executor/gym/provenance seam 2h; authenticated batch routes and admission/replay 2h; CLI/template 1.5h; UI grouping/labels 1h; tests and review 2h. Roughly **9 hours**, plus contingency; not a guaranteed schedule. Coordinate with the backend/security worker before editing shared files.

Checkpoint after the solver/provenance seam: if accurate null metrics, shared persistence, or public-board grouping requires broad refactoring, stop before enabling any upload endpoint. Fallback is the honestly labeled existing Vultr model mode and a local adapter demonstration that is not advertised as live-board integration. Full-agent worker hosting, arbitrary endpoint support, callbacks, per-task repair queues and private hosted drafts are out of scope.

The local agent may use any provider under the judge's control; this protocol cannot attest its inference routing. Keep the official Track 01 demonstration on built-in Vultr routes unless organizers explicitly accept the external-artifact mode. No claim that a full external agent was run or contained on Vultr.
