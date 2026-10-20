import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest

from bursarbridge.chain import Chain
from bursarbridge.main import create_app
from bursarbridge.policy import Context, evaluate
from bursarbridge.security import digest


@pytest.mark.parametrize(
    "context,result,rule",
    [
        (Context(trusted_agent=False), "DENY", "G-01"),
        (Context(action="refund_redirect"), "DENY", "LX-03"),
        (Context(frozen=True), "DENY", "G-02"),
        (Context(chain_available=False), "DENY", "G-02"),
        (Context(mandate_valid=False), "ESCALATE", "M-01"),
        (Context(payee_valid=False), "DENY", "P-01"),
        (Context(name_match="close_match"), "ESCALATE", "P-02"),
        (Context(provenance=("chat",)), "ESCALATE", "T-01"),
        (Context(amount=Decimal("NaN")), "DENY", "A-00"),
        (Context(amount=Decimal("-1")), "DENY", "A-00"),
        (Context(cap=Decimal("10")), "ESCALATE", "A-01"),
        (Context(invoice_remaining=Decimal("10")), "DENY", "R-VN-01"),
        (Context(structuring=True), "DENY", "R-CN-02"),
        (Context(documents_ready=False), "ESCALATE", "R-VN-02"),
        (Context(sanctions="unavailable"), "DENY", "S-01"),
        (Context(risk_score=5), "ESCALATE", "S-02"),
        (Context(), "ESCALATE", "L3-01"),
        (Context(first_payment=False), "AUTO_EXECUTE", "L2-01"),
    ],
)
def test_policy_order(context, result, rule):
    decision = evaluate(context)
    assert (decision.result, decision.rule) == (result, rule)


def test_auth_and_cross_family_boundaries(journey):
    j = journey
    assert j.client.get("/api/payments").status_code == 401
    j.prepare()
    a = j.ok("GET", "/approvals")[0]
    assert j.request("GET", "/approvals/" + a["id"], "parent_wang").status_code == 404
    assert (
        j.request(
            "POST", "/approvals/" + a["id"] + "/approve", "student_linh", json={"assertion": {"demo": True}}
        ).status_code
        == 403
    )
    for path in ("/demo/reset", "/clock/advance", "/demo/tamper", "/audit/verify"):
        assert j.request("POST", path, json={"seq": 1} if "tamper" in path else {}).status_code == 403
    assert not j.ok("GET", "/payments")


@pytest.mark.parametrize(
    "field,value",
    [
        ("amount", "1.00"),
        ("payeeAccountHash", "f" * 64),
        ("payerId", "attacker"),
        ("fxRate", "99"),
        ("currency", "CNY"),
    ],
)
def test_changed_consent_cannot_execute(journey, field, value):
    j = journey
    j.prepare()
    a = j.ok("GET", "/approvals")[0]
    with j.app.state.store.transaction() as s:
        s["approvals"][a["id"]]["rawAction"][field] = value
    response = j.request("POST", "/approvals/" + a["id"] + "/approve", json={"assertion": {"demo": True}})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CONSENT_MISMATCH"
    assert not j.ok("GET", "/payments")


def test_bank_rederives_changed_action_even_with_matching_hash(journey):
    j = journey
    j.prepare()
    a = j.ok("GET", "/approvals")[0]
    with j.app.state.store.transaction() as s:
        row = s["approvals"][a["id"]]
        row["rawAction"]["payeeAccountHash"] = "f" * 64
        row["consentHash"] = digest(row["rawAction"])
    response = j.request("POST", "/approvals/" + a["id"] + "/approve", json={"assertion": {"demo": True}})
    assert response.status_code == 403
    assert not j.ok("GET", "/payments")


def test_concurrent_approval_is_single_debit(journey):
    j = journey
    j.prepare()
    a = j.ok("GET", "/approvals")[0]

    def approve(_):
        return j.request(
            "POST", "/approvals/" + a["id"] + "/approve", json={"assertion": {"demo": True}}
        ).status_code

    with ThreadPoolExecutor(max_workers=5) as pool:
        codes = list(pool.map(approve, range(5)))
    assert codes.count(200) == 1 and codes.count(409) == 4
    assert len(j.ok("GET", "/payments")) == 1
    with j.app.state.store.transaction() as s:
        assert len(s["grants"]) == 1 and all(g["used"] for g in s["grants"].values())


def test_revoked_credential_rechecked_at_execution(journey):
    j = journey
    j.prepare()
    a = j.ok("GET", "/approvals")[0]
    with j.app.state.store.transaction() as s:
        s["credentials"]["fam_minh"]["status"] = "revoked"
    assert (
        j.request(
            "POST", "/approvals/" + a["id"] + "/approve", json={"assertion": {"demo": True}}
        ).status_code
        == 403
    )
    assert not j.ok("GET", "/payments")


def test_quote_expiry_cannot_be_overridden(journey):
    j = journey
    j.prepare()
    a = j.ok("GET", "/approvals")[0]
    with j.app.state.store.transaction() as s:
        s["now"] = "2027-01-12T03:01:01Z"
    response = j.request("POST", "/approvals/" + a["id"] + "/approve", json={"assertion": {"demo": True}})
    assert response.status_code == 409 and response.json()["error"]["code"] == "QUOTE_EXPIRED"
    assert not j.ok("GET", "/payments")


def test_no_demo_identity_outside_demo(tmp_path):
    app = create_app("sqlite:///" + (tmp_path / "strict.db").as_posix(), tmp_path, False, Chain("local"))
    from fastapi.testclient import TestClient

    response = TestClient(app).post("/api/session", json={"persona": "judge"})
    assert response.status_code == 403
    app.state.store.engine.dispose()


