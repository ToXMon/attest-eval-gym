# ADR 0002: Vultr Multi-Model Routing & Decision Calibration

Date: 2026-11-07 · Status: accepted

## Context
Track 01 scores "Application of Technology" on real Vultr usage; Gate G2/G6/G7 need model diversity. A single-model leaderboard looks synthetic to judges.

## Decision
All model traffic routes through **Vultr Serverless Inference** (`https://api.vultrinference.com/v1`, Bearer `VULTR_INFERENCE_API_KEY`), with a deliberate 5-model routing table:

| Role | Model | Price (in/out per M) |
|---|---|---|
| Suite generator + `naive`/`compliant` agents | qwen3.8-flash-next | $0.10 / $0.20 |
| `careful` agent + repair agent | glm-5.3-flash (or glm-5.3) | $0.10 / $0.35 |
| 4th seeded baseline | deepseek-v4.1-flash-1017 | $0.15 / $0.60 |
| Safety annotation (non-verdict) | nemotron-3.5-content-safety | $0.05 / $0.15 |
| Calibrated `P(safe)` display | pplx-decider-v1.2 or clef-flash | $0.05–$0.10 |

Per-task UI shows model name, latency, token counts, and USD cost. Verdicts remain 100% deterministic (ADR 0001).

## Consequences
- 6+ seeded agents (`naive-qwen`, `compliant-qwen`, `careful-glm`, `deepseek-v4.1-flash`, `mimo-v2.6-flash`, `redteam-probe`) span the score/cost/containment spectrum on first paint.
- Control plane holds keys; containers get network=none and no credentials.