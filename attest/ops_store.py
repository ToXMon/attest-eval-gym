"""Durable run-state + sanitized stage events for the operational agent.

ADR 0004: the agent service persists run state and completed-stage events in
its OWN on-disk store (never :memory:, never attest.db). Events are hash-
chained through the proven Ledger class so tampering is detectable, and they
are written to disk BEFORE any API exposes them.

Payloads appended here must already be sanitized/redacted by the caller.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time

from .ledger import Ledger

DEFAULT_OPS_DB = os.environ.get("ATTEST_OPS_DB", "/var/lib/attest/ops_runs.db")


class OpsStore:
    """Run rows + hash-chained stage events in one durable file."""

    def __init__(self, path: str | None = None):
        self.path = path or DEFAULT_OPS_DB
        if ":memory:" in self.path:
            raise ValueError("ops store must be durable on-disk state")
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self.ledger = Ledger(self.path)
        self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ops_runs (
                    run_id     TEXT PRIMARY KEY,
                    scenario   TEXT NOT NULL,
                    model      TEXT NOT NULL DEFAULT '',
                    status     TEXT NOT NULL DEFAULT 'running',
                    result     TEXT NOT NULL DEFAULT '',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )

    # --- runs --------------------------------------------------------

    def create_run(self, run_id: str, scenario: str, model: str = "") -> None:
        now = time.time()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO ops_runs (run_id, scenario, model, status, created_at,"
                " updated_at) VALUES (?,?,?,'running',?,?)",
                (run_id, scenario, model, now, now))

    def finish_run(self, run_id: str, status: str, result: dict | None = None) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE ops_runs SET status=?, result=?, updated_at=? WHERE run_id=?",
                (status, json.dumps(result or {}, default=str), time.time(), run_id))

    def cancel_run(self, run_id: str) -> bool:
        """Operator cancel: only a still-running run can be canceled. Already
        committed broker effects remain committed (the loop checks this flag
        before dispatching any further action)."""
        with self._conn() as conn:
            cur = conn.execute(
                "UPDATE ops_runs SET status='canceled', updated_at=? WHERE run_id=?"
                " AND status='running'", (time.time(), run_id))
            return cur.rowcount == 1

    def mark_interrupted_failed(self) -> list[str]:
        """Restart recovery (E7.7): any run still 'running' when the store is
        opened did not finish honestly. Mark it failed with a typed reason;
        never fake completion, never lose the row. Committed broker effects
        stay in the broker's own durable DB and remain reconcilable."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT run_id FROM ops_runs WHERE status='running'").fetchall()
            now = time.time()
            for (run_id,) in rows:
                conn.execute(
                    "UPDATE ops_runs SET status='failed', result=?, updated_at=?"
                    " WHERE run_id=?",
                    (json.dumps({"run_id": run_id, "status": "failed",
                                 "error": "service_restarted",
                                 "evaluation": {"passed": False,
                                                "outcome": "service_restarted_task_incomplete",
                                                "sections": {}}}),
                     now, run_id))
        for (run_id,) in rows:
            self.append_event(run_id, "run_recovered", {
                "code": "service_restarted",
                "note": ("in-flight run at restart marked failed; committed effects "
                         "remain in broker state and are reconcilable by action id")})
        return [r[0] for r in rows]

    def get_run(self, run_id: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT run_id, scenario, model, status, result, created_at, updated_at"
                " FROM ops_runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            return None
        return {"run_id": row[0], "scenario": row[1], "model": row[2],
                "status": row[3],
                "result": json.loads(row[4]) if row[4] else None,
                "created_at": row[5], "updated_at": row[6]}

    def list_runs(self, limit: int = 50) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT run_id, scenario, model, status, created_at FROM ops_runs"
                " ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [{"run_id": r[0], "scenario": r[1], "model": r[2], "status": r[3],
                 "created_at": r[4]} for r in rows]

    # --- events (durable BEFORE exposure) --------------------------------

    def append_event(self, run_id: str, kind: str, payload: dict) -> str:
        """Persist one sanitized completed-stage event to disk; returns hash."""
        return self.ledger.append(run_id, kind, payload)

    def events(self, run_id: str) -> list[dict]:
        return [{"seq": e.seq, "kind": e.kind, "payload": e.payload, "ts": e.ts,
                 "content_hash": e.content_hash} for e in self.ledger.events(run_id)]

    def chain_valid(self, run_id: str) -> bool:
        return self.ledger.verify(run_id)