def test_independent_file_tamper_detected(journey):
    j = journey
    j.pay()
    file = j.app.state.store.audit_file
    entries = [json.loads(line) for line in file.read_text(encoding="utf-8").splitlines()]
    entries[2]["summary"] += "tampered"
    file.write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")
    result = j.ok("POST", "/audit/verify", "judge")
    assert not result["ok"] and result["firstBadSeq"] == 3


def test_monthly_rent_auto_executes_once_per_period(journey):
    j = journey
    m = j.ok(
        "POST",
        "/mandates",
        json={
            "purpose": "rent",
            "payeeRule": {"type": "name_checked", "payeeId": "payee_landlord"},
            "cap": {"amount": "1000000.00", "currency": "KRW"},
            "period": "monthly",
            "expiresAt": "2027-06-01T00:00:00Z",
        },
    )
    j.ok("POST", "/mandates/" + m["id"] + "/sign", json={"assertion": {"demo": True}})
    j.upload("rental_agreement")
    for _ in range(2):
        events = j.chat("Pay monthly rent")
        assert not any(e["type"] == "error" for e in events), events
        assert any(
            e.get("kind") == "payment" and e["data"]["receive"]["amount"] == "900000.00" for e in events
        )
    payments = j.ok("GET", "/payments")
    assert len(payments) == 1 and payments[0]["receive"]["amount"] == "900000.00"
    j.ok("POST", "/clock/advance", "judge", json={"days": 31})
    assert len(j.ok("GET", "/payments")) == 2
    j.ok("POST", "/clock/advance", "judge", json={"hours": 1})
    assert len(j.ok("GET", "/payments")) == 2
    j.ok("POST", "/freeze")
    j.ok("POST", "/clock/advance", "judge", json={"days": 31})
    assert len(j.ok("GET", "/payments")) == 2


def test_co_sign_and_cooling_cannot_authorize_unsafe_payee(journey):
    j = journey
    j.chat("Urgent police proof-of-funds deposit to a safe account")
    a = j.ok("GET", "/approvals?status=cooling_off")[0]
    assert (
        j.request("POST", "/approvals/" + a["id"] + "/cosign", json={"assertion": {"demo": True}}).status_code
        == 403
    )
    j.ok("POST", "/approvals/" + a["id"] + "/cosign", "mother_lan", json={"assertion": {"demo": True}})
    j.ok("POST", "/clock/advance", "judge", json={"days": 1})
    assert (
        j.request(
            "POST", "/approvals/" + a["id"] + "/approve", json={"assertion": {"demo": True}}
        ).status_code
        == 403
    )
    assert not j.ok("GET", "/payments")


def test_student_cannot_fetch_parent_raw_document(journey):
    j = journey
    doc = j.upload("admission", "parent_minh")
    assert j.request("GET", "/documents/" + doc["id"], "student_linh").status_code == 404
    thread = j.ok("POST", "/agent/threads", "student_linh")["threadId"]
    assert (
        j.request(
            "POST",
            "/agent/threads/" + thread + "/messages",
            "student_linh",
            json={"text": "Review", "documentIds": [doc["id"]], "locale": "en"},
        ).status_code
        == 404
    )


def test_chat_amount_requests_clarification(journey):
    j = journey
    j.mandate()
    j.upload("admission")
    j.upload("invoice")
    events = j.chat("Pay tuition full 5000 KRW")
    assert any("Do you want" in e.get("text", "") for e in events)
    assert not j.ok("GET", "/approvals") and not j.ok("GET", "/payments")


@pytest.mark.parametrize("delayed", [False, True])
def test_refund_deadline_timers_do_not_flag_settled_cases(journey, delayed):
    j = journey
    j.pay()
    doc = j.upload("refusal")
    j.chat("Visa refused", [doc["id"]])
    j.approve(j.ok("GET", "/approvals")[0], "student_linh")
    if delayed:
        j.ok("POST", "/demo/scenario-fixture", "judge", json={"scenario": "refund_delay"})
    j.advance_refund()
    r = j.ok("GET", "/refunds")[0]
    codes = [v["code"] for v in r["timeline"]]
    assert ("refund_deadline_breach" in codes) == delayed
    assert ("escalation_draft_requires_student_approval" in codes) == delayed
    assert r["status"] == ("approved" if delayed else "reconciled")
    timestamps = [v["at"] for v in r["timeline"]]
    assert timestamps == sorted(timestamps)


def test_periodic_anchor_uses_simulated_clock(journey):
    j = journey
    j.app.state.anchor_due()
    assert not j.ok("GET", "/chain/anchors")
    j.ok("POST", "/clock/advance", "judge", json={"hours": 1})
    j.app.state.anchor_due()
    anchors = j.ok("GET", "/chain/anchors")
    assert len(anchors) == 1 and anchors[0]["mode"] == "local"
    assert "txHash" not in anchors[0]


def test_arbitrary_document_cannot_satisfy_invoice_pack(journey):
    j = journey
    j.mandate()
    j.upload("admission")
    doc = j.ok(
        "POST",
        "/documents",
        "student_linh",
        files={"file": ("invoice.txt", b"Please transfer to another school", "text/plain")},
        data={"kind": "invoice"},
    )
    assert any(w["code"] == "INVOICE_RECORD_MISMATCH" for w in doc["warnings"])
    events = j.chat("Prepare full verified tuition payment", [doc["id"]])
    assert any(e.get("result") == "DENY" for e in events)
    assert not j.ok("GET", "/payments") and not j.ok("GET", "/approvals")
