"""Refusal before payment, safe dialogue failures, and non-blocking Reset recovery."""

import json
import threading
import time

import pytest
from web3.exceptions import TimeExhausted

from bursarbridge.chain import Chain
from bursarbridge.engine import DomainError, bank_execute, verified_invoice


def login_again(j):
    for persona in list(j.headers):
        r = j.client.post("/api/session", json={"persona": persona})
        assert r.status_code == 200
        j.headers[persona] = {"Authorization": "Bearer " + r.json()["token"]}


def test_unpaid_refusal_stops_other_threads_and_informs_parent(journey):
    j = journey
    j.upload("admission")
    j.upload("invoice")
    j.chat("pay tuition")
    refusal = j.upload("refusal")
    events = j.chat("visa e bị từ chối rồi :(", [refusal["id"]], locale="vi")
    assert not any(e["type"] == "error" for e in events)
    text = next(e["text"] for e in events if e["type"] == "token")
    assert "chưa chuyển" in text and "ba" in text and "kỳ sau" in text
    assert j.ok("GET", "/refunds") == j.ok("GET", "/payments") == []
    notice = j.ok("GET", "/me")["admissionDisposition"]
    assert notice["tuitionStopped"] and not notice["refundRequired"] and not notice["admissionWithdrawn"]
    assert notice["parentNotice"]["recipientIds"] == ["usr_parent_minh"]
    assert (
        j.client.post("/api/session", json={"persona": "parent_minh"}).json()["user"]["admissionDisposition"]
        == notice
    )
    assert not notice["parentNotice"]["externalMessageSent"]
    assert j.ok("GET", "/study-plan")["admissionDisposition"] == notice
    with j.app.state.store.transaction() as s:
        assert all(t.get("_pendingIntent") != "pay" for t in s["threads"].values())
        assert len([e for e in s["events"] if e["type"] == "admission_updated"]) == 1
    j.mandate()
    assert j.ok("GET", "/approvals") == []
    again = j.chat("pay tuition")
    assert any(e.get("data", {}).get("code") == "ADMISSION_RECONFIRMATION_REQUIRED" for e in again)
    j.chat("Visa refused", [refusal["id"]])
    with j.app.state.store.transaction() as s:
        assert len([e for e in s["events"] if e["type"] == "admission_updated"]) == 1
    assert j.ok("GET", "/me", "parent_wang")["admissionDisposition"] is None
    parent = j.chat("visa của con bị từ chối thì sao?", persona="parent_minh", locale="vi")
    assert not any(e["type"] == "error" for e in parent)


def test_pending_approval_and_bank_boundary_are_cancelled_after_refusal(journey):
    j = journey
    j.prepare()
    old = j.ok("GET", "/approvals")[0]
    doc = j.upload("refusal")
    # Block the upload-to-chat race as soon as clean refusal evidence exists.
    with j.app.state.store.transaction() as s:
        with pytest.raises(DomainError, match="Visa refused"):
            bank_execute(s, s["approvals"][old["id"]], j.app.state.issuer)
    j.chat("Visa refused", [doc["id"]])
    row = j.ok("GET", "/approvals/" + old["id"])
    assert row["status"] == "rejected" and row["consentHash"] == old["consentHash"]
    assert (
        j.request(
            "POST", "/approvals/" + old["id"] + "/approve", json={"assertion": {"demo": True}}
        ).status_code
        != 200
    )
    with j.app.state.store.transaction() as s:
        forged = s["approvals"][old["id"]]
        forged["status"] = "pending"
        with pytest.raises(DomainError, match="Visa refused"):
            bank_execute(s, forged, j.app.state.issuer)
        forged["status"] = "rejected"
    assert not j.ok("GET", "/payments")


@pytest.mark.parametrize(
    "code,status", [("FROZEN", 403), ("CREDENTIAL_REVOKED", 403), ("REFUND_FORM_REQUIRES_REVIEW", 409)]
)
def test_domain_refusals_are_saved_words_not_stream_errors(journey, monkeypatch, code, status):
    from bursarbridge import agent

    j = journey
    j.pay()
    doc = j.upload("refusal")

    def refuse(*args):
        raise DomainError(code, "INTERNAL RAW DETAIL MUST NOT LEAK", status)

    monkeypatch.setattr(agent, "prepare_refund", refuse)
    events = j.chat("Visa refused", [doc["id"]])
    assert not any(e["type"] == "error" for e in events)
    assert any(e["type"] == "done" for e in events)
    token = next(e for e in events if e["type"] == "token")
    assert token["source"] == "scripted_domain" and token["text"]
    assert "INTERNAL RAW" not in json.dumps(events)
    assert not j.ok("GET", "/refunds")


def test_reset_is_local_receipt_timeout_retries_and_bank_waits(journey, monkeypatch):
    j = journey
    chain = j.app.state.chain
    monkeypatch.setattr(chain, "mode", "fisco")
    calls = []

    def slow(s):
        calls.append(True)
        raise TimeExhausted("PRIVATE TRANSACTION DETAIL")

    monkeypatch.setattr(chain, "register", slow)
    monkeypatch.setattr(chain, "available", lambda: True)
    monkeypatch.setattr(chain, "anchor", Chain("local").anchor)
    result = j.ok("POST", "/demo/reset", "judge")
    assert result["registrationStatus"] == "pending" and not calls
    login_again(j)
    j.app.state.anchor_due()
    assert len(calls) == 1 and not j.ok("GET", "/me")["frozen"]
    with j.app.state.store.transaction() as s:
        with pytest.raises(DomainError) as failed:
            verified_invoice(s, "fam_minh", j.app.state.issuer)
        assert failed.value.code == "CHAIN_REGISTRATION_PENDING"
        assert "PRIVATE TRANSACTION DETAIL" not in json.dumps(s)
    monkeypatch.setattr(chain, "register", lambda s: None)
    # Manual anchoring must not strand registry recovery when no audit entries remain.
    j.ok("POST", "/chain/anchor", "judge")
    monotonic = time.monotonic
    with monkeypatch.context() as clock:
        clock.setattr(time, "monotonic", lambda: monotonic() + 61)
        j.app.state.anchor_due()
    assert j.ok("GET", "/chain/status")["registrationStatus"] == "ready"
    assert j.ok("POST", "/audit/verify", "judge")["ok"]


def test_reset_during_inflight_chain_io_rejects_old_generation_receipt(journey, monkeypatch):
    j = journey
    chain = j.app.state.chain
    monkeypatch.setattr(chain, "mode", "fisco")
    entered, release = threading.Event(), threading.Event()

    def wait(s):
        entered.set()
        assert release.wait(5)

    monkeypatch.setattr(chain, "register", wait)
    monkeypatch.setattr(chain, "anchor", Chain("local").anchor)
    j.ok("POST", "/demo/reset", "judge")
    login_again(j)
    worker = threading.Thread(target=j.app.state.anchor_due)
    worker.start()
    try:
        assert entered.wait(2)
        # No ledger lock is held by chain I/O; Reset can retire its generation.
        before = time.perf_counter()
        result = j.ok("POST", "/demo/reset", "judge")
        assert result["ok"] and time.perf_counter() - before < 2
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive()
    with j.app.state.store.transaction() as s:
        assert s["registrationPending"] and not s["anchors"]
