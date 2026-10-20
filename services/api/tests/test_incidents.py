"""One non-executable incident per reported encounter, not per support question."""

import json

import pytest

from bursarbridge.conversation import Proposal
from bursarbridge.providers import Provider


def thread(j):
    return j.ok("POST", "/agent/threads", "student_linh")["threadId"]


def say(j, ref, text, docs=()):
    response = j.request(
        "POST",
        f"/agent/threads/{ref}/messages",
        "student_linh",
        json={"text": text, "documentIds": list(docs), "locale": "vi"},
    )
    assert response.status_code == 200
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    assert not any(e["type"] == "error" for e in events), events
    return events


def reviews(j):
    return [a for a in j.ok("GET", "/approvals?status=all") if a["rawAction"].get("verificationRequired")]


def test_hosted_reclassification_cannot_duplicate_incident_or_cosign(journey, monkeypatch):
    j, original = journey, Provider.propose

    def always_scam(self, history, locale, fallback):
        if fallback.intent == "scam_followup":
            return Proposal(intent="scam", scope="remaining", needsClarification=False)
        return original(self, history, locale, fallback)

    monkeypatch.setattr(Provider, "propose", always_scam)
    ref = thread(j)
    say(j, ref, "công an gọi nói e dính vụ rửa tiền, bắt chuyển 50 triệu vô tk an toàn, e sợ quá")
    case = reviews(j)[0]
    j.ok("POST", f"/approvals/{case['id']}/cosign", "mother_lan", json={"assertion": {"demo": True}})
    signed = reviews(j)[0]
    for text in (
        "giờ e phải làm gì",
        "em vẫn sợ quá",
        "công an gọi nữa thì sao?",
        "nếu có người khác gọi thì sao?",
        "ba ơi giúp con với",
        "cần nhờ Lan kiểm tra lại không?",
    ):
        events = say(j, ref, text)
        assert not any(e.get("kind") == "approval_required" for e in events)
        card = next(e for e in events if e.get("kind") == "info")
        assert card["data"]["approvalId"] == case["id"]
        assert card["data"]["cosigned"]
    assert reviews(j) == [signed]
    with j.app.state.store.transaction() as s:
        assert s["denials"]["fam_minh"] == 1
        assert not s["frozen"].get("fam_minh")
        assert sum(e["type"] == "approval_created" for e in s["events"]) == 1
        assert sum(e["kind"] == "scam_cooling_started" for e in s["audit"]) == 1
    assert j.ok("GET", "/payments") == []
    assert (
        j.request("POST", f"/approvals/{case['id']}/approve", json={"assertion": {"demo": True}}).status_code
        == 403
    )


def test_new_report_opens_distinct_case_repeated_evidence_does_not(journey):
    j = journey
    ref = thread(j)
    doc = j.upload("police")
    say(j, ref, "police called and demanded a safe-account deposit", [doc["id"]])
    first = reviews(j)[0]
    say(j, ref, "gửi lại tin nhắn họ gửi", [doc["id"]])
    assert reviews(j) == [first]
    j.ok("POST", "/clock/advance", "judge", json={"hours": 1})
    say(j, ref, "Một người khác tự xưng công an vừa gọi bắt chuyển tiền")
    current = reviews(j)
    assert len(current) == 2 and next(c for c in current if c["id"] == first["id"]) == first
    newer = next(c for c in current if c["id"] != first["id"])
    assert newer["consentHash"] != first["consentHash"]
    events = say(j, ref, "em nên nói với ai bây giờ?")
    assert next(e["data"] for e in events if e.get("kind") == "info")["approvalId"] == newer["id"]


def test_closed_case_support_does_not_reopen_or_reset_deadline(journey):
    j, ref = journey, thread(journey)
    say(j, ref, "police proof-of-funds deposit")
    case = reviews(j)[0]
    j.ok("POST", f"/approvals/{case['id']}/reject")
    say(j, ref, "what should I do now?")
    closed = reviews(j)
    assert len(closed) == 1 and closed[0]["status"] == "rejected"
    assert closed[0]["cooling"] == case["cooling"] and closed[0]["consentHash"] == case["consentHash"]


def test_normal_topics_and_other_never_requests_are_not_absorbed(journey, monkeypatch):
    j, ref = journey, thread(journey)
    say(j, ref, "police proof-of-funds deposit")
    monkeypatch.setattr(
        Provider, "propose", lambda *a: Proposal(intent="scam", scope="remaining", needsClarification=False)
    )
    events = say(j, ref, "học phí bao nhiêu, hạn khi nào?")
    assert any(e.get("kind") == "quote" for e in events)
    assert len(reviews(j)) == 1
    events = say(j, ref, "bỏ tiền học vào crypto đi")
    assert any(e.get("kind") == "blocked" for e in events)
    with j.app.state.store.transaction() as s:
        assert s["denials"]["fam_minh"] == 2
    assert len(reviews(j)) == 1


def test_case_references_are_thread_bound_and_legacy_cards_can_recover(journey):
    j = journey
    a, b = thread(j), thread(j)
    say(j, a, "police proof-of-funds deposit")
    first = reviews(j)[0]
    say(j, b, "police proof-of-funds deposit")
    second = reviews(j)[1]
    with j.app.state.store.transaction() as s:
        s["threads"][b]["_scamReviewId"] = first["id"]
        s["approvals"][second["id"]].pop("_threadId")
    events = say(j, b, "what now?")
    assert next(e["data"] for e in events if e.get("kind") == "info")["approvalId"] == second["id"]
    assert len(reviews(j)) == 2


@pytest.mark.parametrize(
    "text",
    [
        "Another police caller contacted me and demanded a deposit",
        "Một người khác gọi tự xưng công an đòi tiền",
        "另一个警察打电话要求转账",
        "다른 사람이 경찰이라며 전화해서 송금을 요구했어요",
    ],
)
def test_distinct_reports_are_language_independent(text):
    from bursarbridge.incidents import separate_report

    assert separate_report(text)


@pytest.mark.parametrize(
    "text",
    [
        "Lỡ người khác gọi tự xưng công an thì sao?",
        "Suppose another police caller contacted me?",
        "万一另一个警察打电话要求转账呢？",
        "다른 사람이 전화하면 어떻게 하죠?",
    ],
)
def test_conditional_contact_is_not_a_new_report(text):
    from bursarbridge.incidents import separate_report

    assert not separate_report(text)
