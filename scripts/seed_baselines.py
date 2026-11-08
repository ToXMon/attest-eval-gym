"""Seed the leaderboard with the 6 baseline agents (real Vultr Inference runs).

Every seeded agent runs the full task suite through the real pipeline -- real
model calls in the control plane, real sandbox executions (network=none, no
secrets in containers) -- so the runs land in the hash-chained ledger and the
leaderboard shows real cost/latency/convergence/containment on first paint.

Budget-guarded: the script aborts if estimated spend passes BUDGET_USD.

    python scripts/seed_baselines.py            # seed all 6
    python scripts/seed_baselines.py --probe    # just verify the catalogue answers

The inference key is read from .env (VULTR_INFERENCE_API_KEY) and never
printed. Verdicts stay 100% deterministic oracles; the model-backed safety
annotation and P(safe) are display-only (ADR 0002).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def _load_env() -> None:
    """Parse .env with sed (never source it) and export only what we need."""
    env_file = REPO / ".env"
    if not env_file.exists():
        print("error: .env not found", file=sys.stderr)
        raise SystemExit(1)
    import subprocess
    key = subprocess.run(
        ["sed", "-n", "s/^VULTR_INFERENCE_API_KEY=//p", str(env_file)],
        capture_output=True, text=True,
    ).stdout.strip().splitlines()
    if not key:
        print("error: VULTR_INFERENCE_API_KEY not set in .env", file=sys.stderr)
        raise SystemExit(1)
    val = key[-1].strip().strip('"').strip("'")
    import os
    os.environ["VULTR_INFERENCE_API_KEY"] = val  # never printed


_load_env()

from attest import gym, llm                       # noqa: E402
from attest.agent import reference_agents         # noqa: E402
from attest.ledger import Ledger                  # noqa: E402
from attest.sandbox import detect_runtime         # noqa: E402
from attest.tasks import SEEDED_SUITE             # noqa: E402

BUDGET_USD = 2.00
RUNS_DIR = REPO / "runs"
DB_PATH = REPO / "attest.db"


def probe_catalogue() -> bool:
    models = ["qwen3.8-flash-next", "glm-5.3-flash", "deepseek-v4.1-flash-1017",
              "mimo-v2.6-flash", "nemotron-3.5-content-safety"]
    ok = True
    for m in models:
        r = llm.probe(m)
        mark = "OK  " if r.get("ok") else "FAIL"
        ok &= bool(r.get("ok"))
        extra = r.get("sample") or r.get("error", "")
        print(f"  [{mark}] {m:<32} {str(extra)[:60]}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true", help="only verify the catalogue answers")
    ap.add_argument("--budget", type=float, default=BUDGET_USD)
    args = ap.parse_args()

    print(f"runtime: {detect_runtime()}   ledger: {DB_PATH.name}   budget: ${args.budget:.2f}")
    if args.probe:
        return 0 if probe_catalogue() else 1

    if not probe_catalogue():
        print("catalogue probe failed -- not spending money on a broken endpoint",
              file=sys.stderr)
        return 1

    RUNS_DIR.mkdir(exist_ok=True)
    ledger = Ledger(str(DB_PATH))
    agents = reference_agents()
    print(f"\nseeding {len(agents)} agents over {len(SEEDED_SUITE)} tasks each\n")

    runs = []
    for agent in agents:
        t0 = time.time()
        run = gym.run_suite(agent, list(SEEDED_SUITE), ledger=ledger, suite_source="seeded")
        runs.append(run)
        (RUNS_DIR / f"{run.run_id}.json").write_text(json.dumps(run.to_dict(), indent=2))
        s = run.scores
        spent = llm.meter_cost_usd()
        print(f"  {agent.id:<22} TASK {s['TASK']:<6} ADV {s['ADVERSARIAL']:<6} "
              f"CONTAIN {s['CONTAINMENT']:<6} OVERALL {s['OVERALL']:<6} "
              f"tokens {run.total_tokens:<7} ${run.total_cost_usd:.4f} "
              f"({time.time()-t0:.0f}s)  cumulative ${spent:.4f}  chain={run.chain_valid}")
        if spent > args.budget:
            print(f"\nBUDGET GUARD: ${spent:.4f} > ${args.budget:.2f} -- stopping",
                  file=sys.stderr)
            break

    total = llm.meter_cost_usd()
    board = gym.agent_leaderboard(runs)
    print(f"\n=== leaderboard ({len(board)} rows) ===")
    for row in board:
        print(f"  #{row['rank']:<2} {row['agent_name']:<22} score {row['mean_score']:<7} "
              f"containment {row['containment_mean']:<7} convergence {row['convergence_mean']:<8} "
              f"latency {row['mean_latency_ms']}ms  cost ${row['total_cost_usd']:.4f}  "
              f"runs {row['runs']}")

    print(f"\nmetered calls : {llm.meter().get('_calls', 0)}")
    for m, t in sorted(llm.meter().items()):
        if m != "_calls":
            print(f"  {m:<32} {t:>8} tokens  (~${llm.estimate_cost_usd(m, t):.4f})")
    print(f"TOTAL ESTIMATED SPEND: ${total:.4f} (budget ${args.budget:.2f})")

    ok = (len(board) == len(agents) and total <= args.budget
          and all(r.chain_valid for r in runs))
    print("\nRESULT:", "ALL GREEN" if ok else "NEEDS WORK")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
