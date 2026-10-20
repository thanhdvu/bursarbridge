"""FastAPI transport; role and family checks precede every domain operation."""

import asyncio
import copy
import json
import logging
import os
import queue
import secrets
import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import agent, auth
from . import models as m
from .availability import error_info
from .chain import Chain
from .conversation import Proposal, dialogue_locale
from .engine import (
    DomainError,
    advance,
    audit,
    bank_execute,
    cancel,
    create_mandate,
    dt,
    event,
    execute_rent,
    family_rows,
    file_refund,
    freeze_family,
    frozen_reason,
    mandate_valid,
    owned,
    parent,
    parse_document,
    public,
    quote,
    refund_view,
    require,
    restore_frozen_mandates,
    seed,
    uid,
    verified_invoice,
)
from .localization import localize
from .providers import Provider
from .screening import Screening
from .security import Issuer, canonical, digest
from .settings import load_settings
from .store import Store, verify
from .study import rent_setup, study_plan


def sse(events):
    for data in events:
        yield "event: " + data.get("type", "message") + "\ndata: " + canonical(data) + "\n\n"


def create_app(database_url=None, data_dir=None, demo=None, chain=None, provider=None, public_mode=None):
    load_settings()
    if public_mode is None and database_url is None and os.getenv("PUBLIC_DEMO", "0") == "1":
        from .public import create_public_app

        return create_public_app(directory=data_dir, chain=chain, provider=provider)
    public_mode = bool(public_mode)
    demo = os.getenv("DEMO", "0") == "1" if demo is None else demo
    directory = Path(data_dir or os.getenv("DATA_DIR", "runtime"))
    store = Store(database_url or os.getenv("DATABASE_URL", "sqlite:///./bursarbridge.db"), directory)
    issuer = Issuer(directory / "issuer.key")
    provider = provider or Provider()
    chain = chain or Chain()
    issuer.chain = chain
    issuer.screening = Screening()
    legacy_rp = os.getenv("WEBAUTHN_RP_ID", "localhost")
    origin = [
        v.strip()
        for v in os.getenv("WEBAUTHN_ORIGIN", "http://localhost:3000,http://localhost:3700").split(",")
        if v.strip()
    ]
    parties = auth.relying_parties(origin)
    with store.transaction() as s:
        if not s:
            seed(s, issuer)
            chain.register(s)
        # Preserve pre-multi-origin credentials only for their original RP. New
        # registrations are stored per RP and cannot overwrite another domain.
        for key, record in s["authenticators"].items():
            if key in {user["id"] for user in s["users"].values()}:
                record.setdefault("rpId", legacy_rp)
        for family, frozen in s["frozen"].items():
            if frozen and (
                family not in s.get("frozenReasons", {})
                or any(
                    p["_family"] == family and p["status"] == "sent" and dt(s["now"]) < dt(p["_cancelUntil"])
                    for p in s["payments"].values()
                )
            ):
                freeze_family(s, family, "system", s.get("frozenReasons", {}).get(family, "LEGACY_FREEZE"))

    anchor_retry = {"after": 0.0, "attempts": 0}

    anchor_worker = threading.Lock()

    def anchor_due():
        # Chain I/O never holds the ledger lock: Reset and conversation stay responsive.
        if time.monotonic() < anchor_retry["after"] or not anchor_worker.acquire(blocking=False):
            return
        resumed = set()
        try:
            with store.transaction() as state:
                snapshot = copy.deepcopy(state)
                generation = state.get("_generation")
            registration = bool(snapshot.get("registrationPending"))
            last = (
                snapshot["anchors"][-1]
                if snapshot["anchors"]
                else {"lastSeq": 0, "at": snapshot["audit"][0]["at"]}
            )
            count = len(snapshot["audit"]) - last["lastSeq"]
            due = (
                registration
                or snapshot.get("anchorDeferred")
                or snapshot.get("chainRetryPending")
                or count >= 20
                or count
                and (dt(snapshot["now"]) - dt(last["at"])).total_seconds() >= 300
            )
            if not due:
                return
            try:
                if registration:
                    chain.register(snapshot)
                anchor = chain.anchor(snapshot)
            except Exception as exc:
                anchor_retry["attempts"] += 1
                anchor_retry["after"] = time.monotonic() + min(
                    60, 5 * 2 ** min(anchor_retry["attempts"] - 1, 4)
                )
                code = exc.code if isinstance(exc, DomainError) else "ANCHOR_ERROR"
                with store.transaction() as state:
                    if state.get("_generation") != generation:
                        return  # A reset retired this generation while its receipt was pending.
                    if not state.get("anchorDeferred"):
                        logging.getLogger("bursarbridge.chain").warning("anchor_retry code=%s", code)
                        state["anchorDeferred"] = True
                        audit(
                            state,
                            "system",
                            "anchor_deferred",
                            "Registry or anchoring will retry automatically; no family freeze",
                            code=code,
                        )
                        for family in {u["familyId"] for u in state["users"].values()}:
                            event(
                                state,
                                family,
                                "anchor_updated",
                                {"status": "retrying", "code": code, "recovery": "automatic_retry"},
                            )
                return
            with store.transaction() as state:
                if state.get("_generation") != generation:
                    return
                # Only commit a receipt for the exact prefix sent, never a replaced generation.
                if anchor and (
                    state["anchors"] != snapshot["anchors"][:-1]
                    or len(state["audit"]) < anchor["lastSeq"]
                    or state["audit"][anchor["lastSeq"] - 1]["hash"]
                    != snapshot["audit"][anchor["lastSeq"] - 1]["hash"]
                ):
                    return
                if registration:
                    for family, cred in snapshot["credentials"].items():
                        if state["credentials"][family]["hash"] == cred["hash"] and cred.get("chainTx"):
                            state["credentials"][family]["chainTx"] = cred["chainTx"]
                    state.pop("registrationPending", None)
                if anchor:
                    state["anchors"].append(anchor)
                deferred = state.pop("anchorDeferred", False)
                pending = state.pop("chainRetryPending", False)
                anchor_retry.update(after=0.0, attempts=0)
                if deferred or pending or registration:
                    audit(
                        state,
                        "system",
                        "anchor_recovered",
                        "Pending registry and audit commitments recovered",
                    )
                    for family in {u["familyId"] for u in state["users"].values()}:
                        event(
                            state,
                            family,
                            "anchor_updated",
                            {"status": "ready", "registrationStatus": "ready", "recovery": None},
                        )
                        resumed.add(family)
        finally:
            anchor_worker.release()
        for family in resumed:
            continue_after_commit(family)

    @asynccontextmanager
    async def lifespan(app):
        async def tick():
            while True:
                await asyncio.sleep(1)
                await asyncio.to_thread(anchor_due)

        task = asyncio.create_task(tick())
        yield
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    app = FastAPI(
        title="BursarBridge API",
        version="0.1.0",
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        lifespan=lifespan,
    )
    app.state.anchor_due = anchor_due
    app.state.store, app.state.issuer, app.state.chain = store, issuer, chain
    app.state.demo = demo
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origin,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "Last-Event-ID"],
    )
    buckets = defaultdict(deque)
    dialogue_locks = defaultdict(threading.Lock)

    def resume_pending(family):
        """Resume recorded intent, never document instructions or a new model decision."""
        with store.transaction() as s:
            refs = [
                t["threadId"]
                for t in s["threads"].values()
                if t["_family"] == family and t.get("_pendingIntent") in {"pay", "rent"}
            ]
        for ref in refs:
            with dialogue_locks[ref], store.transaction() as s:
                thread = s["threads"][ref]
                if thread.get("_pendingIntent") not in {"pay", "rent"} or s["frozen"].get(family):
                    continue
                if (dt(s["now"]) - dt(thread.get("_pendingAt", s["now"]))).total_seconds() >= 86400:
                    thread["_pendingIntent"] = None
                    continue
                user = next(u for u in s["users"].values() if u["id"] == thread["_owner"])
                pending = thread["_pendingIntent"]
                if pending == "rent":
                    if rent_setup(s, user)["missing"]:
                        continue
                else:
                    if not any(
                        mandate_valid(s, row) and row["_family"] == family and row["purpose"] == "tuition"
                        for row in s["mandates"].values()
                    ):
                        continue
                    from .engine import pack

                    if any(d["status"] == "missing" for d in pack(s, family)["documents"]):
                        continue
                    if study_plan(s, user, issuer)["paymentWindowStatus"] not in {
                        "open",
                        "legacy_unspecified",
                    }:
                        continue
                if not chain.available():
                    continue
                body = m.MessageIn(text="", locale=thread.get("_locale", user["locale"]))
                before = len(thread["messages"])
                agent.run(
                    s,
                    user,
                    thread,
                    body,
                    issuer,
                    Provider("scripted"),
                    prepared_plan=Proposal(
                        intent=pending, scope=thread.get("_scope", "remaining"), needsClarification=False
                    ),
                )
                del thread["messages"][before]  # System continuation, not a fabricated user message.
                thread["_autoResumed"] = thread["_lastFacts"]["outcome"] == "approval"
                message = thread["messages"][-1]
                audit(
                    s,
                    "agent",
                    "pending_request_resumed",
                    "Recorded purpose-specific request resumed after prerequisites",
                    reference=ref,
                )
                event(s, family, "thread_updated", {"threadId": ref, "messageId": message["id"]})

    def continue_after_commit(family):
        # A failed continuation cannot turn an already committed upload/signature
        # into a failed HTTP operation. Its transaction rolls back independently.
        try:
            resume_pending(family)
        except Exception as exc:
            with store.transaction() as s:
                audit(
                    s,
                    "agent",
                    "pending_resume_deferred",
                    "Continuation unavailable; request remains pending",
                    code=exc.code if isinstance(exc, DomainError) else "INTERNAL_ERROR",
                )

    @app.middleware("http")
    async def limits(request, call_next):
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        bucket = buckets[key]
        while bucket and bucket[0] < now - 60:
            bucket.popleft()
        if len(bucket) > 600:
            return JSONResponse(
                {"error": {"code": "RATE_LIMITED", "message": "Try again later", "details": {}}},
                status_code=429,
            )
        bucket.append(now)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(DomainError)
    async def domain_error(request, exc):
        return JSONResponse(
            {"error": {"code": exc.code, "message": exc.message, "ruleId": exc.rule, "details": {}}},
            status_code=exc.status,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request does not match schema",
                    "details": {"fields": [".".join(str(p) for p in e["loc"]) for e in exc.errors()]},
                }
            },
            status_code=422,
        )

    bearer = HTTPBearer(auto_error=False)

    def user_id(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        authorization = "Bearer " + credentials.credentials if credentials else ""
        require(authorization.startswith("Bearer "), "UNAUTHENTICATED", "Bearer session required", 401)
        with store.transaction() as s:
            user_key = s["sessions"].get(digest(authorization[7:]))
            require(user_key in s["users"], "UNAUTHENTICATED", "Invalid session", 401)
            return user_key

    def judge(user):
        require(user["role"] == "judge", "ROLE_REQUIRED", "Judge role required")

    def demo_only():
        require(demo, "DEMO_DISABLED", "Demo control disabled", 403)

    @app.get("/api/health")
    def health():
        return {
            "ok": True,
            "demo": demo,
            "bank": "MOCK",
            "bursar": "MOCK",
            "llmProvider": provider.name,
            "chainMode": chain.mode,
            "screeningMode": issuer.screening.mode,
            "llm": provider.status(),
            "publicDemo": public_mode,
        }

    @app.post("/api/session", response_model=m.SessionOut)
    def session(body: m.SessionIn):
        demo_only()
        token = secrets.token_urlsafe(32)
        with store.transaction() as s:
            s["sessions"][digest(token)] = body.persona
            return {
                "token": token,
                "user": {
                    **s["users"][body.persona],
                    "admissionDisposition": s.get("admissionDispositions", {}).get(
                        s["users"][body.persona]["familyId"]
                    ),
                    "simulatedNow": s["now"],
                    "frozen": s["frozen"].get(s["users"][body.persona]["familyId"], False),
                    "frozenReason": frozen_reason(s, s["users"][body.persona]["familyId"]),
                },
            }

    @app.get("/api/me", response_model=m.User)
    def me(key=Depends(user_id)):
        with store.transaction() as s:
            family = s["users"][key]["familyId"]
            return {
                **s["users"][key],
                "simulatedNow": s["now"],
                "frozen": s["frozen"].get(family, False),
                "frozenReason": frozen_reason(s, family),
                "admissionDisposition": s.get("admissionDispositions", {}).get(family),
            }

    @app.post("/api/demo/reset", response_model=m.ResetOut)
    def reset(key=Depends(user_id)):
        demo_only()
        with store.lock:
            with store.transaction() as s:
                judge(s["users"][key])
                seed(s, issuer)
                s["registrationPending"] = chain.mode == "fisco"
                s["anchorDeferred"] = True
                audit(
                    s,
                    "system",
                    "reset_chain_pending",
                    "Sandbox reset locally; registry and audit commitments queued for background retry",
                )
                for family in {u["familyId"] for u in s["users"].values()}:
                    event(
                        s,
                        family,
                        "anchor_updated",
                        {
                            "status": "pending",
                            "registrationStatus": "pending" if s["registrationPending"] else "ready",
                            "recovery": "automatic_retry",
                        },
                    )
                anchor_retry.update(after=0.0, attempts=0)
                store.reset_mirrors()
            # A reset changes the generation and invalidates all old sessions.
            with store.transaction() as s:
                store.audit_file.write_text(
                    "".join(canonical(e) + "\n" for e in s["audit"]), encoding="utf-8"
                )
        return {
            "ok": True,
            "registrationStatus": "pending" if chain.mode == "fisco" else "ready",
            "anchorStatus": "pending",
            "recovery": "automatic_retry",
        }

    @app.get("/api/study-plan", response_model=m.StudyPlan)
    def study(locale: str = "en", key=Depends(user_id)):
        with store.transaction() as s:
            require(s["users"][key]["role"] != "judge", "ROLE_REQUIRED", "Family required", 403)
            return localize(study_plan(s, s["users"][key], issuer), locale)

    @app.get("/api/rent", response_model=m.RentSetup)
    def rent(locale: str = "en", key=Depends(user_id)):
        with store.transaction() as s:
            require(s["users"][key]["role"] != "judge", "ROLE_REQUIRED", "Family required", 403)
            return localize(rent_setup(s, s["users"][key]), locale)

    @app.get(
        "/api/study-plan/standard-admission-certificate.pdf",
        response_class=Response,
        responses={200: {"content": {"application/pdf": {}}}},
    )
    def standard_certificate(key=Depends(user_id)):
        from .fixtures import render

        with store.transaction() as s:
            row = study_plan(s, s["users"][key], issuer)["standardAdmissionCertificate"]
            require(
                row["status"] == "issued_MOCK",
                "CERTIFICATE_UNAVAILABLE",
                "No acceptance certificate is recorded in these signed terms",
                409,
            )
            return Response(
                render(
                    "Standard admission certificate",
                    [
                        "Hanbit University (MOCK) / SYNTHETIC",
                        "Issued following acceptance: " + row["issuedAt"],
                        "Certificate precedes the D-2 application and tuition payment window.",
                        "Spring 2027 degree programme; D-2 application sequence illustration.",
                        "No embassy submission or real admission is represented.",
                    ],
                ),
                media_type="application/pdf",
            )

    @app.get(
        "/api/approvals/{ref}/letter.pdf",
        response_class=Response,
        responses={200: {"content": {"application/pdf": {}}}},
    )
    def escalation_letter(ref: str, key=Depends(user_id)):
        from .escalations import letter_lines
        from .fixtures import render

        with store.transaction() as s:
            approval = owned(s, "approvals", ref, s["users"][key])
            require(approval["action"] == "escalation_letter", "INVALID_ACTION", "Not correspondence", 409)
            refund = owned(s, "refunds", approval["rawAction"]["refundId"], s["users"][key])
            return Response(
                render("Refund escalation", letter_lines(refund, approval)), media_type="application/pdf"
            )

    @app.get(
        "/api/refunds/{ref}/complaint-pack.pdf",
        response_class=Response,
        responses={200: {"content": {"application/pdf": {}}}},
    )
    def complaint_pack(ref: str, key=Depends(user_id)):
        from .escalations import letter_lines
        from .fixtures import render

        with store.transaction() as s:
            refund = owned(s, "refunds", ref, s["users"][key])
            require(
                refund.get("followUp", {}).get("complaintPack"),
                "PACK_NOT_READY",
                "No stalled chaser yet",
                409,
            )
            return Response(
                render("Refund complaint pack", letter_lines(refund)), media_type="application/pdf"
            )

    @app.get("/api/clock")
    def clock(key=Depends(user_id)):
        with store.transaction() as s:
            return {"now": s["now"], "simulated": True}

    @app.post("/api/clock/advance")
    def clock_advance(body: m.ClockIn, key=Depends(user_id)):
        demo_only()
        if public_mode:
            require(
                body.days * 24 + body.hours <= 31 * 24,
                "PUBLIC_CLOCK_LIMIT",
                "Advance at most 31 simulated days per public request",
                422,
            )
        with store.transaction() as s:
            judge(s["users"][key])
            advance(s, body.days, body.hours)
            for user in s["users"].values():
                if user["role"] == "parent" and not s["frozen"].get(user["familyId"]):
                    if any(
                        row["purpose"] == "rent"
                        and row["_family"] == user["familyId"]
                        and mandate_valid(s, row)
                        for row in s["mandates"].values()
                    ):
                        if not rent_setup(s, user)["missing"]:
                            execute_rent(s, user, issuer)
            return {"now": s["now"]}

    @app.post("/api/webauthn/register/options")
    def register_options(request: Request, key=Depends(user_id)):
        rp, selected_origin = auth.request_party(request, parties)
        with store.transaction() as s:
            return auth.register_options(s, s["users"][key], rp, selected_origin)

    @app.post("/api/webauthn/register/verify")
    def register_verify(body: m.CredentialIn, request: Request, key=Depends(user_id)):
        rp, selected_origin = auth.request_party(request, parties)
        with store.transaction() as s:
            return auth.register_verify(s, s["users"][key], body.credential, demo, rp, selected_origin)

    @app.post("/api/webauthn/assert/options")
    def assert_options(body: m.AssertionOptions, request: Request, key=Depends(user_id)):
        rp, selected_origin = auth.request_party(request, parties)
        with store.transaction() as s:
            return auth.assertion_options(s, s["users"][key], body.refId, body.purpose, rp, selected_origin)

    @app.post("/api/webauthn/assert/verify")
    def assert_verify(body: m.AssertionVerify, request: Request, key=Depends(user_id)):
        rp, selected_origin = auth.request_party(request, parties)
        with store.transaction() as s:
            return auth.assertion_verify(
                s, s["users"][key], body.refId, body.credential, demo, rp, selected_origin
            )

    @app.get("/api/mandates", response_model=list[m.Mandate])
    def mandates(key=Depends(user_id)):
        with store.transaction() as s:
            return family_rows(s, "mandates", s["users"][key])

    @app.post("/api/mandates", response_model=m.Mandate)
    def mandate_create(body: m.MandateIn, key=Depends(user_id)):
        with store.transaction() as s:
            return public(create_mandate(s, s["users"][key], body.model_dump()))

    @app.post("/api/mandates/{ref}/sign", response_model=m.Mandate)
    def mandate_sign(ref: str, body: m.SignIn, request: Request, key=Depends(user_id)):
        rp, selected_origin = auth.request_party(request, parties)
        with store.transaction() as s:
            user = s["users"][key]
            parent(user)
            row = owned(s, "mandates", ref, user)
            require(not s["frozen"].get(user["familyId"]))
            require(
                row["status"] == "pending_signature" and row["_owner"] == user["id"],
                "INVALID_STATE",
                "Cannot sign mandate",
                409,
            )
            auth.consume(s, user, ref, body.assertion, row["hash"], demo, rp, selected_origin)
            require(chain.available(), "CHAIN_UNAVAILABLE", "Writes paused", 503)
            row["status"] = "active"
            audit(s, user["id"], "mandate_signed", "Mandate activated", mandateHash=row["hash"])
            anchor = chain.anchor(s)
            if anchor and anchor.get("txHash"):
                row["chainTx"] = {k: anchor[k] for k in ("txHash", "blockNumber")}
            result, family = public(row), user["familyId"]
        continue_after_commit(family)
        return result

    @app.post("/api/mandates/{ref}/revoke", response_model=m.Mandate)
    def mandate_revoke(ref: str, key=Depends(user_id)):
        with store.transaction() as s:
            user = s["users"][key]
            parent(user)
            row = owned(s, "mandates", ref, user)
            row["status"] = "revoked"
            audit(s, user["id"], "mandate_revoked", "Mandate revoked", mandateHash=row["hash"])
            return localize(public(row), user["locale"])

    @app.post("/api/documents", response_model=m.Document)
    async def document_upload(
        file: UploadFile = File(...), kind: str = Form("invoice"), key=Depends(user_id)
    ):
        require(
            kind in {"invoice", "admission", "refusal", "email", "rental_agreement"},
            "INVALID_KIND",
            "Invalid document kind",
            422,
        )
        content = await file.read(5 * 1024 * 1024 + 1)
        parsed_text = None
        if public_mode:
            from .pdf_worker import extract_public_text

            parsed_text = await asyncio.to_thread(extract_public_text, content)
        with store.transaction() as s:
            user = s["users"][key]
            result = public(
                parse_document(s, user, file.filename or "document", kind, content, parsed_text=parsed_text)
            )
            family = user["familyId"]
        if not result["warnings"]:
            await asyncio.to_thread(continue_after_commit, family)
        return result

    @app.get("/api/documents", response_model=list[m.Document])
    def document_list(key=Depends(user_id)):
        with store.transaction() as s:
            user = s["users"][key]
            return [
                public(d)
                for d in s["documents"].values()
                if d["_family"] == user["familyId"]
                and (user["role"] == "parent" or d["uploadedBy"] == user["id"])
            ]

    @app.get("/api/documents/{ref}", response_model=m.Document)
    def document_get(ref: str, key=Depends(user_id)):
        with store.transaction() as s:
            user = s["users"][key]
            row = owned(s, "documents", ref, user)
            require(
                user["role"] == "parent" or row["uploadedBy"] == user["id"],
                "NOT_FOUND",
                "Document not shared with this user",
                404,
            )
            return localize(public(row), user["locale"])

    @app.post("/api/agent/threads")
    def thread_create(key=Depends(user_id)):
        with store.transaction() as s:
            user = s["users"][key]
            require(user["role"] in {"student", "parent", "cosigner"})
            ref = uid("thr")
            s["threads"][ref] = {
                "threadId": ref,
                "messages": [],
                "_family": user["familyId"],
                "_owner": user["id"],
            }
            return {"threadId": ref}

    @app.get("/api/agent/threads/{ref}")
    def thread_get(ref: str, locale: str | None = None, key=Depends(user_id)):
        with store.transaction() as s:
            user = s["users"][key]
            thread = owned(s, "threads", ref, user)
            require(thread["_owner"] == user["id"], "NOT_FOUND", "Thread not found", 404)
            return localize(public(thread), locale or thread.get("_locale", user["locale"]))

    @app.post("/api/agent/threads/{ref}/messages")
    def message(ref: str, body: m.MessageIn, key=Depends(user_id)):
        with store.transaction() as s:
            user = s["users"][key]
            thread = owned(s, "threads", ref, user)
            require(thread["_owner"] == user["id"], "NOT_FOUND", "Thread not found", 404)
            body = body.model_copy(
                update={"locale": dialogue_locale(body.text, thread.get("_locale", body.locale))}
            )
            for document_id in body.documentIds:
                doc = owned(s, "documents", document_id, user)
                require(
                    user["role"] == "parent" or doc["uploadedBy"] == user["id"],
                    "NOT_FOUND",
                    "Document not shared",
                    404,
                )

        def stream():
            channel = queue.SimpleQueue()

            def work():
                try:
                    with dialogue_locks[ref]:
                        with store.transaction() as s:
                            user = s["users"][key]
                            thread = owned(s, "threads", ref, user)
                            _, history, fallback = agent.plan_context(s, user, thread, body)
                        channel.put(
                            {
                                "type": "step",
                                "id": "understand",
                                "label": {
                                    "en": "Reading your request…",
                                    "vi": "Mình đang xem yêu cầu…",
                                    "ko": "요청을 확인하고 있어요…",
                                    "zh": "正在查看你的请求…",
                                }[body.locale],
                                "status": "running",
                            }
                        )
                        planning_failed = False
                        fallback_info = None
                        try:
                            proposal = provider.invoke("propose", history, body.locale, fallback)
                        except Exception as exc:
                            proposal, planning_failed = fallback, True
                            fallback_info = error_info(exc, provider.name, "propose")
                        channel.put(
                            {
                                "type": "step",
                                "id": "understand",
                                "label": {
                                    "en": "Request understood",
                                    "vi": "Đã xem yêu cầu",
                                    "ko": "요청 확인 완료",
                                    "zh": "已查看请求",
                                }[body.locale],
                                "status": "done",
                            }
                        )
                        pending_events = []
                        # Re-read authority after the external call. Freeze remains responsive.
                        with store.transaction() as s:
                            user = s["users"][key]
                            thread = owned(s, "threads", ref, user)
                            result = agent.run(
                                s,
                                user,
                                thread,
                                body,
                                issuer,
                                provider,
                                lambda item: (
                                    channel.put(item)
                                    if item["type"] == "step"
                                    else pending_events.append(item)
                                ),
                                prepared_plan=proposal,
                                planning_failed=planning_failed,
                                defer_reply=True,
                                public_mode=public_mode,
                            )
                            facts = copy.deepcopy(thread["_lastFacts"])
                        for item in pending_events:
                            channel.put(item)
                        try:
                            if planning_failed:
                                raise ValueError("Planning unavailable")
                            reply, source = (
                                provider.invoke("reply", history, body.locale, facts),
                                provider.name,
                            )
                        except Exception as exc:
                            reply, source = agent.scripted_reply(facts, body.locale), "scripted_fallback"
                            if not planning_failed:
                                fallback_info = error_info(exc, provider.name, "reply")
                        token = {"type": "token", "text": reply, "source": source}
                        if fallback_info:
                            token["fallback"] = fallback_info
                        with store.transaction() as s:
                            thread = owned(s, "threads", ref, s["users"][key])
                            if facts["outcome"] == "approval" and s["frozen"].get(
                                s["users"][key]["familyId"]
                            ):
                                facts.update(outcome="payment_blocked", reason="FROZEN_OR_UNAVAILABLE")
                                token = {
                                    "type": "token",
                                    "text": agent.scripted_reply(facts, body.locale),
                                    "source": "scripted_state_refresh",
                                }
                                thread["_lastFacts"] = facts
                            message = next(
                                m for m in thread["messages"] if m["id"] == result[-1]["messageId"]
                            )
                            message["text"] = token["text"]
                            message["events"].append(token)
                            if source == "scripted_fallback" and not planning_failed:
                                audit(
                                    s,
                                    "agent",
                                    "reply_fallback",
                                    "Hosted reply unavailable or failed grounding validation; deterministic reply used",
                                )
                        channel.put(token)
                        channel.put(result[-1])  # Success only after committed reply.
                except DomainError as exc:
                    if exc.code in {"NOT_FOUND", "UNAUTHENTICATED"}:
                        channel.put(
                            {"type": "error", "code": exc.code, "message": "Session or thread unavailable"}
                        )
                    else:
                        with store.transaction() as state:
                            notice = agent.domain_notice(state, state["users"][key], ref, body, exc)
                        for item in notice:
                            channel.put(item)
                except Exception:
                    channel.put(
                        {
                            "type": "error",
                            "code": "AGENT_UNAVAILABLE",
                            "message": "Assistant unavailable; action not completed",
                        }
                    )
                finally:
                    channel.put(None)

            worker = threading.Thread(target=work, daemon=True)
            worker.start()
            while True:
                try:
                    item = channel.get(timeout=1)
                except queue.Empty:
                    yield ": working\n\n"
                    continue
                if item is None:
                    break
                yield from sse([item])

        return StreamingResponse(
            stream(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"}
        )

    @app.get("/api/approvals", response_model=list[m.Approval])
    def approvals(status: str = "pending", locale: str | None = None, key=Depends(user_id)):
        with store.transaction() as s:
            rows = family_rows(s, "approvals", s["users"][key])
            statuses = set(status.split(","))
            require(
                status == "all" or statuses <= {"pending", "approved", "rejected", "expired", "cooling_off"},
                "INVALID_STATUS",
                "Unknown approval status",
                422,
            )
            return localize(
                [r for r in rows if status == "all" or r["status"] in statuses],
                locale or s["users"][key]["locale"],
            )

    @app.get("/api/approvals/{ref}", response_model=m.Approval)
    def approval_get(ref: str, locale: str | None = None, key=Depends(user_id)):
        with store.transaction() as s:
            return localize(
                public(owned(s, "approvals", ref, s["users"][key])), locale or s["users"][key]["locale"]
            )

    @app.post("/api/approvals/{ref}/approve", response_model=m.Approval)
    def approval_approve(ref: str, body: m.SignIn, request: Request, key=Depends(user_id)):
        rp, selected_origin = auth.request_party(request, parties)
        with store.transaction() as s:
            user = s["users"][key]
            row = owned(s, "approvals", ref, user)
            require(
                user["role"]
                == ("student" if row["action"] in {"refund_claim", "escalation_letter"} else "parent"),
                "ROLE_REQUIRED",
                "Approval role mismatch",
            )
            require(
                not row.get("_riskOnly"),
                "VERIFICATION_REQUIRED",
                "Cooling and co-sign cannot authorize an unverified payee",
            )
            require(row["status"] == "pending", "INVALID_STATE", "Approval already used or expired", 409)
            require(
                row["action"] in {"refund_claim", "escalation_letter"}
                or not s["frozen"].get(user["familyId"]),
                "FROZEN",
                "Outbound payments paused",
            )
            require(dt(row["expiresAt"]) > dt(s["now"]), "APPROVAL_EXPIRED", "Approval expired", 409)
            require(digest(row["rawAction"]) == row["consentHash"], "CONSENT_MISMATCH", "Raw action changed")
            auth.consume(s, user, ref, body.assertion, row["consentHash"], demo, rp, selected_origin)
            require(chain.available(), "CHAIN_UNAVAILABLE", "Writes paused", 503)
            if row["action"] == "refund_claim":
                result = file_refund(s, row)
            elif row["action"] == "escalation_letter":
                from .escalations import submit

                result = submit(s, row)
            else:
                result = bank_execute(s, row, issuer)
            row["resultRef"] = result["id"]
            row["status"] = "approved"
            audit(s, user["id"], "approval_signed", "Exact action approved", consentHash=row["consentHash"])
            chain.anchor(s)
            return localize(public(row), user["locale"])

    @app.post("/api/approvals/{ref}/reject", response_model=m.Approval)
    def approval_reject(ref: str, body: m.RejectIn = m.RejectIn(), key=Depends(user_id)):
        with store.transaction() as s:
            user = s["users"][key]
            row = owned(s, "approvals", ref, user)
            require(
                user["role"]
                == ("student" if row["action"] in {"refund_claim", "escalation_letter"} else "parent")
            )
            require(row["status"] in {"pending", "cooling_off"}, "INVALID_STATE", "Not pending", 409)
            row["status"] = "rejected"
            audit(s, user["id"], "approval_rejected", "Human rejected action")
            return localize(public(row), user["locale"])

    @app.post("/api/approvals/{ref}/cosign", response_model=m.Approval)
    def approval_cosign(ref: str, body: m.SignIn, request: Request, key=Depends(user_id)):
        rp, selected_origin = auth.request_party(request, parties)
        with store.transaction() as s:
            user = s["users"][key]
            row = owned(s, "approvals", ref, user)
            expected = auth.target_hash(s, user, ref, "cosign")
            require(row["status"] == "cooling_off", "INVALID_STATE", "No co-sign review pending", 409)
            auth.consume(s, user, ref, body.assertion, expected, demo, rp, selected_origin)
            row["_cosigned"] = True
            row["cosigned"] = True
            row["cosignedAt"] = s["now"]
            event(
                s,
                user["familyId"],
                "approval_updated",
                {
                    "approvalId": ref,
                    "status": row["status"],
                    "cosigned": True,
                    "cosignedAt": row["cosignedAt"],
                },
            )
            # Compatibility for the current web notification subscriber.
            event(
                s,
                user["familyId"],
                "payment_updated",
                {"approvalId": ref, "cosigned": True, "cosignedAt": row["cosignedAt"]},
            )
            audit(
                s,
                user["id"],
                "risk_cosigned",
                "Home co-signer acknowledged review; no unsafe payment authorized",
                consentHash=expected,
            )
            return localize(public(row), user["locale"])

    @app.get("/api/catalog")
    def catalog(key=Depends(user_id)):
        with store.transaction() as s:
            user = s["users"][key]
            return {
                "issuer": issuer.did,
                "bankPayees": [public(v) for v in s["bankPayees"].values()],
                "familyId": user["familyId"],
                "bank": "MOCK",
                "bursar": "MOCK",
                "demo": demo,
            }

    @app.get("/api/screening")
    def screening(
        name: str = Query(min_length=1, max_length=200), type: str = "business", key=Depends(user_id)
    ):
        with store.transaction() as s:
            judge(s["users"][key])
            require(
                type in {"business", "person", "organization"}, "INVALID_TYPE", "Unsupported entity type", 422
            )
            result = issuer.screening.screen(name, type)
            audit(s, "system", "sanctions_screening", "Counterparty screened", ["S-01"], screening=result)
            return result

    @app.post("/api/demo/scenario-fixture")
    def scenario_fixture(body: m.ScenarioFixtureIn, key=Depends(user_id)):
        demo_only()
        with store.transaction() as s:
            judge(s["users"][key])
            if body.scenario == "T10":
                require(
                    not any(p["_family"] == "fam_wang" for p in s["payments"].values()),
                    "INVALID_STATE",
                    "Use fresh family sandbox",
                    409,
                )
                s["fxPurchases"] = [
                    {
                        "payer": payer,
                        "family": "fam_wang",
                        "beneficiary": "payee_hanbit",
                        "purpose": "tuition",
                        "at": s["now"],
                        "amount": "30000",
                        "remaining": "50000",
                    }
                    for payer in ("acct_parent_wang", "acct_mock_uncle")
                ]
            elif body.scenario == "T11":
                require(
                    not any(p["_family"] == "fam_minh" for p in s["payments"].values()),
                    "INVALID_STATE",
                    "Use fresh family sandbox",
                    409,
                )
                subject = verified_invoice(s, "fam_minh", issuer)
                subject["name"] = (
                    "MOCK-SANCTIONS-HIT"
                    if issuer.screening.mode == "synthetic"
                    else "KOREA KWANGSON BANKING CORP."
                )
                token = issuer.issue(
                    subject,
                    int(dt(s["now"]).timestamp()) - 86400 * 2,
                    int(dt(s["now"]).timestamp()) + 86400 * 365,
                )
                s["credentials"]["fam_minh"] = {"jwt": token, "status": "valid", "hash": digest(token)}
                chain.register(s)
            else:
                s["refundDelay"] = True
            audit(
                s,
                "system",
                "scenario_fixture",
                "Judge selected fixed synthetic scenario input",
                scenario=body.scenario,
            )
            return {"ok": True, "scenario": body.scenario, "mock": True}

    @app.get("/api/payments", response_model=list[m.Payment])
    def payments(key=Depends(user_id)):
        with store.transaction() as s:
            return family_rows(s, "payments", s["users"][key])

    @app.get("/api/payments/{ref}", response_model=m.Payment)
    def payment_get(ref: str, key=Depends(user_id)):
        with store.transaction() as s:
            return public(owned(s, "payments", ref, s["users"][key]))

    @app.post("/api/payments/{ref}/cancel", response_model=m.Payment)
    def payment_cancel(ref: str, key=Depends(user_id)):
        with store.transaction() as s:
            user = s["users"][key]
            row = owned(s, "payments", ref, user)
            cancel(s, row, user)
            return localize(public(row), user["locale"])

    @app.get(
        "/api/approvals/{ref}/paperwork/{kind}",
        response_class=Response,
        responses={200: {"content": {"application/pdf": {}}}},
    )
    def approval_paperwork(ref: str, kind: str, key=Depends(user_id)):
        from .paperwork import KINDS, pdf

        require(kind in KINDS, "NOT_FOUND", "Form not found", 404)
        with store.transaction() as s:
            approval = owned(s, "approvals", ref, s["users"][key])
            require(
                approval["action"] == "refund_claim" and "paperwork" in approval["rawAction"],
                "NOT_FOUND",
                "Refund forms not found",
                404,
            )
            return Response(
                pdf(approval, kind),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'inline; filename="{kind}.pdf"',
                    "Cache-Control": "no-store",
                },
            )

    @app.get("/api/refunds", response_model=list[m.Refund])
    def refunds(locale: str | None = None, key=Depends(user_id)):
        with store.transaction() as s:
            return localize(
                [
                    refund_view(s, r)
                    for r in s["refunds"].values()
                    if r["_family"] == s["users"][key]["familyId"]
                ],
                locale or s["users"][key]["locale"],
            )

    @app.get("/api/refunds/{ref}", response_model=m.Refund)
    def refund_get(ref: str, locale: str | None = None, key=Depends(user_id)):
        with store.transaction() as s:
            return localize(
                refund_view(s, owned(s, "refunds", ref, s["users"][key])), locale or s["users"][key]["locale"]
            )

    @app.get("/api/fx/quote", response_model=m.FxQuote)
    def fx(
        from_: str = Query(alias="from"),
        to: str = "KRW",
        amount: str = "7174000",
        side: str = "send",
        key=Depends(user_id),
    ):
        with store.transaction() as s:
            return quote(s, from_, to, amount, side)

    @app.get("/api/events")
    async def events(
        request: Request,
        key=Depends(user_id),
        last_event_id: str = Header(default="0"),
        after: int | None = None,
    ):
        try:
            cursor = max(0, after if after is not None else int(last_event_id))
        except ValueError:
            cursor = 0
        with store.transaction() as s:
            family = s["users"][key]["familyId"]

        async def stream():
            nonlocal cursor
            while not await request.is_disconnected():
                with store.transaction() as s:
                    batch = [e for e in s["events"] if e["id"] > cursor and e["_family"] == family]
                for e in batch:
                    cursor = e["id"]
                    yield "id: " + str(cursor) + "\n" + next(iter(sse([public(e)])))
                yield ": heartbeat\n\n"
                await asyncio.sleep(1)

        return StreamingResponse(stream(), media_type="text/event-stream")

    @app.post("/api/freeze")
    def freeze(key=Depends(user_id)):
        start = time.perf_counter()
        with store.transaction() as s:
            user = s["users"][key]
            require(user["role"] in {"parent", "student"})
            family = user["familyId"]
            result = freeze_family(s, family, user["id"], "USER_REQUESTED")
            result["tookMs"] = round((time.perf_counter() - start) * 1000, 3)
            return result

    @app.post("/api/unfreeze")
    def unfreeze(body: m.SignIn, request: Request, key=Depends(user_id)):
        rp, selected_origin = auth.request_party(request, parties)
        with store.transaction() as s:
            user = s["users"][key]
            parent(user)
            expected = auth.target_hash(s, user, user["familyId"], "freeze")
            auth.consume(s, user, user["familyId"], body.assertion, expected, demo, rp, selected_origin)
            require(chain.available(), "CHAIN_UNAVAILABLE", "Chain unavailable", 503)
            s["frozen"][user["familyId"]] = False
            s.setdefault("frozenReasons", {}).pop(user["familyId"], None)
            s["denials"][user["familyId"]] = 0
            restored = restore_frozen_mandates(s, user["familyId"])
            audit(
                s,
                user["id"],
                "unfreeze",
                "Outbound authority resumed; original mandate limits preserved",
                restoredMandates=restored,
            )
            result = {"frozen": False, "reason": None, "frozenReason": None, "restoredMandates": restored}
            event(s, user["familyId"], "freeze", result)
            return result

    @app.get("/api/audit/entries")
    def audit_entries(
        after: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), key=Depends(user_id)
    ):
        with store.transaction() as s:
            judge(s["users"][key])
            rows = s["audit"][after : after + limit]
            return {"entries": rows, "next": after + limit if len(s["audit"]) > after + limit else None}

    @app.post("/api/audit/verify")
    def audit_verify(key=Depends(user_id)):
        with store.transaction() as s:
            judge(s["users"][key])
            result = chain.verify(s)
            if result["ok"]:
                try:
                    mirror = [
                        json.loads(line) for line in store.audit_file.read_text(encoding="utf-8").splitlines()
                    ]
                    checked = verify(mirror)
                    if not checked["ok"] or mirror != s["audit"]:
                        result = {**checked, "ok": False, "detail": "JSONL mirror differs from SQLite log"}
                except Exception:
                    result = {
                        "ok": False,
                        "entries": len(s["audit"]),
                        "anchors": len(s["anchors"]),
                        "detail": "JSONL mirror unreadable",
                    }
            return result

    @app.get("/api/chain/status")
    def chain_status(key=Depends(user_id)):
        result = chain.status()
        with store.transaction() as s:
            return {
                **result,
                "registrationStatus": "pending" if s.get("registrationPending") else "ready",
                "anchorStatus": "retrying" if s.get("anchorDeferred") else "ready",
            }

    @app.get("/api/chain/anchors")
    def anchors(key=Depends(user_id)):
        with store.transaction() as s:
            return s["anchors"]

    @app.post("/api/chain/anchor")
    def anchor(key=Depends(user_id)):
        with store.transaction() as s:
            judge(s["users"][key])
            return chain.anchor(s) or {"unchanged": True}

    @app.post("/api/demo/tamper")
    def tamper(body: m.TamperIn, key=Depends(user_id)):
        demo_only()
        with store.transaction() as s:
            judge(s["users"][key])
            require(body.seq <= len(s["audit"]), "NOT_FOUND", "Audit entry not found", 404)
            require("tamperBackup" not in s, "INVALID_STATE", "Restore before another tamper", 409)
            s["tamperBackup"] = {"seq": body.seq, "summary": s["audit"][body.seq - 1]["summary"]}
            s["audit"][body.seq - 1]["summary"] += "!"
            return {"ok": True}

    @app.post("/api/demo/restore")
    def restore(key=Depends(user_id)):
        demo_only()
        with store.transaction() as s:
            judge(s["users"][key])
            backup = s.pop("tamperBackup", None)
            if backup:
                s["audit"][backup["seq"] - 1]["summary"] = backup["summary"]
            return {"ok": True}

    @app.get("/api/scenarios")
    def scenarios(key=Depends(user_id)):
        from .scenarios import CATALOG

        with store.transaction() as s:
            judge(s["users"][key])
        return CATALOG

    @app.post("/api/scenarios/run")
    def scenarios_run(body: m.ScenarioIn, key=Depends(user_id)):
        from .scenarios import CATALOG, run_scenarios

        demo_only()
        with store.transaction() as s:
            judge(s["users"][key])
        require(
            body.ids is None or all(i in {c["id"] for c in CATALOG} for i in body.ids),
            "UNKNOWN_SCENARIO",
            "Unknown scenario ID",
            422,
        )
        # Isolated sandbox: judge runs cannot reset a family's active demo.
        return StreamingResponse(
            sse(run_scenarios(body.ids, chain=chain if public_mode else None)), media_type="text/event-stream"
        )

    return app
