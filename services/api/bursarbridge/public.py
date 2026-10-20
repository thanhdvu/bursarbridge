"""Bounded per-browser synthetic sandboxes; no IP-based identity or shared Reset."""

import asyncio
import hashlib
import hmac
import ipaddress
import logging
import os
import re
import secrets
import shutil
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

from .availability import Budget, HostedGate
from .chain import Chain
from .providers import Provider
from .security import digest
from .settings import load_settings

COOKIE = "bb_sandbox"
LIFETIME = 2**40  # A sandbox generation's state caps do not reset at midnight or Reset.
BOOTSTRAP_PATH = {
    "/api/public/bootstrap": {
        "get": {
            "summary": "Public mode only: establish a stateless browser cookie; sandbox starts at persona login",
            "responses": {
                "303": {"description": "Secure HttpOnly sandbox cookie and same-origin redirect"},
                "429": {"description": "HTTP burst rate limited; HTML retry page or API JSON"},
            },
        }
    }
}


def visitor_ip(request, proxy_secret):
    """An authenticated Pages hop may replace only the rate-limit IP."""
    fallback = request.client.host if request.client else "unknown"
    secrets_sent = request.headers.getlist("x-bb-proxy-secret")
    addresses = request.headers.getlist("x-bb-client-ip")
    if (
        not proxy_secret
        or len(secrets_sent) != 1
        or not hmac.compare_digest(secrets_sent[0].encode(), proxy_secret.encode())
        or len(addresses) != 1
    ):
        return fallback
    try:
        # Exactly one IP literal, never a forwarding chain, CIDR, zone or port.
        if "%" in addresses[0]:
            return fallback
        address = ipaddress.ip_address(addresses[0])
    except ValueError:
        return fallback
    return str(getattr(address, "ipv4_mapped", None) or address)


