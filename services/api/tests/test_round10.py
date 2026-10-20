"""The panic button stops outgoing holds, preserves authority and lets refunds return."""

import copy
from decimal import Decimal

import pytest


def claim(j):
    doc = j.upload("refusal")
    j.chat("Visa refused", [doc["id"]])
    a = j.ok("GET", "/approvals")[0]
    j.approve(a, "student_linh")
    return j.ok("GET", "/refunds")[0]


@pytest.mark.parametrize("actor", ["parent_minh", "student_linh"])
def test_freeze_cancels_held_payment_and_restores_limit_without_resend(journey, actor):
    j = journey
    original_balance = j.ok("GET", "/me")["accounts"][0]["balance"]
    p = j.pay(settle=False)
    original_mandate = j.ok("GET", "/mandates")[0]
    frozen = j.ok("POST", "/freeze", actor)
    assert frozen["cancelledPayments"] == 1 and not frozen["incomingRefundsPaused"]
    assert j.ok("GET", "/payments")[0]["status"] == "cancelled"
    assert j.ok("GET", "/me")["accounts"][0]["balance"] == original_balance
    assert j.ok("GET", "/mandates")[0]["spent"]["amount"] == "0.00"
    assert j.ok("POST", "/freeze", actor)["cancelledPayments"] == 0
    j.ok("POST", "/clock/advance", "judge", json={"hours": 1})
    assert j.ok("GET", "/payments")[0]["status"] == "cancelled"
    thaw = j.ok("POST", "/unfreeze", json={"assertion": {"demo": True}})
    assert thaw["restoredMandates"] == 1
    restored = j.ok("GET", "/mandates")[0]
    for field in ("id", "hash", "cap", "payeeRule", "expiresAt", "chainTx"):
        assert restored[field] == original_mandate[field]
    assert restored["status"] == "active" and restored["spent"]["amount"] == "0.00"
    assert len(j.ok("GET", "/payments")) == 1
    assert j.ok("GET", "/payments")[0]["id"] == p["id"]
    assert not j.ok("GET", "/me", "parent_wang")["frozen"]


def test_pending_outbound_is_paused_not_rejected_and_resumes_exact_consent(journey):
    j = journey
    j.prepare()
    a = j.ok("GET", "/approvals")[0]
    j.ok("POST", "/freeze")
    assert j.ok("GET", "/approvals")[0]["consentHash"] == a["consentHash"]
    assert (
        j.request(
            "POST", "/approvals/" + a["id"] + "/approve", json={"assertion": {"demo": True}}
        ).status_code
        == 403
    )
    j.ok("POST", "/unfreeze", json={"assertion": {"demo": True}})
    j.approve(a)
    assert j.ok("GET", "/payments")[0]["status"] == "sent"


def test_refund_forms_and_incoming_credit_continue_during_freeze(journey):
    j = journey
    j.pay()
    j.ok("POST", "/freeze")
    r = claim(j)
    before = Decimal(j.ok("GET", "/me")["accounts"][0]["balance"]["amount"])
    j.advance_refund()
    r = j.ok("GET", "/refunds")[0]
    assert r["status"] == "reconciled"
    back = Decimal(r["reconciliation"]["receivedBack"]["amount"])
    assert Decimal(j.ok("GET", "/me")["accounts"][0]["balance"]["amount"]) == before + back
    assert r["destination"]["id"] == "acct_parent_minh"
    assert j.ok("GET", "/me")["frozen"]
    assert j.ok("GET", "/payments")[0]["status"] == "matched"


def test_unfreeze_never_revives_revoked_unsigned_or_expired_mandates(journey):
    j = journey
    j.mandate()
    live = j.ok("GET", "/mandates")[0]
    with j.app.state.store.transaction() as s:
        template = copy.deepcopy(s["mandates"][live["id"]])
        for ref, state in [("revoked", "revoked"), ("unsigned", "pending_signature")]:
            s["mandates"][ref] = {**copy.deepcopy(template), "id": ref, "status": state}
    j.ok("POST", "/freeze")
    with j.app.state.store.transaction() as s:
        s["mandates"][live["id"]]["expiresAt"] = s["now"]
    j.ok("POST", "/unfreeze", json={"assertion": {"demo": True}})
    rows = {r["id"]: r for r in j.ok("GET", "/mandates")}
    assert rows[live["id"]]["status"] == "expired"
    assert rows["revoked"]["status"] == "revoked"
    assert rows["unsigned"]["status"] == "pending_signature"


def test_rent_panic_cancel_is_not_replayed_by_clock_after_unfreeze(journey):
    j = journey
    j.upload("rental_agreement")
    m = j.ok(
        "POST",
        "/mandates",
        json={
            "purpose": "rent",
            "payeeRule": {"type": "name_checked", "payeeId": "payee_landlord"},
            "cap": {"amount": "900000.00", "currency": "KRW"},
            "period": "monthly",
            "expiresAt": "2027-06-01T00:00:00Z",
        },
    )
    j.ok("POST", "/mandates/" + m["id"] + "/sign", json={"assertion": {"demo": True}})
    j.chat("pay rent")
    j.ok("POST", "/freeze")
    j.ok("POST", "/unfreeze", json={"assertion": {"demo": True}})
    j.ok("POST", "/clock/advance", "judge", json={"hours": 1})
    assert len(j.ok("GET", "/payments")) == 1
    assert j.ok("GET", "/payments")[0]["status"] == "cancelled"
    j.chat("pay rent again")
    assert len(j.ok("GET", "/payments")) == 2


def test_cn_held_fx_quota_is_reversed_with_the_cancelled_payment(journey):
    from bursarbridge.engine import bank_execute, prepare_payment

    j = journey
    j.mandate(persona="parent_wang")
    j.upload("admission", "parent_wang")
    j.upload("invoice", "parent_wang")
    with j.app.state.store.transaction() as s:
        user = s["users"]["parent_wang"]
        approval, _ = prepare_payment(s, user, j.app.state.issuer)
        p = bank_execute(s, approval, j.app.state.issuer)
        before = s["fxPurchases"][-1]
        assert before["paymentId"] == p["id"] and not before.get("reversed")
    j.ok("POST", "/freeze", "parent_wang")
    with j.app.state.store.transaction() as s:
        assert s["fxPurchases"][-1]["reversed"]
    assert j.ok("GET", "/payments", "parent_wang")[0]["status"] == "cancelled"


def test_upgrade_repairs_an_old_frozen_family_with_a_cancellable_hold(journey):
    from bursarbridge.chain import Chain
    from bursarbridge.main import create_app

    j = journey
    j.pay(settle=False)
    with j.app.state.store.transaction() as s:
        s["frozen"]["fam_minh"] = True
        s.setdefault("frozenReasons", {})["fam_minh"] = "USER_REQUESTED"
    upgraded = create_app(
        str(j.app.state.store.engine.url), j.app.state.store.directory, True, Chain("local")
    )
    try:
        with upgraded.state.store.transaction() as s:
            assert next(iter(s["payments"].values()))["status"] == "cancelled"
            assert s["frozen"]["fam_minh"]
    finally:
        upgraded.state.store.engine.dispose()
