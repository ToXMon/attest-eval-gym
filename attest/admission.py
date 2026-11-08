"""Process-local demo limits. Restarting the process resets these counters."""
from __future__ import annotations

import asyncio
import datetime as dt
import math
import os
import threading
import time
from collections import deque

from fastapi.responses import JSONResponse


class LimitError(RuntimeError):
    pass


class SpendBudget:
    """Reserve before each paid attempt; ambiguous failures retain the reservation."""

    def __init__(self, process=0.50, daily=0.25):
        if not all(math.isfinite(v) and v >= 0 for v in (process, daily)):
            raise ValueError("invalid_budget_configuration")
        self.process_limit = process
        self.daily_limit = daily
        self.total = 0.0
        self.days = {}
        self.lock = threading.Lock()

    def reserve(self, amount):
        day = dt.datetime.now(dt.timezone.utc).date().isoformat()
        with self.lock:
            if not math.isfinite(amount) or amount < 0:
                raise LimitError("invalid_spend_estimate")
            if (self.total + amount > self.process_limit
                    or self.days.get(day, 0) + amount > self.daily_limit):
                raise LimitError("server_budget_exhausted")
            self.total += amount
            self.days[day] = self.days.get(day, 0) + amount
        return day, amount

    def settle(self, ticket, actual):
        day, reserved = ticket
        # Never refund an estimate: missing/invalid usage cannot make calls free.
        extra = max(0.0, actual - reserved)
        with self.lock:
            self.total += extra
            self.days[day] = self.days.get(day, 0) + extra


SPEND = SpendBudget(
    float(os.environ.get("ATTEST_PROCESS_BUDGET_USD", "0.50")),
    float(os.environ.get("ATTEST_DAY_BUDGET_USD", "0.25")),
)


class Lease:
    def __init__(self, owner):
        self.owner = owner
        self.transferred = False
        self.released = False

    def release(self):
        with self.owner.lock:
            if not self.released:
                self.owner.active -= 1
                self.released = True


class Admission:
    def __init__(self, concurrent=2, per_minute=6, daily_jobs=100):
        self.concurrent = concurrent
        self.per_minute = per_minute
        self.daily_jobs = daily_jobs
        self.active = 0
        self.clients = {}
        self.day = None
        self.jobs = 0
        self.lock = threading.Lock()

    def acquire(self, ip):
        now = time.monotonic()
        day = dt.datetime.now(dt.timezone.utc).date()
        with self.lock:
            if day != self.day:
                self.day, self.jobs = day, 0
            self.clients = {k: v for k, v in self.clients.items()
                            if v and now - v[-1] < 60}
            history = self.clients.get(ip, deque())
            while history and now - history[0] >= 60:
                history.popleft()
            if (self.active >= self.concurrent or len(history) >= self.per_minute
                    or self.jobs >= self.daily_jobs or len(self.clients) >= 4096):
                raise LimitError("admission_limit")
            history.append(now)
            self.clients[ip] = history
            self.active += 1
            self.jobs += 1
            return Lease(self)


ADMISSION = Admission()
MAX_TASKS = 16


class AdmissionMiddleware:
    """Bound bodies before JSON parsing; never trust visitor forwarding headers."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        protected = ((scope.get("method"), scope.get("path")) in {
            ("POST", "/api/run"), ("POST", "/api/suite"), ("GET", "/api/selftest")})
        if scope["type"] != "http" or not protected:
            return await self.app(scope, receive, send)
        peer = (scope.get("client") or ("unknown",))[0]
        # Deployed uvicorn disables proxy headers. Only local cloudflared may
        # assert CF-Connecting-IP; X-Forwarded-For is deliberately ignored.
        if os.environ.get("ATTEST_TRUST_LOCAL_TUNNEL") == "1" and peer in ("127.0.0.1", "::1"):
            headers = dict(scope.get("headers", []))
            import ipaddress
            try:
                peer = str(ipaddress.ip_address(headers.get(b"cf-connecting-ip", b"").decode()))
            except ValueError:
                pass
        try:
            lease = ADMISSION.acquire(peer)
        except LimitError:
            return await JSONResponse({"error": "admission_limit", "status": 429},
                                      status_code=429, headers={"Retry-After": "60"})(scope, receive, send)
        scope.setdefault("state", {})["admission_lease"] = lease
        try:
            body = bytearray()
            deadline = time.monotonic() + 10
            while True:
                try:
                    message = await asyncio.wait_for(receive(), max(0.001, deadline - time.monotonic()))
                except asyncio.TimeoutError:
                    return await JSONResponse({"error": "request_timeout"}, status_code=408)(scope, receive, send)
                if message["type"] == "http.disconnect":
                    return
                body.extend(message.get("body", b""))
                if len(body) > 32768:
                    return await JSONResponse({"error": "request_too_large"}, status_code=413)(scope, receive, send)
                if not message.get("more_body"):
                    break

            delivered = False

            async def replay():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()

            await self.app(scope, replay, send)
        finally:
            if not lease.transferred:
                lease.release()
