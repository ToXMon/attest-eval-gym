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
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import gym, llm
from .agent import AgentSpec, reference_agents
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
        run = gym.RunResult(
            run_id=data["run_id"], agent_id=data["agent_id"], agent_name=data["agent_name"],
            agent_style=data.get("agent_style", "compliant"),
            suite_version=data.get("suite_version", ""), suite_source=data.get("suite_source", "seeded"),
            created_at=data.get("created_at", 0), duration_ms=data.get("duration_ms", 0),
            scores=data.get("scores", {}), ledger_head=data.get("ledger_head", ""),
            chain_valid=data.get("chain_valid", True), public=data.get("public", True),
        )
        RUNS[run.run_id] = run
    except Exception:
        continue


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


class RunRequest(BaseModel):
    agent_id: str = "compliant"
    custom: CustomAgent | None = None
    suite_id: str | None = None
    public: bool = True


# --- helpers --------------------------------------------------------------------

def _agent_for(req: RunRequest) -> AgentSpec:
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
    for a in reference_agents():
        if a.id == req.agent_id:
            return a
    raise HTTPException(status_code=400, detail=f"unknown agent '{req.agent_id}'")


def _suite_for(req: RunRequest) -> tuple[list[Task], str]:
    if req.suite_id and req.suite_id in SUITES:
        return SUITES[req.suite_id], SUITE_META[req.suite_id].get("source", "cached")
    return list(SEEDED_SUITE), "seeded"


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
    run = RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="unknown run")
    return run.to_dict()


@app.get("/api/scorecard/{run_id}")
def scorecard(run_id: str):
    run = RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="unknown run")
    return run.scorecard()


@app.get("/api/leaderboard")
def board():
    return {"rows": gym.leaderboard(list(RUNS.values()))}


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
