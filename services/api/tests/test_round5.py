"""Family continuation, presentation and early streaming without new money authority."""

import asyncio
import json
import threading

import pytest

from bursarbridge.conversation import dialogue_locale, scripted_proposal
from bursarbridge.models import MessageIn
from bursarbridge.providers import Provider


def say(j, ref, text):
    response = j.request(
        "POST", f"/agent/threads/{ref}/messages", "student_linh", json={"text": text, "locale": "vi"}
    )
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    assert not any(e["type"] == "error" for e in events)
    return events


@pytest.mark.parametrize("mandate_last", [True, False])
def test_last_family_prerequisite_resumes_original_scope_once(journey, mandate_last):
    j = journey
    ref = j.ok("POST", "/agent/threads", "student_linh")["threadId"]
    say(j, ref, "chỉ trả đợt 1 thôi")
    if not mandate_last:
        j.mandate()
    j.upload("admission")
    assert not j.ok("GET", "/approvals")
    j.upload("invoice")
    if mandate_last:
        assert not j.ok("GET", "/approvals")
        j.mandate()
    approval = j.ok("GET", "/approvals")[0]
    assert approval["rawAction"]["receive"]["amount"] == "3587000.00"
    assert not j.ok("GET", "/payments")
    thread = j.ok("GET", f"/agent/threads/{ref}", "student_linh")
    assert [m["role"] for m in thread["messages"]] == ["user", "assistant", "assistant"]
    assert any(e.get("kind") == "approval_required" for e in thread["messages"][-1]["events"])
    with j.app.state.store.transaction() as s:
        notification = next(e for e in s["events"] if e["type"] == "thread_updated")
        assert notification["data"] == {"threadId": ref, "messageId": thread["messages"][-1]["id"]}
    j.upload("invoice")
    j.mandate()
    assert len(j.ok("GET", "/approvals")) == 1
    assert len(j.ok("GET", f"/agent/threads/{ref}", "student_linh")["messages"]) == 3


@pytest.mark.parametrize("stop", ["freeze", "expiry", "change"])
def test_continuation_does_not_revive_frozen_expired_or_changed_intent(journey, stop):
    j = journey
    ref = j.ok("POST", "/agent/threads", "student_linh")["threadId"]
    say(j, ref, "đóng tiền học giùm con")
    if stop == "change":
        say(j, ref, "ba gửi con tiền tiêu vặt")
    if stop == "expiry":
        j.ok("POST", "/clock/advance", "judge", json={"hours": 25})
    j.mandate()
    if stop == "freeze":
        j.ok("POST", "/freeze")
    j.upload("admission")
    j.upload("invoice")
    assert not j.ok("GET", "/approvals") and not j.ok("GET", "/payments")


def test_cosign_is_public_not_authority_and_history_is_filterable(journey):
    j = journey
    j.chat("police proof-of-funds verification deposit")
    review = j.ok("GET", "/approvals?status=all")[0]
    assert review["cosigned"] is False and review["cosignedAt"] is None
    signed = j.ok(
        "POST", f"/approvals/{review['id']}/cosign", "mother_lan", json={"assertion": {"demo": True}}
    )
    other_phone = j.ok("GET", f"/approvals/{review['id']}")
    assert signed["cosigned"] and signed["cosignedAt"] == other_phone["cosignedAt"]
    assert (
        j.request(
            "POST", f"/approvals/{review['id']}/approve", json={"assertion": {"demo": True}}
        ).status_code
        == 403
    )
    with j.app.state.store.transaction() as s:
        data = next(e["data"] for e in s["events"] if e["type"] == "approval_updated")
        assert data["approvalId"] == review["id"] and data["cosigned"]
    j.ok("POST", f"/approvals/{review['id']}/reject")
    assert j.ok("GET", "/approvals") == []
    assert len(j.ok("GET", "/approvals?status=pending,rejected")) == 1
    assert j.ok("GET", "/approvals?status=all", "parent_wang") == []
    assert j.request("GET", "/approvals?status=nonsense").status_code == 422


