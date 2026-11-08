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
    agent_mod._chat = fake_chat

    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")
        if not cond:
            failures.append(name)

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
        endpoint=EndpointSpec(base_url="https://api.example.com/v1", model="my-model"),
    ))
    agent = srv._agent_for(req)
    check("endpoint agent built from frozen payload",
          agent.model == "my-model" and agent.base_url == "https://api.example.com/v1")

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
