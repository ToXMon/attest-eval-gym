"""Hash-chained run ledger.

Every event in a run is appended to a chain: each row carries the SHA-256 of
the previous row's content plus its own canonical content. Editing, deleting or
reordering any event breaks the chain at that point, so a published scorecard
can be checked rather than believed.

    ledger = Ledger("attest.db")
    h1 = ledger.append("run-1", "suite_generated", {"tasks": 8})
    h2 = ledger.append("run-1", "task_result", {"task": "t3", "passed": True})
    ledger.verify("run-1")   # -> True
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from typing import Any

GENESIS = "0" * 64


def _canonical(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _hash(prev_hash: str, kind: str, payload: dict, ts: float) -> str:
    material = f"{prev_hash}|{kind}|{_canonical(payload)}|{ts}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


@dataclass
class LedgerEvent:
    seq: int
    run_id: str
    kind: str
    payload: dict
    ts: float
    prev_hash: str
    content_hash: str

    def to_dict(self) -> dict:
        return {
            "seq": self.seq,
            "kind": self.kind,
            "payload": self.payload,
            "ts": self.ts,
            "prev_hash": self.prev_hash,
            "content_hash": self.content_hash,
        }


class Ledger:
    """Append-only, hash-chained event log backed by SQLite."""

    def __init__(self, path: str = "attest.db"):
        self.path = path
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    seq           INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id        TEXT NOT NULL,
                    kind          TEXT NOT NULL,
                    payload       TEXT NOT NULL,
                    ts            REAL NOT NULL,
                    prev_hash     TEXT NOT NULL,
                    content_hash  TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_run ON events(run_id, seq)")

    # --- writes ------------------------------------------------------------

    def append(self, run_id: str, kind: str, payload: dict | None = None) -> str:
        """Append one event to the chain and return its content hash."""
        payload = payload or {}
        with self._conn() as conn:
            row = conn.execute(
                "SELECT content_hash FROM events WHERE run_id = ? ORDER BY seq DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            prev = row[0] if row else GENESIS
            ts = time.time()
            chash = _hash(prev, kind, payload, ts)
            conn.execute(
                "INSERT INTO events (run_id, kind, payload, ts, prev_hash, content_hash) VALUES (?,?,?,?,?,?)",
                (run_id, kind, _canonical(payload), ts, prev, chash),
            )
        return chash

    # --- reads -------------------------------------------------------------

    def events(self, run_id: str) -> list[LedgerEvent]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT seq, run_id, kind, payload, ts, prev_hash, content_hash "
                "FROM events WHERE run_id = ? ORDER BY seq",
                (run_id,),
            ).fetchall()
        return [
            LedgerEvent(seq=r[0], run_id=r[1], kind=r[2], payload=json.loads(r[3]),
                        ts=r[4], prev_hash=r[5], content_hash=r[6])
            for r in rows
        ]

    def verify(self, run_id: str) -> bool:
        """Recompute the chain. False means the history was tampered with."""
        prev = GENESIS
        for ev in self.events(run_id):
            if ev.prev_hash != prev:
                return False
            if _hash(ev.prev_hash, ev.kind, ev.payload, ev.ts) != ev.content_hash:
                return False
            prev = ev.content_hash
        return True

    def head(self, run_id: str) -> str:
        evs = self.events(run_id)
        return evs[-1].content_hash if evs else GENESIS

    def run_ids(self) -> list[str]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT run_id FROM events ORDER BY run_id"
            ).fetchall()
        return [r[0] for r in rows]

    def export(self, run_id: str) -> dict:
        """A portable evidence pack for one run."""
        evs = self.events(run_id)
        return {
            "run_id": run_id,
            "event_count": len(evs),
            "head_hash": evs[-1].content_hash if evs else GENESIS,
            "chain_valid": self.verify(run_id),
            "events": [e.to_dict() for e in evs],
        }
