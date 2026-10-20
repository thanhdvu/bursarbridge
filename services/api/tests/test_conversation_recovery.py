"""Same-thread recovery and the frontend's public contract, through real HTTP handlers."""

import json
from decimal import Decimal


def exchange(j, thread, text, docs=()):
    r = j.request(
        "POST",
        f"/agent/threads/{thread}/messages",
        "student_linh",
        json={"text": text, "documentIds": list(docs), "locale": "vi"},
    )
    assert r.status_code == 200, r.text
    events = [json.loads(line[6:]) for line in r.text.splitlines() if line.startswith("data: ")]
    assert not any(e["type"] == "error" for e in events), events
    return [e for e in events if e["type"] == "card"]


def test_single_thread_request_documents_scam_payment_refusal_refund(journey):
    j = journey
    thread = j.ok("POST", "/agent/threads", "student_linh")["threadId"]
    cards = exchange(j, thread, "ba ơi chuyển tiền học kỳ 1 cho con nha")
    needs = next(c["data"] for c in cards if c["kind"] == "needs")
    assert {m["kind"] for m in needs["missing"]} == {"mandate", "admission", "invoice"}
    assert not any(c["kind"] == "blocked" for c in cards)
    assert next(m for m in needs["missing"] if m["kind"] == "mandate")["actorId"] == "usr_parent_minh"
    j.mandate()
    admission, invoice = j.upload("admission"), j.upload("invoice")
    cards = exchange(j, thread, "giấy tờ đây nè", [admission["id"], invoice["id"]])
    approval = next(c["data"] for c in cards if c["kind"] == "approval_required")
    assert approval["approverId"] == "usr_parent_minh"
    assert sum(Decimal(line["amount"]["amount"]) for line in approval["invoice"]["lines"]) == Decimal(
        "7174000"
    )
    assert approval["expiresAt"] == "2027-01-13T03:00:00Z"
    fake = j.upload("fake_invoice")
    cards = exchange(j, thread, "giấy tờ đây nè", [fake["id"]])
    blocked = next(c["data"] for c in cards if c["kind"] == "blocked")
    assert {r["code"] for r in blocked["reasons"]} >= {
        "TAINTED_PARAMETERS",
        "PAYEE_UNVERIFIED",
        "UNTRUSTED_INSTRUCTIONS",
    }
    assert blocked["attempted"]["account"] == "MOCK-ATTACKER-9912"
    assert blocked["attempted"]["source"]["filename"] == "fake_invoice.pdf"
    cards = exchange(j, thread, "học phí bao nhiêu vậy, hạn khi nào?")
    assert not any(c["kind"] == "blocked" for c in cards)
    approved = j.approve(approval)
    payment = j.ok("GET", "/payments")[0]
    assert approved["resultRef"] == payment["id"]
    assert all(payment[k] for k in ("purpose", "fees", "createdAt", "cancelUntil"))
    j.ok("POST", "/clock/advance", "judge", json={"hours": 1})
    refusal = j.upload("refusal")
    cards = exchange(j, thread, "giấy tờ đây nè", [refusal["id"]])
    claim = next(c["data"] for c in cards if c["kind"] == "approval_required")
    assert claim["rawAction"]["refundAmount"] == payment["receive"]
    assert claim["approverId"] == "usr_student_linh"
    agent = j.upload("refund_agent")
    assert any(c["kind"] == "blocked" for c in exchange(j, thread, "forwarded", [agent["id"]]))
    assert not any(c["kind"] == "blocked" for c in exchange(j, thread, "học phí bao nhiêu?"))
    signed = j.approve(claim, "student_linh")
    refund = j.ok("GET", "/refunds")[0]
    assert signed["resultRef"] == refund["id"]
    assert refund["destination"]["id"] == "acct_parent_minh"
    # Explicit reuse of the malicious document remains denied.
    assert any(c["kind"] == "blocked" for c in exchange(j, thread, "pay tuition", [fake["id"]]))


def test_document_list_preserves_role_and_family_privacy_and_frozen(journey):
    j = journey
    student = j.upload("invoice")
    parent = j.upload("invoice", "parent_minh")
    assert {d["id"] for d in j.ok("GET", "/documents", "student_linh")} == {student["id"]}
    assert {d["id"] for d in j.ok("GET", "/documents")} == {student["id"], parent["id"]}
    assert j.ok("GET", "/documents", "parent_wang") == []
    assert j.ok("GET", "/me")["frozen"] is False
    j.ok("POST", "/freeze")
    assert j.ok("GET", "/me", "student_linh")["frozen"] is True


def test_family_event_resume_header_and_query(journey):
    import asyncio

    from bursarbridge.engine import event

    j = journey
    with j.app.state.store.transaction() as state:
        event(state, "fam_minh", "blocked", {"marker": "old"})
        event(state, "fam_wang", "blocked", {"marker": "private"})
        event(state, "fam_minh", "payment_updated", {"marker": "new"})
    endpoint = next(r.endpoint for r in j.app.routes if r.path == "/api/events")

    class Request:
        async def is_disconnected(self):
            return False

    async def first(header, after=None):
        response = await endpoint(Request(), key="student_linh", last_event_id=header, after=after)
        stream = response.body_iterator
        data = await anext(stream)
        await stream.aclose()
        return data

    for header, after in [("1", None), ("0", 1), ("999", 1)]:
        data = asyncio.run(first(header, after))
        assert "id: 3\n" in data and '"new"' in data
        assert '"old"' not in data and '"private"' not in data
    assert asyncio.run(first("3")) == ": heartbeat\n\n"
