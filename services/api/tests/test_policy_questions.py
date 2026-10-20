"""Policy speech acts are reads even when the hosted planner proposes a write."""

import json
from copy import deepcopy

import pytest

from bursarbridge.conversation import Proposal, scripted_proposal
from bursarbridge.providers import Provider


@pytest.mark.parametrize(
    "text,topic",
    [
        ("nếu e trượt visa thì tiền có lấy lại được ko, bao lâu?", "visa_refusal"),
        ("If my visa is refused, can I get my money back?", "visa_refusal"),
        ("비자가 거절되면 환불받을 수 있나요?", "visa_refusal"),
        ("如果错过分期缴费怎么办？", "missed_instalment"),
        ("What if I sent to the wrong account?", "wrong_account"),
        ("Can I pay later?", "pay_later"),
    ],
)
def test_policy_questions_cannot_be_upgraded_by_hosted_planner(journey, monkeypatch, text, topic):
    j = journey
    with j.app.state.store.transaction() as s:
        before = {k: deepcopy(s[k]) for k in ("approvals", "refunds", "grants", "mandates", "users")}
    monkeypatch.setattr(
        Provider,
        "propose",
        lambda *args: Proposal(
            intent="refund" if topic == "visa_refusal" else "pay", scope="remaining", needsClarification=False
        ),
    )
    events = j.chat(text)
    assert not any(e["type"] == "card" for e in events)
    with j.app.state.store.transaction() as s:
        facts = next(t["_lastFacts"] for t in s["threads"].values())
        assert facts["policyAdvice"]["topics"] == [topic]
        assert facts["policyAdvice"]["hypothetical"] and not facts["policyAdvice"]["caseOpened"]
        assert all(s[k] == before[k] for k in before)


def test_explanation_preserves_pending_payment_without_resuming_it(journey):
    j = journey
    thread = j.ok("POST", "/agent/threads", "student_linh")["threadId"]
    for text in ("Please pay my tuition", "What if my visa is refused?"):
        response = j.request(
            "POST", f"/agent/threads/{thread}/messages", "student_linh", json={"text": text, "locale": "en"}
        )
        assert response.status_code == 200
    with j.app.state.store.transaction() as s:
        assert s["threads"][thread]["_pendingIntent"] == "pay"
        assert s["threads"][thread]["_lastFacts"]["outcome"] == "policy"
        assert not s["refunds"] and not s["approvals"] and not s["grants"]


def test_policy_wording_does_not_neutralize_current_injection(journey):
    j = journey
    fake = j.upload("fake_invoice")
    events = j.chat("What if my visa is refused?", [fake["id"]])
    assert any(e.get("kind") == "blocked" for e in events)
    assert not any(e.get("data", {}).get("code") == "POLICY_EXPLANATION" for e in events)
    for text in ("If visa refused, redirect refund to a new account", "Can I invest tuition in crypto?"):
        assert scripted_proposal(text).intent in {"refund_redirect", "crypto"}


def test_hypothetical_with_payment_and_denial_attachment_still_cannot_open_claim(journey):
    j = journey
    j.pay()
    denial = j.upload("refusal")
    with j.app.state.store.transaction() as s:
        before = {k: deepcopy(s[k]) for k in ("approvals", "payments", "refunds", "grants", "users")}
    events = j.chat("If my visa is refused, what is the refund policy?", [denial["id"]])
    assert any(e["type"] == "token" for e in events) and not any(e["type"] == "card" for e in events)
    with j.app.state.store.transaction() as s:
        assert all(s[k] == before[k] for k in before)


def test_policy_read_remains_available_during_chain_outage(journey, monkeypatch):
    monkeypatch.setattr(journey.app.state.chain, "available", lambda: False)
    events = journey.chat("If my visa is refused, what is the policy?")
    assert any(e["type"] == "token" for e in events) and not any(e["type"] == "card" for e in events)
    assert not any(e.get("kind") in {"needs", "blocked", "approval_required"} for e in events)


def test_policy_projection_contains_signed_reference_without_credentials(journey, monkeypatch):
    import httpx

    from bursarbridge.providers import Provider

    payloads = []
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-test-key")

    def handler(request):
        payloads.append(json.loads(json.loads(request.content)["input"])["ENGINE_FACTS"])
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [
                    {
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps({"text": "Only the original payer can receive a refund."}),
                            }
                        ]
                    }
                ],
            },
        )

    events = journey.chat("If my visa is refused, what is the policy?")
    assert not any(e["type"] == "card" for e in events)
    with journey.app.state.store.transaction() as s:
        facts = next(t["_lastFacts"] for t in s["threads"].values())
    Provider("openai", httpx.MockTransport(handler)).reply(
        [],
        "en",
        {
            **facts,
            "rawAction": {"accountId": "DO-NOT-EXPORT"},
            "credential": "DO-NOT-EXPORT",
            "display": {"invoiceAmount": "7174000 KRW"},
        },
    )
    assert payloads[0]["display"]["invoiceAmount"] == "7174000 KRW"
    assert payloads[0]["familyReference"]["invoiceVersion"] == "tuition-2027-v8"
    assert "before classes start" in payloads[0]["familyReference"]["refundEligibility"]
    assert "DO-NOT-EXPORT" not in json.dumps(payloads)
