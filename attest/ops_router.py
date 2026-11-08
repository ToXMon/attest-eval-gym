"""Operational-agent HTTP routes (ADR 0004: additive /api/ops namespace).

The frozen /api shapes are untouched; this router only ADDS routes. Mounted
from attest.server via app.include_router(ops_router).

Auth model (documented in the ADR; spec's read-only demo stays keyless):
  * operator endpoints (start with fault injection, cancel, replay, requote)
    require the ATTEST_OPS_TOKEN bearer (constant-time compare, from env).
  * the public demo start endpoint requires no token but is bounded by the
    shared admission middleware and only runs the fixed demo scenarios with
    the server-side demo_fixture authority. Ordinary callers can NEVER:
    grant approvals, select the authority, inject faults, or reset state.
  * the broker has no listener of its own: it is reachable only through this
    trusted control-plane process.

Streams: one in-memory queue per active run for the LIVE view. Durable truth
is the on-disk store: GET events replays persisted events (written to disk
before exposure) regardless of queue lifetime.
"""

from __future__ import annotations

import asyncio
import hmac
import json
import os
import queue
import threading
import time
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import llm
from .errors import redact_value, safe_error
from .merchant import Merchant
from .ops_store import OpsStore
from .procurement_agent import (ALL_SCENARIOS, DEFAULT_OPS_MODEL, PROBE_SCENARIOS,
                                SCENARIOS, start_ops_run)

OPS_TOKEN = os.environ.get("ATTEST_OPS_TOKEN", "")
BROKER_DB = os.environ.get("ATTEST_BROKER_DB",
                           "/var/lib/attest/broker.db")
OPS_DB = os.environ.get("ATTEST_OPS_DB", "/var/lib/attest/ops_runs.db")

router = APIRouter(prefix="/api/ops", tags=["ops"])


def _local_state_dir() -> str:
    """When the service-managed dirs are not writable (local dev), fall back
    to a repo-local ./ops_state directory. Deploy sets ATTEST_OPS_STATE_DIR."""
    forced = os.environ.get("ATTEST_OPS_STATE_DIR")
    if forced:
        return forced
    for candidate in (os.path.dirname(OPS_DB), "/var/lib/attest"):
        try:
            os.makedirs(candidate, exist_ok=True)
            probe = os.path.join(candidate, ".w")
            with open(probe, "w"):
                pass
            os.unlink(probe)
            return candidate
        except OSError:
            continue
    here = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "ops_state")
    os.makedirs(here, exist_ok=True)
    return here


_STATE_DIR = _local_state_dir()
MERCHANT = Merchant(os.environ.get(
    "ATTEST_BROKER_DB", os.path.join(_STATE_DIR, "broker.db")))
STORE = OpsStore(os.environ.get(
    "ATTEST_OPS_DB", os.path.join(_STATE_DIR, "ops_runs.db")))
# Restart recovery: in-flight runs at boot are marked failed, never faked.
STORE.mark_interrupted_failed()

STREAMS: dict[str, queue.Queue] = {}
ACTIVE: dict[str, dict] = {}
_LOCK = threading.Lock()
MAX_CONCURRENT_OPS_RUNS = int(os.environ.get("ATTEST_OPS_MAX_CONCURRENT", "2"))


def _require_operator(request: Request) -> None:
    """Constant-time bearer check; no token configured -> operator routes are
    disabled (fail closed)."""
    if not OPS_TOKEN:
        raise HTTPException(status_code=503, detail="operator routes disabled")
    auth = request.headers.get("authorization", "")
    supplied = auth[7:] if auth.lower().startswith("bearer ") else ""
    if not supplied or not hmac.compare_digest(supplied, OPS_TOKEN):
        raise HTTPException(status_code=401, detail="operator auth required")


def _view(run_id: str) -> dict:
    """Public run view: durable record + recomputed grading + canonical links.
    Grading is ALWAYS recomputed from the broker at read time."""
    row = STORE.get_run(run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="unknown ops run")
    record = row.get("result") or {}
    if record and record.get("scenario") in SCENARIOS:
        from .ops_evaluator import grade_ops_run
        record["evaluation"] = grade_ops_run(record, MERCHANT)
    view = {
        "run_id": run_id,
        "scenario": row["scenario"],
        "model": row["model"],
        "status": row["status"],
        "mode": record.get("mode", "operational-demo"),
        "merchant": "Test merchant \u00b7 no real charge",
        "created_at": row["created_at"],
        "record": record,
        "chain_valid": STORE.chain_valid(run_id),
        "links": {
            "events": f"/api/ops/run/{run_id}/events",
            "evidence": f"/api/ops/run/{run_id}/evidence",
        },
    }
    return redact_value(view)


