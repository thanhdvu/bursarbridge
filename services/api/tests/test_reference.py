"""Reference availability does not depend on a planner's intent or topic."""

import json

import pytest

from bursarbridge.conversation import scripted_reply
from bursarbridge.engine import dt
from bursarbridge.providers import Provider
from bursarbridge.reference import family_reference


@pytest.mark.parametrize(
    "text",
    [
        "Hello",
        "How much is tuition?",
        "If my visa is denied?",
        "Please pay tuition",
        "Invest it in crypto",
        "Pocket money please",
    ],
)
def test_every_reply_has_the_same_signed_reference(journey, monkeypatch, text):
    captured = []

    def reply(self, history, locale, facts):
        captured.append(facts)
        return scripted_reply(facts, locale)

    monkeypatch.setattr(Provider, "reply", reply)
    journey.chat(text)
    facts = captured[0]
    reference = facts["familyReference"]
    assert reference["status"] == "signed_reference_only_not_execution_authority"
    assert reference["latePaymentPolicy"]["id"] == "HBU-LATE-01-v1"
    assert len(reference["schedule"]) == 2
    assert facts["display"]["billInstalment2Amount"] == "3,587,000 KRW"
    assert facts["display"]["billInstalment2DueDate"] == "15 Feb 2027"
    assert [facts["display"][line["amountFact"]] for line in reference["invoiceLines"]] == [
        "7,174,000 KRW",
    ]
    assert facts["display"]["policyRefundDeadline"] == "16 Mar 2027"
    serialized = json.dumps(reference)
    assert not any(k in serialized for k in ("jwt", "accountId", "passport", "LOTUVNVX"))


def test_signed_schedule_and_late_policy_are_not_filled_from_current_code_for_old_records(journey):
    j = journey
    with j.app.state.store.transaction() as s:
        user = next(u for u in s["users"].values() if u["role"] == "parent" and u["familyId"] == "fam_minh")
        issuer = j.app.state.issuer
        cred = s["credentials"][user["familyId"]]
        invoice = issuer.verify(cred["jwt"], int(dt(s["now"]).timestamp()))
        assert [r["dueAt"] for r in invoice["instalmentSchedule"]] == [
            invoice["dueAt"],
            "2027-02-15T08:00:00Z",
        ]
        assert invoice["latePaymentPolicy"]["lateFee"] is None
        invoice.pop("latePaymentPolicy")
        invoice.pop("instalmentSchedule")
        invoice["version"] = "semester-2027-v4"
        cred["jwt"] = issuer.issue(
            invoice, int(dt(s["now"]).timestamp()) - 10, int(dt(s["now"]).timestamp()) + 1000
        )
        reference, display = family_reference(s, user, issuer, "en")
        assert reference["latePaymentPolicy"] == {"status": "not_in_this_signed_invoice_version"}
        assert display["billInstalment2DueDate"] == "15 Jan 2027"
        text = scripted_reply(
            {
                "outcome": "policy",
                "familyReference": reference,
                "policyAdvice": {"topics": ["missed_instalment"]},
                "display": display,
            },
            "en",
        )
        assert "3,587,000 KRW" in text and "15 Jan 2027" in text
        assert "registration" not in text and "does not define" in text


def test_invalid_signature_does_not_get_known_seed_facts_as_a_substitute(journey):
    with journey.app.state.store.transaction() as s:
        user = next(u for u in s["users"].values() if u["role"] == "parent" and u["familyId"] == "fam_minh")
        s["credentials"][user["familyId"]]["jwt"] = "invalid"
        reference, display = family_reference(s, user, journey.app.state.issuer, "vi")
        assert reference["status"] == "unavailable" and display == {}


def test_unknown_scripted_information_does_not_default_to_invoice_totals():
    text = scripted_reply(
        {
            "outcome": "inform",
            "requestedFacts": [],
            "display": {"invoiceAmount": "7,174,000 KRW", "sendAmount": "135,663,956 VND"},
        },
        "en",
    )
    assert text.count("?") == 1
    assert "7,174,000" not in text and "135,663,956" not in text
