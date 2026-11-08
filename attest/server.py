"""FastAPI control plane for the eval gym.

Deployed on a Vultr Cloud Compute instance; the public demo URL points here
through a Cloudflare quick tunnel.

    uvicorn attest.server:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import asyncio
import json
import os
import queue
import threading
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import gym, llm
from .agent import AGENT_ALIASES, AgentSpec, reference_agents
from .attacks import ATTACK_CORPUS
from .ledger import Ledger
from .sandbox import detect_runtime
from .tasks import SEEDED_SUITE, Task, generate_suite
from .gym import suite_version

HERE = Path(__file__).resolve().parent
WEB_DIR = HERE / "web"
RUNS_DIR = HERE.parent / "runs"
RUNS_DIR.mkdir(exist_ok=True)

LEDGER = Ledger(os.environ.get("ATTEST_DB", str(RUNS_DIR.parent / "attest.db")))

app = FastAPI(title="ATTEST — Eval Gym", version="0.1.0")

# --- in-memory state ------------------------------------------------------------

RUNS: dict[str, gym.RunResult] = {}
SUITES: dict[str, list[Task]] = {}
SUITE_META: dict[str, dict] = {}
STREAMS: dict[str, queue.Queue] = {}

# Load runs persisted by an earlier process so the leaderboard survives a restart.
for path in sorted(RUNS_DIR.glob("*.json")):
    try:
        data = json.loads(path.read_text())
    except Exception:
        continue
    run = gym.run_from_dict(data)
    if run is not None:
        RUNS[run.run_id] = run


# --- request models -------------------------------------------------------------

class SuiteRequest(BaseModel):
    topic: str = "data analysis and reporting"
    generate: bool = False
    n_task: int = Field(default=4, ge=1, le=12)
    n_adversarial: int = Field(default=3, ge=1, le=12)
    n_containment: int = Field(default=3, ge=1, le=12)


class CustomAgent(BaseModel):
    name: str = "dropped-in agent"
    base_url: str
    model: str
    api_key: str = ""
    style: str = "compliant"


class EndpointSpec(BaseModel):
    """An OpenAI-compatible endpoint for a dropped-in agent."""
    base_url: str
    model: str = ""
    api_key: str = ""
    style: str = "compliant"


class AgentPayload(BaseModel):
    """The frozen POST /api/run agent object: {endpoint?, name}."""
    name: str = "compliant"
    endpoint: EndpointSpec | None = None


class RunRequest(BaseModel):
    # Frozen shape (docs/adal/spec.md): {agent: {endpoint?, name}, tasks?: [ids]}
    agent: AgentPayload | None = None
    tasks: list[str] | None = None
    # Legacy shape, still accepted so the existing UI keeps working.
    agent_id: str | None = None
    custom: CustomAgent | None = None
    suite_id: str | None = None
    public: bool = True


class PromoteRequest(BaseModel):
    run_id: str
    task_id: str


# --- helpers --------------------------------------------------------------------

def _agent_for(req: RunRequest) -> AgentSpec:
    refs = reference_agents()
    if req.agent is not None:
        a = req.agent
        if a.endpoint is not None:
            e = a.endpoint
            return AgentSpec(
                id="custom-" + uuid.uuid4().hex[:6],
                name=a.name or "dropped-in agent",
                model=e.model or llm.MODEL_SUITE,
                base_url=e.base_url.rstrip("/"),
                api_key=e.api_key,
                style=e.style,
                description="Agent dropped into the gym by the user.",
            )
        want = AGENT_ALIASES.get(a.name, a.name)
        for ref in refs:
            if want in (ref.id, ref.name) or want == ref.name.split(" ")[0]:
                return ref
        raise HTTPException(status_code=400, detail=f"unknown agent '{a.name}'")
    if req.custom is not None:
        c = req.custom
        return AgentSpec(
            id="custom-" + uuid.uuid4().hex[:6],
            name=c.name,
            model=c.model,
            base_url=c.base_url.rstrip("/"),
            api_key=c.api_key,
            style=c.style,
            description="Agent dropped into the gym by the user.",
        )
    want = AGENT_ALIASES.get(req.agent_id or "compliant", req.agent_id or "compliant")
    for a in refs:
        if a.id == want:
            return a
    raise HTTPException(status_code=400, detail=f"unknown agent '{req.agent_id}'")


def _suite_for(req: RunRequest) -> tuple[list[Task], str]:
    if req.suite_id and req.suite_id in SUITES:
        tasks = list(SUITES[req.suite_id])
        source = SUITE_META[req.suite_id].get("source", "cached")
    else:
        tasks = list(SEEDED_SUITE)
        source = "seeded"
    if req.tasks:
        by_id = {t.id: t for t in tasks}
        missing = [tid for tid in req.tasks if tid not in by_id]
        if missing:
            raise HTTPException(status_code=400, detail=f"unknown task ids: {missing}")
        tasks = [by_id[tid] for tid in req.tasks]
    return tasks, source


def _persist(run: gym.RunResult) -> None:
    try:
        (RUNS_DIR / f"{run.run_id}.json").write_text(json.dumps(run.to_dict(), indent=2))
    except Exception:
        pass


# --- routes ---------------------------------------------------------------------

@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "runtime": detect_runtime(),
        "inference": llm.probe(),
        "suite_version": suite_version(list(SEEDED_SUITE)),
        "attacks": len(ATTACK_CORPUS),
        "runs": len(RUNS),
    }


@app.get("/api/agents")
def agents():
    return {
        "reference": [a.to_dict() for a in reference_agents()],
        "models": {
            "default": llm.MODEL_SUITE,
            "strong": llm.MODEL_STRONG,
            "vision": llm.MODEL_VISION,
            "safety": llm.MODEL_SAFETY,
        },
        "base_url": llm.BASE_URL,
    }


@app.get("/api/suite/seeded")
def seeded_suite():
    tasks = list(SEEDED_SUITE)
    sid = f"seeded-{suite_version(tasks)}"
    SUITES[sid] = tasks
    SUITE_META[sid] = {"source": "seeded", "version": suite_version(tasks)}
    return {"suite_id": sid, "source": "seeded", "version": suite_version(tasks),
            "tasks": [t.to_dict() for t in tasks]}


@app.post("/api/suite")
def make_suite(req: SuiteRequest):
    if not req.generate:
        return seeded_suite()
    tasks = generate_suite(
        req.topic,
        n_task=req.n_task,
        n_adversarial=req.n_adversarial,
        n_containment=req.n_containment,
    )
    source = "model"
    if not tasks:
        # The model did not produce a usable suite. Fall back to the seeded one
        # rather than showing an empty gym.
        tasks = list(SEEDED_SUITE)
        source = "seeded-fallback"
    sid = f"{source}-{uuid.uuid4().hex[:8]}"
    SUITES[sid] = tasks
    SUITE_META[sid] = {"source": source, "version": suite_version(tasks)}
    return {"suite_id": sid, "source": source, "version": suite_version(tasks),
            "tasks": [t.to_dict() for t in tasks]}


@app.post("/api/run")
def start_run(req: RunRequest):
    agent = _agent_for(req)
    tasks, source = _suite_for(req)
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    q: queue.Queue = queue.Queue()
    STREAMS[run_id] = q

    def emit(event: dict) -> None:
        q.put(event)

    def worker() -> None:
        try:
            run = gym.run_suite(agent, tasks, ledger=LEDGER, suite_source=source, on_event=emit)
            run.public = req.public
            RUNS[run.run_id] = run
            _persist(run)
            emit({"type": "run_stored", "run_id": run.run_id})
        except Exception as exc:  # pragma: no cover
            emit({"type": "run_error", "error": f"{type(exc).__name__}: {exc}"})
        finally:
            time.sleep(0.2)
            q.put(None)

    threading.Thread(target=worker, daemon=True).start()
    return {"run_id": run_id, "agent": agent.to_dict(), "suite_source": source,
            "task_count": len(tasks)}


@app.get("/api/run/{run_id}/events")
async def stream_events(run_id: str):
    if run_id not in STREAMS:
        raise HTTPException(status_code=404, detail="unknown run")

    async def gen():
        q = STREAMS[run_id]
        while True:
            try:
                event = await asyncio.to_thread(q.get, timeout=30)
            except queue.Empty:
                yield ": keepalive\n\n"
                continue
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/run/{run_id}")
def get_run(run_id: str):
    """The frozen 4-layer scorecard shape (docs/adal/spec.md)."""
    run = RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="unknown run")
    return gym.run_view(run, list(RUNS.values()))


@app.get("/api/run/{run_id}/detail")
def get_run_detail(run_id: str):
    """Full verbose run detail (the pre-frozen shape), for deep dives."""
    run = RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="unknown run")
    return run.to_dict()


@app.get("/api/run/{run_id}/otel.json")
def run_otel(run_id: str):
    """OTLP/JSON trace export; importable into Arize Phoenix."""
    run = RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="unknown run")
    return gym.otel_export(run, list(RUNS.values()))


@app.get("/api/scorecard/{run_id}")
def scorecard(run_id: str):
    run = RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="unknown run")
    return run.scorecard()


@app.get("/api/leaderboard")
def board():
    runs = list(RUNS.values())
    return {
        "rows": gym.agent_leaderboard(runs),      # frozen shape: one row per agent
        "detail_rows": gym.leaderboard(runs),     # supplementary: one row per run
    }


@app.post("/api/regression/promote")
def promote_regression(req: PromoteRequest):
    """Promote Failure to Regression Suite: a failed or contained trace
    becomes a permanent test case, verbatim."""
    run = RUNS.get(req.run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"unknown run '{req.run_id}'")
    tr = next((t for t in run.tasks if t.task.id == req.task_id), None)
    if tr is None:
        raise HTTPException(status_code=404,
                            detail=f"task '{req.task_id}' not in run '{req.run_id}'")
    passed_clean = tr.verdict.passed and (tr.containment or {}).get("outcome") in ("refused", "safe")
    if passed_clean:
        raise HTTPException(status_code=400,
                            detail="only failed or contained traces can be promoted")
    case_id, created = LEDGER.save_regression_case(gym.build_regression_case(run, tr))
    return {"regression_case_id": case_id, "created": created}


@app.get("/api/regression/cases")
def regression_cases():
    return {"cases": LEDGER.regression_cases()}


@app.get("/api/compare")
def compare(base: str, head: str):
    b, h = RUNS.get(base), RUNS.get(head)
    if b is None or h is None:
        raise HTTPException(status_code=404, detail="unknown run")
    return gym.compare_runs(b, h)


@app.get("/api/evidence/{run_id}")
def evidence(run_id: str):
    """The downloadable evidence pack: the full hash-chained history."""
    pack = LEDGER.export(run_id)
    pack["scorecard"] = RUNS[run_id].scorecard() if run_id in RUNS else None
    return pack


@app.get("/api/selftest")
def selftest():
    """Run the attack corpus live and report what was contained."""
    from .sandbox import run_code

    results = []
    for attack in ATTACK_CORPUS:
        res = run_code(attack.source, timeout=attack.timeout)
        contained, evidence_text = attack.detector(res)
        results.append({
            "id": attack.id, "title": attack.title, "class": attack.cls,
            "contained": contained, "evidence": evidence_text,
            "exit_code": res.exit_code, "duration_ms": res.duration_ms,
        })
    return {
        "runtime": detect_runtime(),
        "total": len(results),
        "contained": sum(1 for r in results if r["contained"]),
        "results": results,
    }


if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")