class DemoStartRequest(BaseModel):
    model_config = {"extra": "forbid"}
    scenario: str = Field(pattern="^(benign|injection|probe-credential|probe-network|probe-privilege)$")


class OperatorStartRequest(BaseModel):
    scenario: str
    model: str = DEFAULT_OPS_MODEL
    demo_fixture: bool = True
    run_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{6,64}$")


class CancelRequest(BaseModel):
    run_id: str


class ReplayRequest(BaseModel):
    action_id: str = Field(min_length=6, max_length=64)


class RequoteRequest(BaseModel):
    quote_version: str = Field(min_length=1, max_length=32)


def _spawn(scenario: str, model: str, demo_fixture: bool,
           run_id: str | None = None) -> str:
    with _LOCK:
        if len(ACTIVE) >= MAX_CONCURRENT_OPS_RUNS:
            raise HTTPException(status_code=429, detail="ops concurrency limit")
        run_id = run_id or ("ops-" + uuid.uuid4().hex[:12])
        if STORE.get_run(run_id) is not None:
            raise HTTPException(status_code=409, detail="run id already exists")
        q: queue.Queue = queue.Queue()
        STREAMS[run_id] = q
        ACTIVE[run_id] = {"run_id": run_id, "scenario": scenario,
                          "status": "running", "started_at": time.time()}

    def emit(event: dict) -> None:
        q.put(event)

    def worker() -> None:
        try:
            start_ops_run(scenario, STORE, MERCHANT, model=model,
                          demo_fixture=demo_fixture, on_event=emit,
                          run_id=run_id)
            with _LOCK:
                ACTIVE[run_id]["status"] = "finished"
        except Exception as exc:
            with _LOCK:
                ACTIVE[run_id]["status"] = "failed"
            emit({"type": "run_error", "run_id": run_id,
                  "error": safe_error(exc, "run_worker_failed")})
        finally:
            emit(None)   # end-of-stream sentinel
            time.sleep(30)   # keep late subscribers able to drain
            with _LOCK:
                STREAMS.pop(run_id, None)
                ACTIVE.pop(run_id, None)

    threading.Thread(target=worker, daemon=True, name=f"ops-{run_id}").start()
    return run_id


@router.post("/demo/start")
def demo_start(req: DemoStartRequest, request: Request):
    """Public fixed-demo start. Scenario is fixed; authority is ALWAYS the
    server-side demo_fixture; no fault injection, no model selection."""
    if not llm.API_KEY and req.scenario in SCENARIOS:
        raise HTTPException(status_code=503, detail="inference not configured")
    run_id = _spawn(req.scenario, DEFAULT_OPS_MODEL, demo_fixture=True)
    return {"run_id": run_id, "scenario": req.scenario, "status": "running",
            "mode": "operational-demo",
            "approval_authority": "demo_fixture (server-side; Test-harness approval)",
            "merchant": "Test merchant \u00b7 no real charge",
            "links": {"run": f"/api/ops/run/{run_id}",
                      "events": f"/api/ops/run/{run_id}/events",
                      "evidence": f"/api/ops/run/{run_id}/evidence"}}


@router.post("/start")
def operator_start(req: OperatorStartRequest, request: Request):
    """Operator-only start (model override, fixture authority off, fixed run
    id for scripted tests)."""
    _require_operator(request)
    if req.scenario not in ALL_SCENARIOS:
        raise HTTPException(status_code=400, detail="unknown scenario")
    run_id = _spawn(req.scenario, req.model or DEFAULT_OPS_MODEL,
                    req.demo_fixture, req.run_id)
    return {"run_id": run_id, "scenario": req.scenario, "status": "running"}


@router.post("/cancel")
def cancel(req: CancelRequest, request: Request):
    """Operator cancel: prevents later dispatch; committed effects stay."""
    _require_operator(request)
    canceled = STORE.cancel_run(req.run_id)
    return {"run_id": req.run_id, "canceled": canceled,
            "note": "committed broker effects remain committed"}


