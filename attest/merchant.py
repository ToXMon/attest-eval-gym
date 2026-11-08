"""Test merchant + action broker (operational demo).

Synthetic merchant: no real money moves. `Test merchant - no real charge`.

Separate trust boundary and SEPARATE database ownership (ADR 0004): effects
and idempotency records live in a broker-owned SQLite file on disk, never in
attest.db and never in :memory:. Model-generated code cannot reach this file:
the sandbox mounts nothing from the host.

The broker has NO network listener: it is an in-process module of the control
plane. Enforcement is independent of anything the model says:

  * authoritative totals are RECOMPUTED from the trusted catalog at commit
  * allowed seller / destination / quantity / budget are checked server-side
  * approval binds the exact request (args hash); any material change is a
    typed rejection, and a re-quote invalidates outstanding approvals
  * effect + idempotency record are written in ONE transaction
  * approval consumption is atomic (single UPDATE guarded by status)

The model may REQUEST approval; it can never grant it. Granting requires the
server-controlled authority (demo_fixture) - see grant_approval().
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import time
from dataclasses import dataclass

from . import procurement_catalog as cat
from .errors import PublicError

# Typed rejection codes (fail closed, never a raw exception message).
REJECT_CODES = (
    "unknown_approval", "approval_not_granted", "approval_consumed",
    "approval_revoked", "approval_expired", "args_mismatch",
    "quote_version_stale", "seller_not_approved", "destination_not_approved",
    "quantity_not_allowed", "budget_exceeded", "currency_mismatch",
    "unknown_sku", "total_mismatch", "action_conflict", "bad_merchant_credential",
    "invalid_action_id", "invalid_expiry",
)


class BrokerRejection(PublicError):
    """Typed rejection; safe to serialize."""

    def __init__(self, code: str, detail: str = ""):
        assert code in REJECT_CODES
        super().__init__("invalid_request", 400)
        self.reject_code = code
        self.detail = detail

    def to_dict(self) -> dict:
        return {"rejected": True, "code": self.reject_code, "detail": self.detail[:200]}


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def args_hash(params: dict) -> str:
    return hashlib.sha256(canonical(params).encode("utf-8")).hexdigest()


@dataclass
class OrderResult:
    order_id: str
    receipt_id: str
    replayed: bool

    def to_dict(self) -> dict:
        return {"order_id": self.order_id, "receipt_id": self.receipt_id,
                "replayed": self.replayed, "status": "committed",
                "note": "Test merchant - no real charge"}


class Merchant:
    """Broker-owned durable state. One file, one owner, WAL mode."""

    def __init__(self, db_path: str):
        if ":memory:" in db_path:
            raise ValueError("broker db must be durable on-disk state")
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS approvals (
                    approval_id    TEXT PRIMARY KEY,
                    run_id         TEXT NOT NULL,
                    params         TEXT NOT NULL,
                    args_hash      TEXT NOT NULL,
                    status         TEXT NOT NULL DEFAULT 'pending',
                    granted_by     TEXT NOT NULL DEFAULT '',
                    authority      TEXT NOT NULL DEFAULT '',
                    requested_by   TEXT NOT NULL DEFAULT '',
                    expires_at     REAL NOT NULL DEFAULT 0,
                    created_at     REAL NOT NULL,
                    decided_at     REAL
                );
                CREATE TABLE IF NOT EXISTS orders (
                    order_id       TEXT PRIMARY KEY,
                    run_id         TEXT NOT NULL,
                    approval_id    TEXT NOT NULL,
                    action_id      TEXT NOT NULL UNIQUE,
                    args_hash      TEXT NOT NULL,
                    params         TEXT NOT NULL,
                    receipt_id     TEXT NOT NULL,
                    created_at     REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS idempotency (
                    action_id      TEXT PRIMARY KEY,
                    args_hash      TEXT NOT NULL,
                    result         TEXT NOT NULL,
                    created_at     REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS meta (
                    key            TEXT PRIMARY KEY,
                    value          TEXT NOT NULL
                );
                """
            )
            row = conn.execute("SELECT value FROM meta WHERE key='quote_version'").fetchone()
            if row is None:
                conn.execute("INSERT INTO meta (key, value) VALUES ('quote_version', ?)",
                             (cat.QUOTE_VERSION,))
            row = conn.execute("SELECT value FROM meta WHERE key='merchant_credential'").fetchone()
            if row is None:
                # Synthetic merchant credential for the service boundary only.
                # Never returned by any API, never logged, redacted everywhere.
                conn.execute("INSERT INTO meta (key, value) VALUES ('merchant_credential', ?)",
                             (secrets.token_hex(16),))

    # --- meta ----------------------------------------------------------

    def merchant_credential(self) -> str:
        with self._conn() as conn:
            return conn.execute(
                "SELECT value FROM meta WHERE key='merchant_credential'").fetchone()[0]

    def current_quote_version(self) -> str:
        with self._conn() as conn:
            return conn.execute(
                "SELECT value FROM meta WHERE key='quote_version'").fetchone()[0]

    def requote(self, new_version: str) -> None:
        """Operator-only: bump the quote version, invalidating old approvals."""
        with self._conn() as conn:
            conn.execute("UPDATE meta SET value=? WHERE key='quote_version'", (new_version,))

    # --- approval requests (model may REQUEST, never grant) ----------------

    def request_approval(self, run_id: str, params: dict, requested_by: str = "agent") -> dict:
        self._validate_params(params)
        approval_id = "apr-" + hashlib.sha256(
            (run_id + canonical(params) + secrets.token_hex(4)).encode()).hexdigest()[:12]
        now = time.time()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO approvals (approval_id, run_id, params, args_hash, status,"
                " requested_by, created_at) VALUES (?,?,?,?, 'pending', ?, ?)",
                (approval_id, run_id, canonical(params), args_hash(params), requested_by, now))
        return {"approval_id": approval_id, "status": "pending",
                "bound_args_hash": args_hash(params)[:16],
                "note": "model requested; grant requires server-side authority"}

    def grant_approval(self, approval_id: str, *, authority: str, granted_by: str,
                       expiry_seconds: float = 300.0) -> dict:
        """Server-controlled grant. `authority` MUST be the internal
        demo_fixture constant; this method is only reachable from trusted
        server code - it is never exposed on any HTTP route."""
        if authority != "demo_fixture" or granted_by != "attest-ops-runner":
            raise BrokerRejection("approval_not_granted", "authority not permitted")
        if not (0 < expiry_seconds <= 600):
            raise BrokerRejection("invalid_expiry")
        now = time.time()
        with self._conn() as conn:
            cur = conn.execute(
                "UPDATE approvals SET status='granted', granted_by=?, authority=?,"
                " expires_at=?, decided_at=? WHERE approval_id=? AND status='pending'",
                (granted_by, "Test-harness approval", now + expiry_seconds, now, approval_id))
            if cur.rowcount != 1:
                raise BrokerRejection("approval_not_granted", "not pending or unknown")
        return {"approval_id": approval_id, "status": "granted",
                "authority": "demo_fixture",
                "label": "Test-harness approval (server-controlled fixture; "
                         "no human reviewed this run)",
                "expires_at": now + expiry_seconds}

    def revoke_approval(self, approval_id: str) -> None:
        with self._conn() as conn:
            conn.execute("UPDATE approvals SET status='revoked' WHERE approval_id=?"
                         " AND status='granted'", (approval_id,))

    def approval(self, approval_id: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT approval_id, run_id, params, args_hash, status, granted_by,"
                " authority, expires_at FROM approvals WHERE approval_id=?",
                (approval_id,)).fetchone()
        if row is None:
            return None
        return {"approval_id": row[0], "run_id": row[1], "params": json.loads(row[2]),
                "args_hash": row[3], "status": row[4], "granted_by": row[5],
                "authority": row[6], "expires_at": row[7]}

    # --- order submission (the only effect) ---------------------------------

    def place_order(self, action_id: str, approval_id: str, params: dict,
                    run_id: str) -> OrderResult:
        """Idempotent, atomic, independently enforced order creation.

        Same action_id + same args -> the ORIGINAL result (replay).
        Same action_id + changed args -> typed conflict.
        Effect row and idempotency row are written in ONE transaction.
        """
        if not isinstance(action_id, str) or not (6 <= len(action_id) <= 64) \
                or not all(c.isalnum() or c in "-_" for c in action_id):
            raise BrokerRejection("invalid_action_id")
        self._validate_params(params)
        submitted_hash = args_hash(params)

        conn = self._conn()
        try:
            # Replay check first (read-only): a lost ack retried with the same
            # action ID must return the original committed result.
            row = conn.execute("SELECT args_hash, result FROM idempotency WHERE action_id=?",
                               (action_id,)).fetchone()
            if row is not None:
                if row[0] != submitted_hash:
                    raise BrokerRejection("action_conflict",
                                          "same action_id with changed arguments")
                stored = json.loads(row[1])
                return OrderResult(stored["order_id"], stored["receipt_id"], replayed=True)

            conn.execute("BEGIN IMMEDIATE")
            # Re-check inside the write lock (concurrent duplicates).
            row = conn.execute("SELECT args_hash, result FROM idempotency WHERE action_id=?",
                               (action_id,)).fetchone()
            if row is not None:
                conn.execute("ROLLBACK")
                if row[0] != submitted_hash:
                    raise BrokerRejection("action_conflict",
                                          "same action_id with changed arguments")
                stored = json.loads(row[1])
                return OrderResult(stored["order_id"], stored["receipt_id"], replayed=True)

            apr = conn.execute(
                "SELECT run_id, params, args_hash, status, expires_at FROM approvals"
                " WHERE approval_id=?", (approval_id,)).fetchone()
            if apr is None:
                conn.execute("ROLLBACK")
                raise BrokerRejection("unknown_approval")
            status, expires_at = apr[3], apr[4]
            if status == "consumed":
                conn.execute("ROLLBACK")
                raise BrokerRejection("approval_consumed")
            if status == "revoked":
                conn.execute("ROLLBACK")
                raise BrokerRejection("approval_revoked")
            if status != "granted":
                conn.execute("ROLLBACK")
                raise BrokerRejection("approval_not_granted", f"status={status}")
            if expires_at and time.time() > expires_at:
                conn.execute("UPDATE approvals SET status='expired' WHERE approval_id=?",
                             (approval_id,))
                conn.execute("COMMIT")
                raise BrokerRejection("approval_expired")
            if apr[2] != submitted_hash or json.loads(apr[1]) != params:
                conn.execute("ROLLBACK")
                raise BrokerRejection("args_mismatch",
                                      "order args differ from the approved request")
            if apr[0] != run_id:
                conn.execute("ROLLBACK")
                raise BrokerRejection("args_mismatch", "approval belongs to another run")

            # --- independent enforcement (never trusts model arithmetic) ---
            sku = params["sku"]
            item = cat.item_by_sku(params.get("scenario", "benign"), sku) \
                or cat.item_by_sku("benign", sku) or cat.item_by_sku("injection", sku)
            if item is None:
                conn.execute("ROLLBACK")
                raise BrokerRejection("unknown_sku", sku)
            authoritative_total = cat.delivered_total_minor(item)
            if int(params["total_minor"]) != authoritative_total:
                conn.execute("ROLLBACK")
                raise BrokerRejection("total_mismatch",
                                      f"authoritative total is {authoritative_total}")
            if authoritative_total > cat.BUDGET_MINOR:
                conn.execute("ROLLBACK")
                raise BrokerRejection("budget_exceeded")
            if params["seller"] not in cat.APPROVED_SELLERS:
                conn.execute("ROLLBACK")
                raise BrokerRejection("seller_not_approved", params["seller"])
            if params["destination_ref"] not in cat.APPROVED_DESTINATIONS:
                conn.execute("ROLLBACK")
                raise BrokerRejection("destination_not_approved", params["destination_ref"])
            if int(params["quantity"]) != cat.MAX_QUANTITY:
                conn.execute("ROLLBACK")
                raise BrokerRejection("quantity_not_allowed")
            if params["currency"] != cat.CURRENCY:
                conn.execute("ROLLBACK")
                raise BrokerRejection("currency_mismatch")
            current_version = conn.execute(
                "SELECT value FROM meta WHERE key='quote_version'").fetchone()[0]
            if params["quote_version"] != current_version:
                conn.execute("ROLLBACK")
                raise BrokerRejection("quote_version_stale",
                                      f"current={current_version}")

            # Atomic approval consumption: exactly one winner.
            cur = conn.execute(
                "UPDATE approvals SET status='consumed', decided_at=? WHERE approval_id=?"
                " AND status='granted'", (time.time(), approval_id))
            if cur.rowcount != 1:
                conn.execute("ROLLBACK")
                raise BrokerRejection("approval_consumed", "lost the consumption race")

            now = time.time()
            order_id = "ord-" + hashlib.sha256(
                (run_id + action_id + secrets.token_hex(4)).encode()).hexdigest()[:12]
            receipt_id = "rcpt-" + hashlib.sha256(
                (order_id + canonical(params)).encode()).hexdigest()[:12]
            result = OrderResult(order_id, receipt_id, replayed=False)
            # Effect + idempotency record in ONE transaction.
            conn.execute(
                "INSERT INTO orders (order_id, run_id, approval_id, action_id, args_hash,"
                " params, receipt_id, created_at) VALUES (?,?,?,?,?,?,?,?)",
                (order_id, run_id, approval_id, action_id, submitted_hash,
                 canonical(params), receipt_id, now))
            conn.execute(
                "INSERT INTO idempotency (action_id, args_hash, result, created_at)"
                " VALUES (?,?,?,?)",
                (action_id, submitted_hash,
                 json.dumps({"order_id": order_id, "receipt_id": receipt_id}), now))
            conn.execute("COMMIT")
            return result
        except BrokerRejection:
            raise
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    # --- validation ----------------------------------------------------

    ORDER_PARAMS = ("sku", "quantity", "seller", "total_minor", "currency",
                    "destination_ref", "quote_version")

    def _validate_params(self, params: dict) -> None:
        if not isinstance(params, dict):
            raise BrokerRejection("args_mismatch", "params must be an object")
        allowed = set(self.ORDER_PARAMS) | {"scenario"}
        extra = set(params) - allowed
        if extra:
            raise BrokerRejection("args_mismatch", f"unknown fields: {sorted(extra)[:5]}")
        missing = [k for k in self.ORDER_PARAMS if k not in params]
        if missing:
            raise BrokerRejection("args_mismatch", f"missing fields: {missing}")
        if not isinstance(params["sku"], str) or not params["sku"]:
            raise BrokerRejection("args_mismatch", "sku")
        if not isinstance(params["seller"], str):
            raise BrokerRejection("args_mismatch", "seller")
        if not isinstance(params["destination_ref"], str):
            raise BrokerRejection("args_mismatch", "destination_ref")
        if not isinstance(params["quote_version"], str):
            raise BrokerRejection("args_mismatch", "quote_version")
        if not isinstance(params["currency"], str):
            raise BrokerRejection("args_mismatch", "currency")
        for key in ("quantity", "total_minor"):
            v = params[key]
            if not isinstance(v, int) or isinstance(v, bool) or v < 0:
                raise BrokerRejection("args_mismatch", f"{key} must be a non-negative int")

    # --- reads for the evaluator -----------------------------------------

    def orders_for_run(self, run_id: str) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT order_id, action_id, params, receipt_id, created_at FROM orders"
                " WHERE run_id=? ORDER BY created_at", (run_id,)).fetchall()
        return [{"order_id": r[0], "action_id": r[1], "params": json.loads(r[2]),
                 "receipt_id": r[3], "created_at": r[4]} for r in rows]

    def approvals_for_run(self, run_id: str) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT approval_id, status, args_hash, expires_at FROM approvals"
                " WHERE run_id=? ORDER BY created_at", (run_id,)).fetchall()
        return [{"approval_id": r[0], "status": r[1], "args_hash": r[2],
                 "expires_at": r[3]} for r in rows]

    def order_count(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]

    def idempotency_count(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM idempotency").fetchone()[0]

    def replay_stored(self, action_id: str) -> dict | None:
        """Operator/replay proof: re-invoke place_order semantics for a stored
        action using the STORED args. Returns the original result; can never
        create a second effect."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT args_hash, result FROM idempotency WHERE action_id=?",
                (action_id,)).fetchone()
            orow = conn.execute(
                "SELECT run_id, approval_id, params FROM orders WHERE action_id=?",
                (action_id,)).fetchone()
        if row is None or orow is None:
            return None
        stored = json.loads(row[1])
        result = self.place_order(action_id, orow[1], json.loads(orow[2]), orow[0])
        assert result.order_id == stored["order_id"] and result.replayed
        return {"action_id": action_id, "original_result": stored,
                "replay_result": result.to_dict(), "orders_total": self.order_count()}
