# ATTEST — Agent Eval & Containment Gym

Hackathon: Vultr "Agent Rush", Track 01 (Blast Radius Zero). Deadline Nov 8 2026, 23:00 UTC.

## Agent skills

### Issue tracker

Issues live in **GitHub Issues** on `ToXMon/attest-eval-gym` (via `gh` CLI). See `docs/agents/issue-tracker.md`.

### Domain docs

**Single-context**: root `GLOSSARY.md` + `docs/adr/`. See `docs/agents/domain.md`.

**Deploying, updating the domain/tunnels, or troubleshooting the live site?** Read `docs/agents/deployment.md` first (approved host/tunnel/DNS identifiers, decision table, restart and rollback rules).

## Ground truth

- `docs/adal/plan.md` — architecture; `docs/adal/spec.md` — frozen spec.
- `docs/adal/judging_rubric_analysis.md` — Track 1 gates G1–G8 + 4 scored criteria.
- Proven code: `attest/sandbox.py`, `attest/attacks.py`, `attest/oracles.py`, `attest/ledger.py`, `attest/capabilities.py`. Validate with `python3 scripts/selftest.py` (expect 10/10 attacks contained, 15/15 oracles green) and `python3 scripts/piptest.py`.
- Secrets (`VULTR_API_KEY`, `VULTR_INFERENCE_API_KEY`, `ATTEST_CANARY`) live in `.env`, NEVER exported into sandbox containers, never committed.

## Module ownership (concurrent editors — do not revert others' work)

- **AdaL**: `attest/server.py`, `attest/gym.py`, `attest/llm.py`, `attest/ledger.py`, Vultr deploy (`scripts/deploy*.sh`), OTel export, README/submission.
- **Pi**: `attest/web/`, `attest/tasks.py` (task suites), baseline agents, demo script.
- Shared frozen contract: `/api` JSON shapes + `attest/tasks.py` schema (see `docs/adal/spec.md`). Changing them requires an ADR.