@router.post("/replay")
def replay(req: ReplayRequest, request: Request):
    """Lost-ack replay proof: re-submit a stored action id; the broker must
    return the ORIGINAL result and never create a second order."""
    _require_operator(request)
    before = MERCHANT.order_count()
    result = MERCHANT.replay_stored(req.action_id)
    if result is None:
        raise HTTPException(status_code=404, detail="unknown action id")
    return {**result, "orders_before": before,
            "orders_after": MERCHANT.order_count(),
            "dedupe_holds": MERCHANT.order_count() == before}


@router.post("/requote")
def requote(req: RequoteRequest, request: Request):
    """Operator-only quote bump (stale-version enforcement tests)."""
    _require_operator(request)
    MERCHANT.requote(req.quote_version)
    return {"quote_version": MERCHANT.current_quote_version()}


@router.get("/run/{run_id}")
def get_run(run_id: str):
    return _view(run_id)


@router.get("/runs")
def list_runs():
    return {"runs": STORE.list_runs()}


@router.get("/run/{run_id}/events")
def get_events(run_id: str, after: int = 0):
    """Durable event log (persisted to disk BEFORE exposure)."""
    if STORE.get_run(run_id) is None:
        raise HTTPException(status_code=404, detail="unknown ops run")
    events = [e for e in STORE.events(run_id) if e["seq"] > after]
    return {"run_id": run_id, "after": after, "events": redact_value(events),
            "chain_valid": STORE.chain_valid(run_id)}


@router.get("/run/{run_id}/stream")
async def stream(run_id: str):
    """Live SSE view of the CURRENT run only; durable truth is /events.
    Replays persisted events first, then tails the in-memory queue."""
    if STORE.get_run(run_id) is None:
        raise HTTPException(status_code=404, detail="unknown ops run")
    q = STREAMS.get(run_id)
    backlog = STORE.events(run_id)

    async def gen():
        for e in backlog:
            yield f"data: {json.dumps({'type': e['kind'], 'run_id': run_id, **e['payload']})}\n\n"
        if q is None:
            row = STORE.get_run(run_id)
            yield f"data: {json.dumps({'type': 'run_state', 'run_id': run_id, 'status': row['status'] if row else 'unknown'})}\n\n"
            return
        while True:
            try:
                event = await asyncio.to_thread(q.get, timeout=30)
            except queue.Empty:
                yield ": keepalive\n\n"
                continue
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"
        row = STORE.get_run(run_id)
        yield f"data: {json.dumps({'type': 'run_state', 'run_id': run_id, 'status': row['status'] if row else 'unknown'})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


@router.get("/run/{run_id}/evidence")
def evidence(run_id: str):
    """Full sanitized evidence pack: durable record, events, broker state,
    per-execution sandbox proof, recomputed grading."""
    view = _view(run_id)
    record = view.get("record") or {}
    orders = MERCHANT.orders_for_run(run_id)
    approvals = MERCHANT.approvals_for_run(run_id)
    return redact_value({
        "run_id": run_id,
        "scenario": view["scenario"],
        "status": view["status"],
        "chain_valid": view["chain_valid"],
        "events": STORE.events(run_id),
        "evaluation": record.get("evaluation"),
        "steps": record.get("steps", []),
        "analysis": (record.get("evidence") or {}).get("analysis"),
        "broker": {"orders": orders, "approvals": approvals,
                   "quote_version": MERCHANT.current_quote_version()},
        "usage": record.get("usage"),
        "sandbox": record.get("sandbox"),
        "mode": record.get("mode"),
        "merchant": "Test merchant \u00b7 no real charge",
        "boundary": record.get("boundary") or (
            "generated code executes inside gVisor; orchestration and broker "
            "are trusted control-plane code outside it"),
    })


@router.get("/health")
def ops_health():
    return {
        "ok": True,
        "inference_configured": bool(llm.API_KEY),
        "ops_model": DEFAULT_OPS_MODEL,
        "operator_auth_configured": bool(OPS_TOKEN),
        "broker_db": os.path.basename(MERCHANT.db_path),
        "ops_db": os.path.basename(STORE.path),
        "runs": len(STORE.list_runs(limit=1000)),
        "active": len(ACTIVE),
        "merchant": "Test merchant \u00b7 no real charge",
    }
