"""Safe provider diagnostics and durable public-demo admission budgets."""

import json
import logging
import sqlite3
import threading
import time
from contextlib import closing
from datetime import datetime, timezone

import httpx

LOG = logging.getLogger("bursarbridge.provider")


class AdmissionError(Exception):
    def __init__(self, code):
        self.code = code


def error_info(exc, provider, phase):
    status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
    code = (
        exc.code
        if isinstance(exc, AdmissionError)
        else "rate_limited"
        if status == 429
        else "authentication_failed"
        if status in {401, 403}
        else "provider_unavailable"
        if status and status >= 500
        else "provider_rejected"
        if status
        else "timeout"
        if isinstance(exc, httpx.TimeoutException)
        else "connection_error"
        if isinstance(exc, httpx.HTTPError)
        else "invalid_output"
    )
    result = {
        "provider": provider,
        "phase": phase,
        "code": code,
        "httpStatus": status,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    if isinstance(exc, httpx.HTTPStatusError):
        retry = exc.response.headers.get("retry-after", "")
        if retry.isdigit():
            result["retryAfterSeconds"] = min(int(retry), 86400)
    return result


class Budget:
    """Fixed windows survive restarts. All keys are server-derived, not forwarded headers."""

    def __init__(self, path):
        self.path = str(path)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS budgets (key TEXT, window INTEGER, period INTEGER, count INTEGER, PRIMARY KEY(key, window, period))"
            )
            db.execute("CREATE INDEX IF NOT EXISTS budget_expiry ON budgets(window + period)")
            db.execute("CREATE TABLE IF NOT EXISTS provider_health (id INTEGER PRIMARY KEY, error TEXT)")

    def provider_error(self, value=...):
        with closing(sqlite3.connect(self.path, timeout=5)) as db, db:
            if value is not ...:
                db.execute(
                    "INSERT OR REPLACE INTO provider_health VALUES (1, ?)",
                    (json.dumps(value) if value else None,),
                )
            row = db.execute("SELECT error FROM provider_health WHERE id=1").fetchone()
            return json.loads(row[0]) if row and row[0] else None

    def take(self, rules):
        now = int(time.time())
        with closing(sqlite3.connect(self.path, timeout=5)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM budgets WHERE window + period < ?", (now - 86400,))
            for key, limit, period in rules:
                window = now // period * period
                row = db.execute(
                    "SELECT count FROM budgets WHERE key=? AND window=? AND period=?", (key, window, period)
                ).fetchone()
                if (row[0] if row else 0) >= limit:
                    return False
            for key, limit, period in rules:
                window = now // period * period
                db.execute(
                    "INSERT INTO budgets VALUES (?, ?, ?, 1) ON CONFLICT(key,window,period) DO UPDATE SET count=count+1",
                    (key, window, period),
                )
        return True


class HostedGate:
    def __init__(self, budget, daily=500, hourly=100, concurrent=2):
        self.budget, self.daily, self.hourly = budget, daily, hourly
        self.slots = threading.BoundedSemaphore(concurrent)
        self.cooldown_until = 0
        persisted = self.budget.provider_error()
        if persisted and persisted.get("retryAfterSeconds") and persisted.get("at"):
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(persisted["at"])).total_seconds()
            self.cooldown_until = time.monotonic() + max(0, persisted["retryAfterSeconds"] - age)

    def enter(self):
        if time.monotonic() < self.cooldown_until:
            raise AdmissionError("provider_cooldown")
        if not self.slots.acquire(blocking=False):
            raise AdmissionError("provider_busy")
        try:
            accepted = self.budget.take([("llm", self.daily, 86400), ("llm", self.hourly, 3600)])
        except Exception:
            self.slots.release()
            raise
        if not accepted:
            self.slots.release()
            raise AdmissionError("hosted_budget_exhausted")

    def leave(self):
        self.slots.release()

    def failed(self, exc, info=None):
        if not isinstance(exc, AdmissionError):
            self.cooldown_until = time.monotonic() + max(60, (info or {}).get("retryAfterSeconds", 0))
        if info:
            self.budget.provider_error(info)