def test_localized_presentations_keep_consent_bytes_and_refund_clauses(journey):
    from bursarbridge.security import digest

    j = journey
    j.prepare()
    approval = j.ok("GET", "/approvals?locale=en")[0]
    for locale, word in [("vi", "Học kỳ"), ("ko", "학기"), ("zh", "学期")]:
        localized = j.ok("GET", f"/approvals/{approval['id']}?locale={locale}")
        assert word in localized["invoice"]["term"]
        assert digest(localized["rawAction"]) == approval["consentHash"]
    j.approve(approval)
    j.ok("POST", "/clock/advance", "judge", json={"hours": 1})
    refusal = j.upload("refusal")
    j.chat("visa refused", [refusal["id"]])
    j.approve(j.ok("GET", "/approvals")[0], "student_linh")
    j.advance_refund()
    for locale in ("vi", "ko", "zh"):
        refund = j.ok("GET", f"/refunds?locale={locale}")[0]
        clauses = [line["clause"] for line in refund["reconciliation"]["lines"]]
        assert all("fictional" not in text and "board rate" not in text for text in clauses)


def test_progress_body_is_available_while_planner_is_still_waiting(journey, monkeypatch):
    j = journey
    entered, release = threading.Event(), threading.Event()
    original = Provider.propose

    def wait(*args):
        entered.set()
        assert release.wait(5)
        return original(*args)

    monkeypatch.setattr(Provider, "propose", wait)
    ref = j.ok("POST", "/agent/threads", "student_linh")["threadId"]
    endpoint = next(r.endpoint for r in j.app.routes if r.path == "/api/agent/threads/{ref}/messages")

    async def check():
        response = endpoint(ref, MessageIn(text="pay tuition"), key="student_linh")
        stream = response.body_iterator
        try:
            first = await asyncio.wait_for(anext(stream), timeout=1)
            assert '"type":"step"' in first and '"status":"running"' in first
            assert entered.wait(1) and not release.is_set()
        finally:
            release.set()
        rest = "".join([part async for part in stream])
        assert "event: done" in rest and "event: error" not in rest

    asyncio.run(check())


@pytest.mark.parametrize("verb", ["đóng", "nộp", "chuyển"])
@pytest.mark.parametrize("noun", ["tiền trường", "học phí", "tiền học"])
def test_deadline_worry_requests_help_without_overriding_factual_questions(verb, noun):
    assert scripted_proposal(f"sắp tới hạn {verb} {noun} rồi, làm sao đây").intent == "pay"
    assert scripted_proposal(f"{noun} bao nhiêu, hạn khi nào?").intent == "inform"
    assert scripted_proposal(f"đừng {verb} {noun} vội").intent != "pay"


def test_input_language_beats_app_locale():
    assert dialogue_locale("등록금 내줘 please", "vi") == "ko"
    assert dialogue_locale("帮我交学费", "vi") == "zh"
    assert dialogue_locale("please pay tuition", "vi") == "en"
    assert dialogue_locale("", "ko") == "ko"


@pytest.mark.parametrize("settle", [False, True])
def test_paid_or_reserved_invoice_stays_readable_without_new_payment(journey, settle):
    j = journey
    j.pay(settle=settle)
    before = j.ok("GET", "/payments")
    events = j.chat("học phí bao nhiêu vậy, hạn khi nào?", locale="vi")
    text = next(e["text"] for e in events if e["type"] == "token")
    card = next(e["data"] for e in events if e.get("kind") == "quote")
    assert "7.174.000 KRW" in text and "15/01/2027" in text
    assert card["referenceOnly"] and card["invoiceStatus"] == ("paid" if settle else "bank_hold")
    assert not any(e.get("kind") == "approval_required" for e in events)
    assert j.ok("GET", "/payments") == before
    assert not j.ok("GET", "/approvals")


@pytest.mark.parametrize(
    "text",
    [
        "tuition due soon, what should I do?",
        "곧 등록금 마감인데 어떡해",
        "学费快到期了怎么办",
        "sắp tới hạn học phí rồi giúp con",
    ],
)
def test_urgent_help_does_not_require_an_imperative_payment_verb(text):
    assert scripted_proposal(text).intent == "pay"


def test_continuation_failure_does_not_undo_successful_family_signature(journey, monkeypatch):
    from bursarbridge import agent
    from bursarbridge.engine import DomainError

    j = journey
    ref = j.ok("POST", "/agent/threads", "student_linh")["threadId"]
    say(j, ref, "đóng học phí giúp con")
    j.upload("admission")
    j.upload("invoice")
    monkeypatch.setattr(
        agent, "run", lambda *a, **k: (_ for _ in ()).throw(DomainError("CHAIN_UNAVAILABLE", "Writes paused"))
    )
    assert j.mandate()["status"] == "active"
    with j.app.state.store.transaction() as s:
        assert s["threads"][ref]["_pendingIntent"] == "pay"
        assert s["audit"][-1]["kind"] == "pending_resume_deferred"
    assert not j.ok("GET", "/payments")
