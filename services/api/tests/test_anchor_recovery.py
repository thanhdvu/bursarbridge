"""Transient anchoring never freezes a family; unavailable chains still gate banks."""

import json
import time

import pytest

from bursarbridge.engine import DomainError, bank_execute
from bursarbridge.providers import Provider


@pytest.mark.parametrize(
    "error", [DomainError("CHAIN_UNAVAILABLE", "probe", 503), RuntimeError("secret body")]
)
def test_anchor_failure_is_audited_backed_off_and_catches_up(journey, monkeypatch, error):
    j, chain = journey, journey.app.state.chain
    j.ok("POST", "/clock/advance", "judge", json={"hours": 1})
    original = chain.anchor
    calls = []

    def intermittent(s):
        calls.append(True)
        if len(calls) == 1:
            raise error
        return original(s)

    monkeypatch.setattr(chain, "anchor", intermittent)
    j.app.state.anchor_due()
    j.app.state.anchor_due()
    assert len(calls) == 1
    for persona in ("parent_minh", "parent_wang"):
        assert j.ok("GET", "/me", persona)["frozen"] is False
    with j.app.state.store.transaction() as s:
        deferred = next(e for e in s["audit"] if e["kind"] == "anchor_deferred")
        assert "secret body" not in json.dumps(deferred)
        assert sum(e["type"] == "anchor_updated" for e in s["events"]) >= 2
        assert not any(s["frozen"].values())
    monotonic = time.monotonic
    with monkeypatch.context() as clock:
        clock.setattr(time, "monotonic", lambda: monotonic() + 61)
        j.app.state.anchor_due()
    assert j.ok("POST", "/audit/verify", "judge")["ok"]
    with j.app.state.store.transaction() as s:
        assert not s.get("anchorDeferred")
        assert s["anchors"][-1]["lastSeq"] >= deferred["seq"]
        assert any(e["kind"] == "anchor_recovered" for e in s["audit"])


def test_outage_cannot_debit_or_consume_approval_and_does_not_freeze_others(journey, monkeypatch):
    j = journey
    j.prepare()
    approval = j.ok("GET", "/approvals")[0]
    before = j.ok("GET", "/me")
    monkeypatch.setattr(j.app.state.chain, "available", lambda: False)
    response = j.request("POST", f"/approvals/{approval['id']}/approve", json={"assertion": {"demo": True}})
    assert response.status_code == 503 and response.json()["error"]["code"] == "CHAIN_UNAVAILABLE"
    assert j.ok("GET", "/me") == before
    assert j.ok("GET", "/payments") == []
    assert j.ok("GET", f"/approvals/{approval['id']}")["status"] == "pending"
    with j.app.state.store.transaction() as s:
        with pytest.raises(DomainError) as failed:
            bank_execute(s, s["approvals"][approval["id"]], j.app.state.issuer)
        assert failed.value.code == "CHAIN_UNAVAILABLE"
    events = j.chat("pay tuition")
    assert any(e.get("kind") == "needs" for e in events)
    assert not any(e["type"] == "error" for e in j.chat("ba gửi con tiền tiêu vặt"))
    assert not j.ok("GET", "/me", "parent_wang")["frozen"]


@pytest.mark.parametrize(
    "kind,reason",
    [("manual", "USER_REQUESTED"), ("denials", "DENIAL_CIRCUIT_BREAKER")],
)
def test_all_freezes_have_reason_audit_and_family_event(journey, monkeypatch, kind, reason):
    j = journey
    if kind == "manual":
        j.ok("POST", "/freeze")
    elif kind == "llm":

        def unavailable(*args):
            raise TimeoutError()

        monkeypatch.setattr(Provider, "propose", unavailable)
        j.chat("pay tuition")
    else:
        for _ in range(5):
            j.chat("invest tuition in crypto")
    assert j.ok("GET", "/me")["frozenReason"] == reason
    with j.app.state.store.transaction() as s:
        assert any(e["kind"] == "freeze" and e["reason"] == reason for e in s["audit"])
        event = next(e for e in reversed(s["events"]) if e["type"] == "freeze")
        assert event["_family"] == "fam_minh" and event["data"]["reason"] == reason
        assert event["data"]["recovery"] == "parent_passkey_unfreeze"
    assert not j.ok("GET", "/me", "parent_wang")["frozen"]
    j.ok("POST", "/unfreeze", json={"assertion": {"demo": True}})
    assert j.ok("GET", "/me")["frozenReason"] is None


def test_continuation_speaks_to_requester_not_to_signer(journey):
    j = journey
    ref = j.ok("POST", "/agent/threads", "student_linh")["threadId"]
    j.request(
        "POST",
        f"/agent/threads/{ref}/messages",
        "student_linh",
        json={"text": "đóng học phí giùm con", "locale": "vi"},
    )
    j.upload("admission")
    j.upload("invoice")
    j.mandate()
    with j.app.state.store.transaction() as s:
        thread = s["threads"][ref]
        assert thread["_lastFacts"]["readerRole"] == "student"
        assert thread["_lastFacts"]["readerName"] == "Linh"
        assert "Ba của Linh có thể" in thread["messages"][-1]["text"]
    assert j.ok("GET", "/health")["screeningMode"] == "synthetic"


def test_pending_tuition_resumes_when_chain_recovers_without_unfreeze(journey, monkeypatch):
    j = journey
    j.mandate()
    j.upload("admission")
    j.upload("invoice")
    connected = [False]
    monkeypatch.setattr(j.app.state.chain, "available", lambda: connected[0])
    events = j.chat("pay tuition")
    assert any(e.get("kind") == "needs" for e in events)
    assert j.ok("GET", "/approvals") == []
    connected[0] = True
    j.app.state.anchor_due()
    assert len(j.ok("GET", "/approvals")) == 1
    assert not j.ok("GET", "/me")["frozen"]
    assert j.ok("GET", "/payments") == []


def test_refusal_conversation_continues_offline_but_claim_signature_waits(journey, monkeypatch):
    j = journey
    j.prepare()
    j.approve(j.ok("GET", "/approvals")[0])
    j.ok("POST", "/clock/advance", "judge", json={"hours": 1})
    before = j.ok("GET", "/payments")
    monkeypatch.setattr(j.app.state.chain, "available", lambda: False)
    refusal = j.upload("refusal")
    events = j.chat("visa refused", [refusal["id"]])
    assert not any(e["type"] == "error" for e in events)
    assert any(e.get("kind") == "approval_required" for e in events)
    claim = j.ok("GET", "/approvals")[0]
    response = j.request(
        "POST", f"/approvals/{claim['id']}/approve", "student_linh", json={"assertion": {"demo": True}}
    )
    assert response.status_code == 503
    assert not j.ok("GET", "/me", "student_linh")["frozen"]
    assert j.ok("GET", "/payments") == before and j.ok("GET", "/refunds") == []
