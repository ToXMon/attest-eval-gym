# ATTEST — Frozen Spec v1 (2026-11-07)

Product: **ATTEST — The Agent Eval & Containment Gym.**
Pitch: *"Drop your agent in. Get a failing task suite, a capability vs. regression board, and a public scorecard — including whether the sandbox had to save it."*

## User goal
A judge opens the public demo, selects a built-in agent or supplies their own key for the approved Vultr inference endpoint, and runs a 1-Click Fast Eval (4 tasks, including an `/etc/shadow` probe). The UI shows ledger evidence, estimated USD cost, latency, convergence, and observed containment results. The full attack corpus is a separate action; completion time is not guaranteed.

## Architecture (existing, proven)
FastAPI control plane (`attest/server.py`) → Docker/gVisor sandbox (`attest/sandbox.py`, network=none, read-only, cap-drop ALL, uid 65534, wall-clock caps) → deterministic oracles (`attest/oracles.py`) → hash-chained SQLite ledger (`attest/ledger.py`) → single-page UI (`attest/web/index.html`).

## Frozen contracts

### Task schema (`attest/tasks.py`)
```json
{
  "id": "string",
  "request": "string",
  "context_records": [ ... ],
  "expected_oracle": { "name": "oracle-id", "args": {...} },
  "variant": "complete | partial | contradictory | adversarial-mutation",
  "family": "task-family-id used for convergence grouping"
}
```

### Public endpoint policy

Public custom evals accept only `https://api.vultrinference.com/v1` over HTTPS port 443, with a visitor-supplied `api_key`; they never fall back to server credentials. The optional `agent.endpoint` object contains `{base_url, model?, api_key, style?}`. Both frozen and legacy custom inputs enforce the same policy. Userinfo, alternate hosts or paths, query strings, fragments, and unexpected ports are rejected; provider redirects are disabled. Built-in model agents use Vultr inference. Arbitrary OpenAI-compatible destinations are out of scope unless a separately protected/authenticated mode is added.

Provider failures expose stable error codes and optional HTTP status only, never provider response bodies or request headers. `/api/health` reports local configuration without an inference call.

### `/api` shapes
- `POST /api/run` `{agent: {endpoint?, name}, tasks?: [ids]} → {run_id}`
- `GET /api/run/{run_id}` → `{tasks: [{task_id, variant, layers: {router, trajectory: {required, order, propagation}, outcome: {task, adversarial}, containment: {level, score, achieved_radius}}, convergence_score, model, latency_ms, tokens, cost_usd, p_safe, ledger_hash, otel: "/api/run/{run_id}/otel.json"}]}`
- `GET /api/leaderboard` → rows `{agent_name, mean_score, containment_mean, convergence_mean, total_cost_usd, mean_latency_ms, runs}` sorted by mean_score.
- `POST /api/regression/promote` `{run_id, task_id} → {regression_case_id}` — Promote Failure to Regression Suite.
- `GET /api/run/{run_id}/otel.json` → OTel span JSON exportable to Arize Phoenix.

### Scorecard (per run row, Arize terminology)
Router/Tool Selection · Trajectory & Convergence (3 questions + Convergence Score) · Outcome (TASK, ADVERSARIAL — deterministic only) · Containment (ladder 1.0/1.0/0.5/0.0) · Attempted vs Achieved Radius side-by-side.

## UI requirements
1. 1-Click Fast Eval button top of page + approved Vultr endpoint input (visitor key required).
2. Leaderboard with 6+ seeded agents on first paint (real ledger runs).
3. Regression board tabs labeled **Capability Evals** / **Regression Evals**, badges ▼FIXED / ▲REGRESSED.
4. Per-task card: model, latency, token count, estimated USD cost, classifier-derived `P(safe)` estimate (display only).
5. Two-Layer Defense panel: static pre-flight vs sandbox evidence. Host secrets are not passed as container environment variables; Achieved Radius is classifier-derived and does not prove isolation.

## Deployment
Vultr `vc2-2c-4gb` Ubuntu 24.04 → Docker + gVisor → systemd uvicorn → Cloudflare Quick Tunnel public URL. Secrets in `.env` on VM only.

## Non-goals
Auth (read-only demo), mobile, multi-tenant, LLM-judged verdicts.