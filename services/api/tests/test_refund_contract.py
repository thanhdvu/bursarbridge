"""Calendar entitlement, consent paperwork and factual quotation regressions."""

import json
from decimal import Decimal
from io import BytesIO

from pypdf import PdfReader

from bursarbridge.engine import dt
from bursarbridge.security import digest


def claim(j):
    j.pay()
    denial = j.upload("refusal")
    j.chat("Visa refused", [denial["id"]])
    return j.ok("GET", "/approvals")[0]


def test_refund_waits_for_semester_promise_and_signs_both_forms(journey):
    j = journey
    approval = claim(j)
    packet = approval["rawAction"]["paperwork"]
    assert packet["deadline"] == "2027-03-16T00:00:00Z"
    assert packet["destination"]["accountId"] == "acct_parent_minh"
    assert packet["destination"]["swift"] == "LOTUVNVX"
    assert digest(approval["rawAction"]) == approval["consentHash"]
    for kind in ("admission_withdrawal", "tuition_refund_application"):
        path = f"/approvals/{approval['id']}/paperwork/{kind}"
        response = j.request("GET", path, "student_linh")
        assert response.status_code == 200
        text = PdfReader(BytesIO(response.content)).pages[0].extract_text()
        assert approval["consentHash"] in text and "LOTUVNVX" in text
        assert j.request("GET", path, "parent_wang").status_code == 404
    j.approve(approval, "student_linh")
    balance = j.ok("GET", "/me")["accounts"][0]["balance"]
    j.ok("POST", "/clock/advance", "judge", json={"days": 28})
    refund = j.ok("GET", "/refunds")[0]
    assert refund["status"] == "approved" and refund["reconciliation"] is None
    assert refund["estimate"]["kind"] == "MOCK_ESTIMATE"
    assert refund["estimate"]["receivedBack"]["amount"] == "132551176.98"
    estimate = refund["estimate"]
    assert refund["destination"]["balance"] == balance
    assert j.ok("GET", "/me")["accounts"][0]["balance"] == balance
    assert not any(e["code"] == "refund_deadline_breach" for e in refund["timeline"])
    assert all(f["status"] == "signed" for f in refund["paperwork"]["documents"][:2])
    j.advance_refund()
    settled = j.ok("GET", "/refunds")[0]
    assert settled["status"] == "reconciled"
    assert settled["estimate"] is None
    assert settled["reconciliation"]["receivedBack"] == estimate["receivedBack"]
    assert settled["reconciliation"]["lines"] == estimate["lines"]
    current = j.ok("GET", "/me")["accounts"][0]["balance"]
    assert settled["destination"]["balance"] == current != balance
    assert j.ok("GET", "/refunds/" + settled["id"])["destination"]["balance"] == current
    receipt = next(e for e in settled["timeline"] if e["code"] == "refund_received")
    assert dt(receipt["at"]) >= dt(settled["classesStart"])
    assert dt(receipt["at"]) <= dt(settled["deadline"])


def test_after_start_degree_claim_never_borrows_language_table_or_credits(journey):
    j = journey
    j.pay()
    j.ok("POST", "/clock/advance", "judge", json={"days": 138})
    doc = j.upload("refusal")
    j.chat("Visa refused", [doc["id"]])
    approval = j.ok("GET", "/approvals")[0]
    assert approval["rawAction"]["paperwork"]["eligibility"] == "manual_degree_assessment"
    j.approve(approval, "student_linh")
    balance = j.ok("GET", "/me")["accounts"][0]["balance"]
    j.ok("POST", "/clock/advance", "judge", json={"days": 31})
    refund = j.ok("GET", "/refunds")[0]
    assert refund["status"] == "manual_review" and refund["deadline"] is None
    assert refund["reconciliation"] is None and refund["estimate"] is None
    assert j.ok("GET", "/me")["accounts"][0]["balance"] == balance


def test_total_and_signed_instalments_have_matching_full_vnd_quote(journey):
    j = journey
    j.upload("admission")
    j.upload("invoice")
    events = j.chat("tổng bao nhiêu vậy, chia mấy đợt?", locale="vi")
    text = next(e["text"] for e in events if e["type"] == "token")
    assert "7.174.000 KRW" in text and "135.663.956 VND" in text
    assert "3.587.000 KRW + 3.587.000 KRW" in text and "MOCK" in text
    assert "84.671.725" not in text and ".36 VND" not in text
    quote = next(e["data"] for e in events if e.get("kind") == "quote")
    assert Decimal(quote["send"]["amount"]) > Decimal("130000000")
    assert quote["receive"]["amount"] == "7174000.00"
    with j.app.state.store.transaction() as s:
        assert s["rules"]["corridors"]["VN→AU"]["refundDays"] == 28
        assert "refundDays" not in s["rules"]["corridors"]["VN→KR"]