class PublicDemo:
    def __init__(self, directory, chain, provider):
        self.root = Path(directory).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        key = self.root / "cookie.key"
        if not key.exists():
            with key.open("xb") as out:
                out.write(secrets.token_bytes(32))
            key.chmod(0o600)
        self.key = key.read_bytes()
        self.chain, self.provider = chain, provider
        self.proxy_secret = os.getenv("PUBLIC_PROXY_SECRET", "")
        self.budget = Budget(self.root / "admission.db")
        self.provider.gate = HostedGate(
            self.budget,
            int(os.getenv("PUBLIC_LLM_DAILY_CALLS", "500")),
            int(os.getenv("PUBLIC_LLM_HOURLY_CALLS", "100")),
        )
        self.apps, self.active = {}, {}
        self.lock = threading.RLock()
        self.jobs = threading.BoundedSemaphore(1)
        self.streams = threading.BoundedSemaphore(100)
        self.agents = threading.BoundedSemaphore(8)
        self.max_sandboxes = int(os.getenv("PUBLIC_MAX_SANDBOXES", "128"))
        self.ttl = int(os.getenv("PUBLIC_SANDBOX_IDLE_HOURS", "6")) * 3600
        self.protected_seconds = max(300, int(os.getenv("PUBLIC_SANDBOX_PROTECT_MINUTES", "5")) * 60)
        self.last_sweep = 0

    def signature(self, ref):
        return hmac.new(self.key, ref.encode(), hashlib.sha256).hexdigest()

    def identify(self, value):
        if not value or not re.fullmatch(r"[a-f0-9]{32}\.[a-f0-9]{64}", value):
            return None
        ref, signature = value.split(".")
        if not hmac.compare_digest(signature, self.signature(ref)):
            return None
        return ref

    def sweep(self):
        with self.lock:
            now = time.time()
            if now - self.last_sweep < 60:
                return
            self.last_sweep = now
            for path in self.root.iterdir():
                if not path.is_dir() or not re.fullmatch(r"[a-f0-9]{32}", path.name):
                    continue
                if now - path.stat().st_mtime <= max(self.ttl, self.protected_seconds) or self.active.get(path.name, 0):
                    continue
                self.retire(path)

    def retire(self, path):
        # Caller holds lock; only manager-owned directories and no in-flight request.
        if path.resolve().parent != self.root or not re.fullmatch(r"[a-f0-9]{32}", path.name):
            raise RuntimeError("Unsafe sandbox cleanup path")
        if self.active.get(path.name, 0):
            raise RuntimeError("Cannot retire an active sandbox")
        app = self.apps.pop(path.name, None)
        if app:
            app.state.store.engine.dispose()
        shutil.rmtree(path)

    def allocate(self, ip, ref=None):
        self.sweep()
        with self.lock:
            if ref and (self.root / ref).is_dir():
                return ref, None
            paths = [p for p in self.root.iterdir() if p.is_dir() and re.fullmatch(r"[a-f0-9]{32}", p.name)]
            idle = sorted(
                (p for p in paths if not self.active.get(p.name, 0)
                 and time.time() - p.stat().st_mtime > self.protected_seconds),
                key=lambda p: p.stat().st_mtime,
            )
            needed = max(0, len(paths) - self.max_sandboxes + 1)
            if needed > len(idle):
                return None, "SANDBOX_CAPACITY"
            if not self.budget.take([
                ("new-burst:" + ip, int(os.getenv("PUBLIC_NEW_PER_IP_MINUTE", "10")), 60),
                ("new:" + ip, int(os.getenv("PUBLIC_NEW_PER_IP_HOUR", "120")), 3600),
                ("new-global", int(os.getenv("PUBLIC_NEW_GLOBAL_HOUR", "500")), 3600),
                ("new-global-day", int(os.getenv("PUBLIC_NEW_GLOBAL_DAY", "2000")), 86400),
            ]):
                return None, "SANDBOX_RATE_LIMITED"
            for path in idle[:needed]:
                self.retire(path)
            ref = ref or secrets.token_hex(16)
            (self.root / ref).mkdir(mode=0o700)
            return ref, None

    def child(self, ref):
        from .main import create_app

        with self.lock:
            if ref not in self.apps:
                path = self.root / ref
                self.apps[ref] = create_app(
                    "sqlite:///" + (path / "state.db").as_posix(),
                    path,
                    True,
                    self.chain,
                    self.provider,
                    public_mode=True,
                )
                self.apps[ref].openapi()["paths"].update(BOOTSTRAP_PATH)
            return self.apps[ref]

    def maintain(self):
        self.sweep()
        with self.lock:
            refs = list(self.apps)
        for ref in refs:
            with self.lock:
                child = self.apps.get(ref)
                if not child:
                    continue
                self.active[ref] = self.active.get(ref, 0) + 1
            try:
                child.state.anchor_due()
            except Exception:
                logging.getLogger("bursarbridge.public").warning(
                    "public_maintenance_failed; sandbox retained; no raw exception data logged"
                )
            finally:
                with self.lock:
                    self.active[ref] -= 1
                    if not self.active[ref]:
                        self.active.pop(ref)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            if scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 1008})
            return
        request = Request(scope)
        path = request.url.path
        # Ordinary requests retain Uvicorn's trusted-loopback client resolution.
        # Pages may attest an IP with a separate secret; no other header is trusted.
        ip = digest(visitor_ip(request, self.proxy_secret))
        if not self.budget.take([("http:" + ip, 600, 60), ("http-global", 3000, 60)]):
            return await self.reject(scope, receive, send, 429, "RATE_LIMITED")
        if path == "/api/health":
            response = JSONResponse(
                {
                    "ok": True,
                    "demo": True,
                    "publicDemo": True,
                    "sandboxMode": "per_browser",
                    "llmProvider": self.provider.name,
                    "llm": self.provider.status(),
                    "chainMode": self.chain.mode,
                    "screeningMode": os.getenv("SCREENING_MODE", "watchman"),
                    "bank": "MOCK",
                    "bursar": "MOCK",
                }
            )
            response.headers["Cache-Control"] = "no-store"
            return await response(scope, receive, send)
        ref = self.identify(request.cookies.get(COOKIE))
        bootstrap = path == "/api/public/bootstrap" and request.method == "GET"
        session = path == "/api/session" and request.method == "POST"
        if bootstrap:
            ref = ref or secrets.token_hex(16)  # Signed cookie only; no disk/state allocation.
        elif session:
            ref, error = self.allocate(ip, ref)
            if error:
                return await self.reject(
                    scope, receive, send, 503 if error == "SANDBOX_CAPACITY" else 429, error
                )
        elif ref is None or not (self.root / ref).is_dir():
            return await self.reject(scope, receive, send, 401, "SANDBOX_REQUIRED")
        if request.method == "POST":
            rules = [
                ("writes-total:" + ref, 500, LIFETIME),
                ("writes:" + ref, 30, 60),
                ("writes-ip:" + ip, 90, 60),
                ("writes-global", 300, 60),
            ]
            if path in {"/api/demo/reset", "/api/chain/anchor"}:
                rules.append(("chain-control:" + ref, 3, 60))
            if path == "/api/documents":
                rules.append(("documents-total:" + ref, 30, LIFETIME))
            if path == "/api/agent/threads":
                rules.append(("threads-total:" + ref, 50, LIFETIME))
            if re.fullmatch(r"/api/agent/threads/[^/]+/messages", path):
                rules.append(("messages-total:" + ref, 200, LIFETIME))
            if not self.budget.take(rules):
                return await self.reject(scope, receive, send, 429, "SANDBOX_WRITE_LIMIT")
        if bootstrap:
            if (self.root / ref).is_dir():
                os.utime(self.root / ref, None)
            target = request.headers.get("x-bursar-return", "/")
            if (
                not target.startswith("/")
                or target.startswith("//")
                or "\\" in target
                or any(ord(c) < 32 for c in target)
            ):
                target = "/"
            response = RedirectResponse(target, status_code=303)
            response.set_cookie(
                COOKIE,
                ref + "." + self.signature(ref),
                max_age=self.ttl,
                secure=True,
                httponly=True,
                samesite="lax",
                path="/",
            )
            response.headers["Cache-Control"] = "no-store"
            return await response(scope, receive, send)
        agent = request.method == "POST" and re.fullmatch(r"/api/agent/threads/[^/]+/messages", path)
        document = request.method == "POST" and path == "/api/documents"
        if document and not self.budget.take([("document:" + ref, 10, 60), ("document-ip:" + ip, 30, 60)]):
            return await self.reject(scope, receive, send, 429, "DOCUMENT_RATE_LIMITED")
        runner = path == "/api/scenarios/run"
        stream = agent or path == "/api/events" or runner
        if agent and not self.budget.take(
            [
                ("agent:" + ref, int(os.getenv("PUBLIC_AGENT_PER_MINUTE", "3")), 60),
                ("agent:" + ref, int(os.getenv("PUBLIC_AGENT_PER_HOUR", "30")), 3600),
                ("agent-ip:" + ip, 30, 60),
            ]
        ):
            return await self.reject(scope, receive, send, 429, "AGENT_RATE_LIMITED")
        if runner and not self.budget.take([("runner:" + ref, 2, 3600), ("runner-ip:" + ip, 5, 3600)]):
            return await self.reject(scope, receive, send, 429, "SCENARIO_RATE_LIMITED")
        acquired = []
        for semaphore in (
            ([self.jobs] if runner else [])
            + ([self.streams] if stream else [])
            + ([self.agents] if agent else [])
        ):
            if not semaphore.acquire(blocking=False):
                for slot in acquired:
                    slot.release()
                return await self.reject(scope, receive, send, 429, "DEMO_BUSY")
            acquired.append(semaphore)
        with self.lock:
            if self.active.get(ref, 0) >= 12:
                for slot in acquired:
                    slot.release()
                return await self.reject(scope, receive, send, 429, "VISITOR_BUSY")
            self.active[ref] = self.active.get(ref, 0) + 1
            os.utime(self.root / ref, None)

        async def outgoing(message):
            if message["type"] == "http.response.start":
                from http.cookies import SimpleCookie

                cookie = SimpleCookie()
                cookie[COOKIE] = ref + "." + self.signature(ref)
                (
                    cookie[COOKIE]["path"],
                    cookie[COOKIE]["secure"],
                    cookie[COOKIE]["httponly"],
                    cookie[COOKIE]["samesite"],
                ) = "/", True, True, "Lax"
                cookie[COOKIE]["max-age"] = self.ttl
                message.setdefault("headers", []).append(
                    (b"set-cookie", cookie.output(header="").strip().encode())
                )
            await send(message)

        try:
            child = await asyncio.to_thread(self.child, ref)
            await child(scope, receive, outgoing)
        finally:
            with self.lock:
                os.utime(self.root / ref, None)
                self.active[ref] -= 1
                if not self.active[ref]:
                    self.active.pop(ref)
            for slot in acquired:
                slot.release()

    async def reject(self, scope, receive, send, status, code):
        if "text/html" in Request(scope).headers.get("accept", ""):
            await HTMLResponse(
                "<!doctype html><html lang='en'><meta charset='utf-8'>"
                "<meta name='viewport' content='width=device-width, initial-scale=1'>"
                "<title>BursarBridge — please retry</title><main style='max-width:32rem;"
                "margin:15vh auto;padding:1.5rem;font:18px/1.6 system-ui'>"
                "<h1>A busy moment</h1><p>The demo is welcoming other visitors. "
                "Please wait a minute, then try again.</p>"
                "<button onclick='location.reload()' style='font:inherit;padding:.6rem 1rem'>"
                "Try again</button><p><a href='/'>Return to BursarBridge</a></p></main></html>",
                status_code=status,
                headers={"Retry-After": "60", "Cache-Control": "no-store"},
            )(scope, receive, send)
            return
        await JSONResponse(
            {
                "error": {
                    "code": code,
                    "message": "Demo capacity reached; please retry shortly"
                    if status != 401
                    else "Open the demo to start a private sandbox",
                    "details": {},
                }
            },
            status_code=status,
            headers={"Retry-After": "60", "Cache-Control": "no-store"},
        )(scope, receive, send)


