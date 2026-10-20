"""LangGraph dialogue proposals, deterministic execution, then grounded replies."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .conversation import (
    BLOCKED,
    Proposal,
    dialogue_locale,
    display_money,
    history_for_model,
    hypothetical_question,
    normalize,
    payment_mentioned,
    policy_topics,
    refund_question,
    refund_requested_facts,
    requested_facts,
    scripted_proposal,
    scripted_reply,
    tuition_mentioned,
)
from .engine import (
    DomainError,
    audit,
    dt,
    event,
    execute_rent,
    freeze_family,
    later,
    owned,
    pack,
    prepare_payment,
    prepare_refund,
    public,
    quote,
    refund_view,
    refusal_before_payment,
    require,
    resolve_invoice_action,
    risk_review,
    uid,
    verified_invoice,
)
from .incidents import scam_case, separate_report
from .localization import localize
from .policy import Context, evaluate, scam_score
from .policy_questions import policy_advice
from .reference import family_reference
from .refund_policy import POLICY
from .refund_policy import reconciliation as refund_reconciliation
from .security import redact
from .study import rent_setup, study_plan

STEPS = {
    "en": [
        "Reading the university record…",
        "Verifying Hanbit University's credential…",
        "Checking the bank's document pack…",
    ],
    "vi": [
        "Mình đang đọc hồ sơ học phí của trường…",
        "Đang kiểm tra chứng thực của Đại học Hanbit…",
        "Đang kiểm tra hồ sơ gửi ngân hàng…",
    ],
    "ko": ["대학 등록금 기록 확인 중…", "한빛대학교 인증 검증 중…", "은행 제출 서류 확인 중…"],
    "zh": ["正在读取学校学费记录…", "正在核验学校凭证…", "正在检查银行材料…"],
}


class State(TypedDict):
    text: str
    documents: list
    previous_scope: str
    proposal: dict


def classify(state):
    proposal = scripted_proposal(state["text"], state["documents"], state["previous_scope"])
    return {"proposal": proposal.model_dump()}


builder = StateGraph(State)
builder.add_node("intent", classify)
builder.add_edge(START, "intent")
builder.add_edge("intent", END)
GRAPH = builder.compile()


def grounded_facts(s, user, invoice, scope, outcome, locale="en"):
    """Allowlist, not redaction of raw state: identifiers/credentials never enter this object."""
    currency = "CNY" if user["familyId"] == "fam_wang" else "VND"
    invoice_status = None
    try:
        resolved = resolve_invoice_action(s, invoice, scope == "instalment" and outcome != "inform")
    except DomainError as exc:
        if exc.code != "INVOICE_SETTLED" or outcome not in {"inform", "prepare"}:
            raise
        # A reserved/paid invoice remains readable; it cannot become a new action.
        resolved = {"amount": invoice["amount"]}
        invoice_status = (
            "bank_hold"
            if any(
                p["_family"] == user["familyId"]
                and p["invoiceRef"] == invoice["invoiceRef"]
                and p["status"] == "sent"
                for p in s["payments"].values()
            )
            else "paid"
        )
    if outcome == "inform":
        resolved = {"amount": invoice["amount"]}
    q = quote(s, currency, "KRW", resolved["amount"], "receive")
    outbound = pack(s, user["familyId"])
    due = dt(invoice.get("dueAt", "2027-01-15T00:00:00Z"))
    due_text = {
        "en": due.strftime("%d %b %Y"),
        "vi": due.strftime("%d/%m/%Y"),
        "ko": f"{due.year}년 {due.month}월 {due.day}일",
        "zh": f"{due.year}年{due.month}月{due.day}日",
    }[locale]
    facts = {
        "outcome": outcome,
        "scope": scope,
        "invoiceSource": "verified_issuer",
        "invoiceComposition": [line["label"] for line in invoice["lines"]],
        "bank": "MOCK",
        "bursar": "MOCK",
        "moneyMoved": False,
        "rulesVersion": s["rulesVersion"],
        "missingDocuments": [d["kind"] for d in outbound["documents"] if d["status"] == "missing"],
        "display": {
            "invoiceAmount": display_money(
                {"amount": invoice["amount"], "currency": invoice["currency"]}, locale
            ),
            "instalmentCount": str(len(invoice["instalments"])),
            "instalmentSchedule": " + ".join(
                display_money({"amount": n, "currency": "KRW"}, locale) for n in invoice["instalments"]
            ),
            "fxSource": {
                "en": "MOCK board rate",
                "vi": "tỷ giá mô phỏng (MOCK)",
                "ko": "모의 고시 환율 (MOCK)",
                "zh": "模拟牌价（MOCK）",
            }[locale]
            if q["source"] == "MOCK"
            else "ECB reference rate",
            "payableAmount": display_money(q["receive"], locale),
            "sendAmount": display_money(q["send"], locale),
            "dueDate": due_text,
            "quotedAt": q["quotedAt"],
            "institution": "Hanbit University",
        },
    }
    if invoice_status:
        facts["invoiceStatus"] = invoice_status
        q.update(referenceOnly=True, invoiceStatus=invoice_status)
    return facts, q, outbound


def plan_context(s, user, thread, body):
    # Only explicitly referenced attachments belong to this envelope. History is display-only.
    refs = list(dict.fromkeys(body.documentIds))
    docs = [owned(s, "documents", ref, user) for ref in refs]
    for doc in docs:
        require(
            user["role"] == "parent" or doc["uploadedBy"] == user["id"],
            "NOT_FOUND",
            "Document not shared with this user",
            404,
        )
    history = history_for_model(thread, body.text)
    result = GRAPH.invoke(
        {
            "text": body.text,
            "documents": docs,
            "previous_scope": thread.get("_scope", "remaining"),
            "proposal": {},
        }
    )
    proposal = Proposal.model_validate(result["proposal"])
    if (
        not docs
        and thread.get("_lastFacts", {}).get("reason") == "policy"
        and proposal.intent in {"fallback", "inform", "clarify_request"}
        and not tuition_mentioned(normalize(body.text))
        and not any(
            normalize(word) in normalize(body.text)
            for word in (
                "invoice",
                "bill",
                "hóa đơn",
                "đợt",
                "instalment",
                "installment",
                "청구서",
                "분할",
                "账单",
                "分期",
            )
        )
        and not payment_mentioned(normalize(body.text))
    ):
        # Elliptical questions inherit the conversation's subject. This only
        # selects scripted prose; all signed reference facts are supplied anyway.
        proposal = proposal.model_copy(update={"intent": "policy", "needsClarification": False})
    focused = thread.get("_lastFacts", {}).get("reason") in {"scam", "scam_followup"}
    if scam_case(s, user, thread) and (
        (focused and proposal.intent in {"fallback", "clarify_request"})
        or (proposal.intent == "scam" and not separate_report(body.text))
    ):
        proposal = proposal.model_copy(update={"intent": "scam_followup", "needsClarification": False})
    if proposal.intent == "prepare" and (
        thread.get("_pendingIntent") == "pay"
        or (
            thread.get("_autoResumed")
            and any(
                a["_family"] == user["familyId"]
                and a["status"] == "pending"
                and a["action"] in {"first_payment", "payment"}
                for a in s["approvals"].values()
            )
        )
    ):
        proposal = proposal.model_copy(update={"intent": "pay"})
    return docs, history, proposal


def run(
    s,
    user,
    thread,
    body,
    issuer,
    provider,
    on_event=None,
    prepared_plan=None,
    planning_failed=False,
    defer_reply=False,
    public_mode=False,
):
    body = body.model_copy(update={"locale": dialogue_locale(body.text, thread.get("_locale", body.locale))})
    thread["_locale"] = body.locale
    docs, history, fallback = plan_context(s, user, thread, body)
    thread["_documentIds"] = list(dict.fromkeys(thread.get("_documentIds", []) + body.documentIds))
    events = []

    def emit(type_, **data):
        if type_ == "card":
            data = localize(data, body.locale)
        item = {"type": type_, **data}
        events.append(item)
        if on_event and type_ != "done":
            on_event(item)

    thread["messages"].append(
        {"id": uid("msg"), "role": "user", "text": redact(body.text), "documentIds": body.documentIds}
    )
    planner_ok = True
    try:
        if planning_failed:
            raise ValueError("Planning unavailable")
        proposal = (
            prepared_plan if prepared_plan is not None else provider.propose(history, body.locale, fallback)
        )
    except Exception:
        planner_ok = False
        proposal = fallback
        audit(
            s,
            "system",
            "llm_fallback",
            "Scripted planning used; deterministic money checks remain required",
        )
    # A hosted proposal cannot lift deterministic taint/never-list or chat-amount checks.
    if (
        fallback.intent in BLOCKED
        or fallback.intent == "scam_followup"
        or fallback.intent == "pocket_money"
        or fallback.intent == "policy"
        or (fallback.intent == "refund" and any(d["kind"] == "refusal" and not d["warnings"] for d in docs))
        or fallback.needsClarification
        or (fallback.intent == "pay" and proposal.intent == "inform")
        or (
            (thread.get("_pendingIntent") == "pay" or thread.get("_autoResumed"))
            and docs
            and fallback.intent == "pay"
            and proposal.intent in {"prepare", "fallback"}
        )
    ):
        proposal = fallback
    if (
        scam_case(s, user, thread)
        and proposal.intent in {"scam", "scam_followup"}
        and fallback.intent not in {"scam", "scam_followup"}
    ):
        # A model cannot turn a clear new tuition/refusal question into a new case
        # solely because a scam appears in untrusted conversation history.
        proposal = fallback
    if proposal.intent == "scam_followup" and not scam_case(s, user, thread):
        proposal = fallback
    intent = proposal.intent
    if thread.get("_pendingIntent") == "rent" and intent in {"prepare", "inform", "fallback"} and docs:
        intent = "rent"
    refund_rows = [r for r in s["refunds"].values() if r["_family"] == user["familyId"]]
    refund_drafts = [
        a
        for a in s["approvals"].values()
        if a["_family"] == user["familyId"]
        and a["action"] == "refund_claim"
        and "paperwork" in a["rawAction"]
    ]
    focused_refund = thread.get("_lastFacts", {}).get("reason") in {"refund", "refund_parent", "refund_info"}
    if (
        not docs
        and (refund_rows or refund_drafts)
        and (
            fallback.intent in {"inform", "fallback", "clarify_request"}
            or (
                fallback.intent == "policy"
                and policy_topics(body.text) == ["visa_refusal"]
                and not hypothetical_question(body.text)
            )
        )
        and not fallback.needsClarification
        and proposal.intent not in BLOCKED
        and refund_question(body.text, focused_refund)
    ):
        # A status/deduction question is a read, never a fresh financial proposal.
        intent = "refund_info"
    thread.pop("_autoResumed", None)
    if intent not in {"pay", "inform", "prepare", "policy", "rent"}:
        thread["_pendingIntent"] = None
    facts = {"outcome": "fallback", "reason": intent, "scope": proposal.scope, "moneyMoved": False}
    if intent == "policy":
        # Explain the signed terms without testing payment prerequisites, opening
        # a claim, or treating a hypothetical visa denial as documentary evidence.
        credential = s["credentials"][user["familyId"]]
        require(credential["status"] == "valid", "CREDENTIAL_REVOKED", "Issuer credential revoked", 403)
        invoice = issuer.verify(credential["jwt"], int(dt(s["now"]).timestamp()))
        require(invoice["familyId"] == user["familyId"], "CREDENTIAL_INVALID", "Wrong family", 403)
        explicit_topics = policy_topics(body.text)
        topics = explicit_topics or thread.get("_lastFacts", {}).get("policyAdvice", {}).get("topics", [])
        advice = policy_advice(invoice, topics)
        facts.update(
            outcome="policy", reason="policy", policyAdvice=advice, policyFollowup=not bool(explicit_topics)
        )
        # This is an answer, not an actionable case/status card. The current
        # web renders unknown info codes literally, so keep this prose-only.
        audit(
            s,
            "agent",
            "policy_explained",
            "Read-only policy question; no financial action",
            familyId=user["familyId"],
            topics=advice["topics"],
        )
    elif intent == "scam_followup":
        review = scam_case(s, user, thread)
        if review:
            thread["_scamReviewId"] = review["id"]
            emit(
                "card",
                kind="info",
                data={
                    "code": "SCAM_CASE_FOLLOWUP",
                    "approvalId": review["id"],
                    "status": review["status"],
                    "cosigned": review.get("_cosigned", False),
                    "cosignedAt": review.get("cosignedAt"),
                    "coolingUntil": review["cooling"]["until"],
                },
            )
            facts.update(
                outcome="scam_followup",
                reason="scam_followup",
                incident={
                    "status": review["status"],
                    "cosigned": review.get("_cosigned", False),
                    "newCase": False,
                },
            )
            audit(
                s,
                "agent",
                "scam_case_followup",
                "Support within the existing non-executable case",
                caseRef=review["id"],
                familyId=user["familyId"],
            )
        else:
            # Stale/model-supplied follow-up labels never create a review or authority.
            facts.update(outcome="fallback", reason="fallback")
    elif intent in BLOCKED:
        extra = {}
        if intent == "scam":
            score, features = scam_score(
                body.text + " ".join(f["value"] for d in docs for f in d["fields"]),
                new_payee=True,
                credentialed=False,
            )
            decision = evaluate(Context(risk_score=score))
            review = risk_review(s, user, score, features)
            review["_threadId"] = thread["threadId"]
            thread["_scamReviewId"] = review["id"]
            emit("card", kind="approval_required", data=public(review))
            extra = {
                "risk": {"score": score, "features": features},
                "cooling": {
                    "until": later(s, hours=24),
                    "cosignRequired": True,
                    "cosignerId": "usr_mother_lan",
                },
                "verificationChecklist": [
                    "Contact the student independently",
                    "Call the university's published number",
                ],
                "executable": False,
            }
        else:
            decision = evaluate(
                Context(
                    action=intent if intent != "structuring" else "payment",
                    structuring=intent == "structuring",
                )
            )
        envelope = uid("env")
        emit("envelope", envelopeId=envelope, action=intent, requestedTier="L2")
        emit("disposition", envelopeId=envelope, **decision.as_dict())
        emit(
            "card",
            kind="blocked",
            data={
                **decision.as_dict(),
                "outOfBandVerificationRequired": intent in {"document_instruction", "scam"},
                **blocked_details(
                    intent, docs, decision.as_dict()["reasons"] + extra.get("risk", {}).get("features", [])
                ),
                **extra,
            },
        )
        facts.update(outcome="blocked", reason=intent, disposition=decision.as_dict())
        if intent == "document_instruction":
            facts["safeNextStep"] = (
                "Verify the document or account change using the university's published contact; only the existing verified payee is available."
            )
        audit(s, "agent", "blocked", decision.code, [decision.rule], envelopeId=envelope)
        event(s, user["familyId"], "blocked", decision.as_dict())
        count = s["denials"].get(user["familyId"], 0) + 1
        s["denials"][user["familyId"]] = count
        if count >= 5:
            freeze_family(s, user["familyId"], "system", "DENIAL_CIRCUIT_BREAKER")
            audit(s, "system", "denial_circuit_breaker", "Five denied requests; family writes frozen")
    elif intent == "pocket_money":
        facts.update(outcome="pocket_money", reason="pocket_money")
    elif intent == "clarify_request":
        facts.update(outcome="clarify_request", reason="clarify_request")
    elif intent == "refund" and (
        s.get("admissionDispositions", {}).get(user["familyId"])
        or (
            user["role"] == "student"
            and any(d["kind"] == "refusal" and not d["warnings"] for d in docs)
            and not any(
                p["_family"] == user["familyId"]
                and p.get("purpose") == "tuition"
                and p["status"] != "cancelled"
                for p in s["payments"].values()
            )
        )
    ):
        row = s.get("admissionDispositions", {}).get(user["familyId"])
        if not row:
            document = next(d for d in docs if d["kind"] == "refusal" and not d["warnings"])
            row = refusal_before_payment(s, user, document, issuer)
        emit(
            "card",
            kind="needs",
            data={
                "code": row["code"],
                "admissionDisposition": row,
                "missing": [
                    {"kind": "admission_withdrawal", "actorId": user["id"], "action": "contact_university"}
                ],
            },
        )
        facts.update(outcome="refused_unpaid", reason="refused_unpaid", admissionDisposition=row)
    elif intent == "pay" and s.get("admissionDispositions", {}).get(user["familyId"]):
        emit(
            "card",
            kind="needs",
            data={
                "code": "ADMISSION_RECONFIRMATION_REQUIRED",
                "missing": [
                    {
                        "kind": "new_signed_admission_and_invoice",
                        "actorId": "university",
                        "action": "reconfirm",
                    }
                ],
            },
        )
        thread["_pendingIntent"] = None
        facts.update(
            outcome="refused_unpaid",
            reason="refused_unpaid",
            admissionDisposition=s["admissionDispositions"][user["familyId"]],
        )
    elif intent in {"inform", "prepare", "pay", "rent"} and (
        s.get("registrationPending") or not issuer.chain.available()
    ):
        emit(
            "card",
            kind="needs",
            data={
                "code": "CHAIN_UNAVAILABLE",
                "missing": [{"kind": "chain", "actorId": "platform", "action": "wait"}],
            },
        )
        facts.update(outcome="chain_unavailable", reason="chain_unavailable")
        s["chainRetryPending"] = True
        audit(
            s,
            "agent",
            "chain_action_deferred",
            "Chain-dependent action paused; conversation remains available",
            familyId=user["familyId"],
        )
        if intent == "pay":
            thread.update(_pendingIntent="pay", _pendingAt=s["now"], _scope=proposal.scope)
    elif intent == "pay" and study_plan(s, user, issuer)["seedRefreshRequired"]:
        emit(
            "card",
            kind="needs",
            data={
                "code": "DEMO_SEED_REFRESH_REQUIRED",
                "missing": [
                    {"kind": "current_tuition_seed", "actorId": "visitor", "action": "reset_own_demo"}
                ],
            },
        )
        facts.update(outcome="seed_refresh_required", reason="seed_refresh_required")
    elif intent == "pay" and study_plan(s, user, issuer)["paymentWindowStatus"] not in {
        "open",
        "legacy_unspecified",
        "settled",
    }:
        calendar = study_plan(s, user, issuer)
        emit(
            "card",
            kind="needs",
            data={
                "code": "REGISTRATION_WINDOW_REQUIRED",
                "calendar": calendar,
                "missing": [
                    {
                        "kind": "registration_window",
                        "actorId": "university",
                        "action": "wait_or_contact_bursar",
                    }
                ],
            },
        )
        facts.update(outcome="registration_required", reason="registration_required")
    elif intent in {"inform", "prepare", "pay"}:
        if intent == "pay" and proposal.needsClarification:
            thread["_pendingIntent"] = None
            facts.update(outcome="clarify", reason="clarify")
        else:
            for index, label in enumerate(STEPS[body.locale]):
                emit("step", id=f"step_{index}", label=label, status="running")
                if index == 1:
                    invoice = verified_invoice(s, user["familyId"], issuer)
                emit("step", id=f"step_{index}", label=label, status="done")
            try:
                facts, q, outbound = grounded_facts(s, user, invoice, proposal.scope, intent, body.locale)
                if intent == "inform":
                    facts["requestedFacts"] = requested_facts(body.text)
                emit(
                    "card",
                    kind="quote",
                    data={
                        **q,
                        "invoiceRef": "HBU-2027-0042",
                        "dueAt": invoice["dueAt"],
                        "rulesVersion": s["rulesVersion"],
                    },
                )
                emit("card", kind="pack", data=outbound)
                if intent == "pay":
                    # A correction withdraws the old proposal; it never rewrites a signed action.
                    for old in s["approvals"].values():
                        if (
                            old["_family"] == user["familyId"]
                            and old["action"] in {"first_payment", "payment"}
                            and old["status"] == "pending"
                            and not old.get("_riskOnly")
                            and (old["rawAction"].get("tranche") == "remaining")
                            != (proposal.scope == "remaining")
                        ):
                            old["status"] = "rejected"
                            audit(
                                s,
                                "agent",
                                "proposal_superseded",
                                "User corrected payment scope; old consent cannot be reused",
                                consentHash=old["consentHash"],
                            )
                    approval, decision = prepare_payment(
                        s, user, issuer, instalment=proposal.scope == "instalment"
                    )
                    envelope = uid("env")
                    emit("envelope", envelopeId=envelope, action="execute_payment", requestedTier="L2")
                    emit("disposition", envelopeId=envelope, **decision.as_dict())
                    facts["disposition"] = decision.as_dict()
                    if approval:
                        thread["_pendingIntent"] = None
                        pending = approval["status"] == "pending"
                        emit("card", kind="approval_required" if pending else "info", data=public(approval))
                        facts["outcome"] = "approval" if pending else "executed"
                        facts["moneyMoved"] = not pending
                        if not pending:
                            facts["paymentStatus"] = s["payments"][approval["resultRef"]]["status"]
                    else:
                        missing = [
                            {"kind": d["kind"], "actorId": user["id"], "action": "upload"}
                            for d in outbound["documents"]
                            if d["status"] == "missing"
                        ]
                        if decision.code == "MANDATE_REQUIRED":
                            missing.insert(
                                0,
                                {
                                    "kind": "mandate",
                                    "actorId": next(
                                        u["id"]
                                        for u in s["users"].values()
                                        if u["familyId"] == user["familyId"] and u["role"] == "parent"
                                    ),
                                    "action": "sign",
                                },
                            )
                        prerequisite = decision.code in {"MANDATE_REQUIRED", "DOCUMENTS_REQUIRED"}
                        emit(
                            "card",
                            kind="needs" if prerequisite else "blocked",
                            data={**decision.as_dict(), "missing": missing if prerequisite else []},
                        )
                        thread["_pendingIntent"] = "pay" if prerequisite else None
                        if prerequisite:
                            thread["_pendingAt"] = s["now"]
                        facts.update(outcome="payment_blocked", reason=decision.code)
                thread["_scope"] = proposal.scope
            except DomainError as exc:
                if exc.code != "INVOICE_SETTLED":
                    raise
                held = any(
                    p["_family"] == user["familyId"] and p["status"] == "sent" for p in s["payments"].values()
                )
                facts.update(
                    outcome="payment_pending" if held else "already_paid",
                    reason="payment_pending" if held else "already_paid",
                )
                emit(
                    "card",
                    kind="info",
                    data={
                        "code": "PAYMENT_PENDING" if held else "INVOICE_SETTLED",
                        "paymentStatus": "sent" if held else "matched",
                    },
                )
    elif intent == "refund_info":
        row = refund_rows[-1] if refund_rows else None
        draft = refund_drafts[-1] if refund_drafts else None
        packet = row.get("paperwork") if row else draft["rawAction"]["paperwork"]
        if not packet:
            raise DomainError("SEED_REFRESH_REQUIRED", "Legacy refund needs explicit review", 409)
        before = packet["eligibility"] == "before_start_full_unused"
        payment = s["payments"][row["paymentId"] if row else draft["rawAction"]["paymentId"]]
        status = row["status"] if row else draft["status"]
        display = {}
        if before:
            deadline = dt(packet["deadline"])
            display["refundDeadline"] = {
                "vi": deadline.strftime("%d/%m/%Y"),
                "en": deadline.strftime("%d %b %Y"),
                "ko": f"{deadline.year}년 {deadline.month}월 {deadline.day}일",
                "zh": f"{deadline.year}年{deadline.month}月{deadline.day}日",
            }[body.locale]
            settled = row.get("reconciliation") if row else None
            estimate = settled or (
                refund_view(s, row)["estimate"]
                if row
                else refund_reconciliation(payment, payment["send"]["currency"])
            )
            if estimate:
                display["refundReceivedBack"] = display_money(estimate["receivedBack"], body.locale)
                for key, line in zip(
                    ("refundBankFee", "refundFxLoss", "refundWireFee", "refundRetention"),
                    estimate["lines"],
                    strict=True,
                ):
                    display[key] = display_money(line["amount"], body.locale)
        emit(
            "card",
            kind="refund" if row else "info",
            data=refund_view(s, row)
            if row
            else {
                "code": "REFUND_CASE_STATUS",
                "approvalId": draft["id"],
                "status": status,
            },
        )
        facts.update(
            outcome="refund_info",
            reason="refund_info",
            display=display,
            requestedFacts=refund_requested_facts(body.text, display),
            refundPolicy={
                "beforeStart": before,
                "claimStatus": status,
                "received": status in {"received", "reconciled"},
                "estimateSource": "MOCK return wire board; not a market quote or guarantee",
                "familyCosts": "original bank fee, intermediary wire fee, KRW to USD to home-currency conversion loss; no admission fee charged",
                "formPurpose": "cancel admission and reapply; not leave of absence",
            },
        )
        audit(
            s,
            user["id"],
            "refund_case_followup",
            "Read existing refund case; no new consent or transfer",
            refundId=row["id"] if row else None,
            approvalId=draft["id"] if draft else None,
        )
    elif intent == "refund":
        if user["role"] == "parent":
            active = [r for r in s["refunds"].values() if r["_family"] == user["familyId"]]
            if active:
                emit("card", kind="refund", data=public(active[-1]))
            else:
                emit(
                    "card",
                    kind="needs",
                    data={
                        "code": "STUDENT_REFUND_REQUEST_REQUIRED",
                        "missing": [
                            {
                                "kind": "refusal_and_refund_forms",
                                "actorId": next(
                                    u["id"]
                                    for u in s["users"].values()
                                    if u["familyId"] == user["familyId"] and u["role"] == "student"
                                ),
                                "action": "upload_and_sign",
                            }
                        ],
                    },
                )
            facts.update(
                outcome="refund_parent",
                reason="refund_parent",
                readerRole=user["role"],
                readerName=user["name"],
                refundPolicy={
                    "beforeStart": active[-1].get("eligibility") == "before_start_full_unused"
                    if active
                    else dt(s["now"]) < dt(POLICY["classesStart"]),
                    "claimStatus": active[-1]["status"] if active else "not_filed",
                    "studentMustAct": not bool(active),
                    "studentSigner": next(
                        u["name"]
                        for u in s["users"].values()
                        if u["familyId"] == user["familyId"] and u["role"] == "student"
                    ),
                    "promise": "before-start requests: within two weeks after classes start; after-start: manual degree assessment",
                    "familyCosts": "original bank fee, intermediary wire fee and KRW to USD to home-currency loss",
                    "retention": "separately charged admission fees only; none on this invoice",
                    "destination": "original payer bank record only",
                },
            )
        else:
            valid = any(d["kind"] == "refusal" and not d["warnings"] for d in docs)
            held = any(
                p["_family"] == user["familyId"] and p.get("purpose") == "tuition" and p["status"] == "sent"
                for p in s["payments"].values()
            )
            if held:
                emit(
                    "card",
                    kind="needs",
                    data={
                        "code": "PAYMENT_SETTLEMENT_REQUIRED",
                        "missing": [{"kind": "payment_settlement", "actorId": "bank", "action": "wait"}],
                    },
                )
                facts.update(outcome="payment_pending", reason="payment_pending")
                valid = False
            if valid:
                approval = prepare_refund(s, user, issuer)
                emit("card", kind="approval_required", data=public(approval))
                facts.update(
                    outcome="refund",
                    reason="refund",
                    destination="original_payer_only",
                    refundPolicy={
                        "beforeStart": approval["rawAction"]["paperwork"]["eligibility"]
                        == "before_start_full_unused",
                        "promise": "within two weeks after classes start",
                        "refunds": "paid tuition only; dormitory and NHIS are separate and excluded",
                        "retains": "separately charged admission fees only; none on this invoice",
                        "familyCosts": "original outward bank fee, intermediary wire fee, KRW to USD to home-currency conversion loss",
                        "signature": "student signs admission withdrawal and tuition refund application",
                        "formPurpose": "cancel admission and reapply; not leave of absence",
                        "afterStart": "manual degree-office assessment, no automatic day table",
                    },
                )
            elif not held:
                emit(
                    "card",
                    kind="needs",
                    data={
                        "code": "REFUSAL_DOCUMENT_REQUIRED",
                        "missing": [{"kind": "refusal", "actorId": user["id"], "action": "upload"}],
                    },
                )
                facts.update(outcome="refusal_required", reason="refusal_required")
    elif intent == "rent":
        setup = rent_setup(s, user)
        if setup["missing"]:
            emit("card", kind="needs", data={"code": "RENT_PREREQUISITES_REQUIRED", **setup})
            facts.update(
                outcome="rent_needs",
                reason="rent_needs",
                missingDocuments=[m["kind"] for m in setup["missing"]],
            )
            thread.update(_pendingIntent="rent", _pendingAt=s["now"])
        else:
            payment, decision = execute_rent(s, user, issuer, allow_cancelled=True)
            if decision:
                emit("disposition", envelopeId=uid("env"), **decision.as_dict())
            emit("card", kind="payment", data=public(payment))
            facts.update(
                outcome="rent_executed",
                reason="rent_executed",
                moneyMoved=True,
                paymentStatus=payment["status"],
                cancelAvailable=payment["status"] == "sent",
                display={
                    "payableAmount": display_money(payment["receive"], body.locale),
                    "sendAmount": display_money(payment["send"], body.locale),
                },
            )
            thread["_pendingIntent"] = None
    if facts["outcome"] == "refund":
        packet = approval["rawAction"]["paperwork"]
        if packet["deadline"]:
            from .reference import date_text

            payment = s["payments"][approval["rawAction"]["paymentId"]]
            estimate = refund_reconciliation(payment, payment["send"]["currency"])
            facts["display"] = {
                "refundDeadline": date_text(packet["deadline"], body.locale),
                "refundReceivedBack": display_money(estimate["receivedBack"], body.locale),
            }
    facts["readerRole"] = user["role"]
    facts["readerName"] = user["name"]
    reference, reference_display = family_reference(s, user, issuer, body.locale)
    facts["familyReference"] = reference
    facts["display"] = {**reference_display, **facts.get("display", {})}
    thread["_lastFacts"] = facts
    if defer_reply:
        message = {
            "id": uid("msg"),
            "role": "assistant",
            "text": "",
            "events": events.copy(),
            "aiGenerated": True,
        }
        thread["messages"].append(message)
        emit("done", messageId=message["id"])
        return events
    if not planner_ok:
        reply, source = scripted_reply(facts, body.locale), "scripted_fallback"
    else:
        try:
            reply = provider.reply(history, body.locale, facts)
            source = provider.name
        except Exception:
            reply, source = scripted_reply(facts, body.locale), "scripted_fallback"
            audit(
                s,
                "agent",
                "reply_fallback",
                "Hosted reply unavailable or failed grounding validation; deterministic reply used",
            )
    emit("token", text=reply, source=source)
    # Internal facts contain only the allowlist above, useful for dialogue evals, not authority.
    facts["readerRole"] = user["role"]
    thread["_lastFacts"] = facts
    message = {
        "id": uid("msg"),
        "role": "assistant",
        "text": reply,
        "events": events.copy(),
        "aiGenerated": True,
    }
    thread["messages"].append(message)
    emit("done", messageId=message["id"])
    return events


def domain_notice(s, user, ref, body, exc):
    """Explain an aborted transaction; never turn a domain failure into authority."""
    thread = owned(s, "threads", ref, user)
    require(thread["_owner"] == user["id"], "NOT_FOUND", "Thread not found", 404)
    facts = {
        "outcome": "domain_notice",
        "reason": exc.code,
        "readerRole": user["role"],
        "readerName": user["name"],
        "moneyMoved": False,
    }
    thread["_lastFacts"] = facts
    thread["messages"].append(
        {"id": uid("msg"), "role": "user", "text": redact(body.text), "documentIds": body.documentIds}
    )
    message_id = uid("msg")
    events = [
        {
            "type": "card",
            "kind": "blocked" if exc.status == 403 and exc.code != "FROZEN" else "needs",
            "data": {"code": exc.code, "ruleId": exc.rule, "actionCompleted": False},
        },
        {"type": "token", "text": scripted_reply(facts, body.locale), "source": "scripted_domain"},
    ]
    thread["messages"].append(
        {
            "id": message_id,
            "role": "assistant",
            "text": events[1]["text"],
            "events": events.copy(),
            "aiGenerated": True,
        }
    )
    audit(
        s,
        "agent",
        "dialogue_action_not_prepared",
        "Domain refusal explained; attempted transaction rolled back",
        familyId=user["familyId"],
        code=exc.code,
    )
    return events + [{"type": "done", "messageId": message_id}]


def blocked_details(intent, docs, engine_reasons=()):
    """Display-only quotation of untrusted attempts. Never passed to bank resolution."""
    reasons = list(engine_reasons)
    attempted = {
        "action": "change_refund_destination"
        if intent == "refund_redirect"
        else "execute_payment"
        if intent == "document_instruction" and docs
        else intent,
        "provenance": "untrusted_doc" if docs else "user_input",
    }
    for doc in docs:
        reasons.extend(doc["warnings"])
        fields = {f["name"]: f["value"] for f in doc["fields"]}
        attempted["source"] = {"kind": doc["kind"], "filename": doc["filename"]}
        if "account" in fields:
            attempted["account"] = fields["account"]
            attempted["payee"] = {
                "name": "Unverified document payee",
                "account": {
                    "masked": fields["account"],
                    "bank": "Unverified document text",
                    "hashMatch": False,
                },
            }
        if "amount" in fields:
            attempted["amount"] = {"amount": fields["amount"].replace(",", ""), "currency": "KRW"}
    if any(d["warnings"] for d in docs):
        reasons.extend(
            [
                {"ruleId": "P-01", "code": "PAYEE_UNVERIFIED", "severity": "block", "params": {}},
                {"ruleId": "T-01", "code": "TAINTED_PARAMETERS", "severity": "block", "params": {}},
            ]
        )
    return {
        "attempted": attempted,
        "reasons": reasons + [{"ruleId": "LX-03", "code": intent.upper(), "severity": "block", "params": {}}],
    }