def test_draft_crossing_classes_start_needs_fresh_assessment_and_consent(journey):
    j = journey
    j.pay()
    with j.app.state.store.transaction() as s:
        s["now"] = "2027-03-01T23:30:00Z"
    denial = j.upload("refusal")
    j.chat("Visa refused", [denial["id"]])
    old = j.ok("GET", "/approvals")[0]
    j.ok("POST", "/clock/advance", "judge", json={"hours": 1})
    response = j.request(
        "POST", f"/approvals/{old['id']}/approve", "student_linh", json={"assertion": {"demo": True}}
    )
    assert response.status_code == 409 and response.json()["error"]["code"] == "REFUND_POLICY_CHANGED"
    assert j.ok("GET", "/refunds") == []
    j.chat("Visa refused", [denial["id"]])
    new = j.ok("GET", "/approvals")[0]
    assert new["id"] != old["id"] and new["consentHash"] != old["consentHash"]
    assert new["rawAction"]["paperwork"]["eligibility"] == "manual_degree_assessment"
    historical = j.ok("GET", f"/approvals/{old['id']}")
    assert historical["status"] == "rejected" and historical["consentHash"] == old["consentHash"]


def test_legacy_open_refund_is_not_silently_repriced(journey):
    j = journey
    approval = claim(j)
    j.approve(approval, "student_linh")
    with j.app.state.store.transaction() as s:
        next(iter(s["refunds"].values())).pop("policy")
    balance = j.ok("GET", "/me")["accounts"][0]["balance"]
    j.advance_refund()
    assert j.ok("GET", "/me")["accounts"][0]["balance"] == balance
    assert j.ok("GET", "/refunds")[0]["status"] == "requested"
    assert j.ok("GET", "/refunds")[0]["estimate"] is None


def test_filed_refund_questions_read_same_case_and_never_repeat_consent(journey):
    j = journey
    approval = claim(j)
    with j.app.state.store.transaction() as s:
        thread = next(
            ref for ref, row in s["threads"].items() if row.get("_lastFacts", {}).get("reason") == "refund"
        )
    j.approve(approval, "student_linh")
    original = j.ok("GET", "/refunds")[0]
    balance = j.ok("GET", "/me")["accounts"][0]["balance"]
    for text, expected in [
        ("trường hẹn khi nào, phí gì bị trừ vậy?", "16/03/2027"),
        ("vậy ba nhận lại bao nhiêu?", "132.551.177 VND"),
    ]:
        response = j.request(
            "POST", f"/agent/threads/{thread}/messages", "student_linh", json={"text": text, "locale": "vi"}
        )
        events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
        assert not any(e["type"] == "error" or e.get("kind") == "approval_required" for e in events)
        assert expected in next(e["text"] for e in events if e["type"] == "token")
        assert j.ok("GET", "/refunds")[0]["id"] == original["id"]
        assert j.ok("GET", "/approvals") == []
        assert j.ok("GET", "/me")["accounts"][0]["balance"] == balance
    assert j.ok("GET", "/approvals/" + approval["id"])["consentHash"] == approval["consentHash"]


def test_parent_incoming_tuition_question_reads_existing_refund(journey):
    j = journey
    approval = claim(j)
    j.approve(approval, "student_linh")
    original = j.ok("GET", "/refunds")[0]
    for text in ("khi nào tiền học phí của con về, bị trừ bao nhiêu?", "tiền hoàn khi nào về?"):
        events = j.chat(text, persona="parent_minh", locale="vi")
        cards = [e for e in events if e.get("kind") == "refund"]
        assert len(cards) == 1 and cards[0]["data"]["id"] == original["id"]
        assert cards[0]["data"]["estimate"]["receivedBack"] == original["estimate"]["receivedBack"]
        assert not any(e.get("kind") in {"quote", "pack", "approval_required"} for e in events)
        reply = next(e["text"] for e in events if e["type"] == "token")
        assert "bạn" not in reply.casefold()
    assert len(j.ok("GET", "/refunds")) == 1
    assert len(j.ok("GET", "/approvals?status=all")) == 2


def test_tranche_deadlines_follow_signed_schedule(journey):
    from bursarbridge.engine import resolve_invoice_action

    j = journey
    with j.app.state.store.transaction() as s:
        invoice = j.app.state.issuer.verify(
            s["credentials"]["fam_minh"]["jwt"], int(dt(s["now"]).timestamp())
        )
        first = resolve_invoice_action(s, invoice, instalment=True)
        assert first["dueAt"] == "2027-01-15T08:00:00Z"
        s["invoicePaid"][invoice["invoiceRef"]] = first["amount"]
        second = resolve_invoice_action(s, invoice, instalment=True)
        assert second["dueAt"] == "2027-02-15T08:00:00Z"
        assert second["amount"] == first["amount"] == "3587000.00"
        assert resolve_invoice_action(s, invoice)["dueAt"] == second["dueAt"]