def create_public_app(directory=None, chain=None, provider=None):
    load_settings()
    provider = provider or Provider()
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    local_test_proxy = (
        os.getenv("PUBLIC_LOCAL_PROXY", "0") == "1"
        and base_url.rstrip("/") == "http://127.0.0.1:8318/v1"
    )
    if provider.name == "openai" and not base_url.startswith("https://") and not local_test_proxy:
        raise ValueError("Public demo requires a dedicated HTTPS provider or the explicit 8318 local-test opt-in")
    manager = PublicDemo(
        directory or os.getenv("PUBLIC_DATA_DIR", "runtime/public"), chain or Chain(), provider
    )

    @asynccontextmanager
    async def lifespan(app):
        async def tick():
            while True:
                await asyncio.sleep(5)
                worker = asyncio.create_task(asyncio.to_thread(manager.maintain))
                try:
                    await asyncio.shield(worker)
                except asyncio.CancelledError:
                    await worker
                    raise

        task = asyncio.create_task(tick())
        try:
            yield
        finally:
            task.cancel()
            from contextlib import suppress

            with suppress(asyncio.CancelledError):
                await task
            for child in manager.apps.values():
                child.state.store.engine.dispose()

    app = Starlette(lifespan=lifespan)
    app.state.manager = manager
    app.mount("/", manager)
    return app
