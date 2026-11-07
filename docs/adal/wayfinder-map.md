# Wayfinder Map — ATTEST @ Vultr Agent Rush Track 01

Deadline: **Nov 8, 2026 23:00 UTC** (T-minus ~30h from Nov 7 evening).

## Destination
**All 8 Track-1 gates green + 9.0+ across all 4 judged criteria.** Demo path: judge opens live URL → clicks 1-Click Fast Eval → 4 tasks ~20s → `rm -rf /` probe absorbed (`CONTAINMENT: 0.5 CONTAINED`) → leaderboard row animates in with ledger hash, cost, latency, convergence.

## Landmarks (gates)
G1 agent runs in sandbox · G2 Vultr models used · G3 failing suite produced · G4 regression board · G5 containment proof · G6 cost/latency visible · G7 multi-model · G8 live public URL.

## Route (vertical tracer bullets, in claim order)
1. **API contract freeze + OTel span export** (`/api/run/{run_id}/otel.json`) — AdaL
2. **Task suite expansion to 3-tuple variants** (complete/partial/contradictory/adversarial-mutation) — Pi
3. **Capability pre-flight: transitive import gadgets** in `capabilities.py` — AdaL
4. **Leaderboard UI**: 4-layer scorecard, ▼FIXED/▲REGRESSED badges, Promote-to-Regression button, cost/latency/P(safe) per card — Pi
5. **Vultr deploy script** (VM provision → Docker+gVisor → systemd uvicorn → Quick Tunnel) — AdaL, **needs VULTR_API_KEY allowlisted**
6. **6 seeded baselines via Vultr Inference** incl. `redteam-probe` + real ledger runs — AdaL
7. **1-Click Fast Eval + paste-your-endpoint flow** — Pi (UI) + AdaL (API)
8. **README with Vultr architecture diagram, model table, repro commands; slide outline; 90s demo script** — both

## Open technical tickets (resolved now, no blocking)
- Vultr Inference key creation: user-side, portal instructions delivered.
- Model IDs verified live against `/v1/models` before ticket 6; fallback to any available open-weight IDs (price table in ADR 0002 stays as display copy).

## Bypasses / non-goals
No real billing of inference beyond demo-scale (~$5 budget). No auth on public URL (read-only judge demo; eval posts rate-limited). No mobile UI.