"""Fictional degree contract. Never infer a degree entitlement from a language-course table."""

from datetime import datetime, timedelta
from decimal import Decimal

POLICY = {
    "id": "HBU-REF-01-v3",
    "source": "Hanbit University fictional contractual policy (MOCK), not Korean law",
    "classesStart": "2027-03-02T00:00:00Z",
    "paymentWithinDaysAfterClassesStart": 14,
    "promiseAt": "2027-03-16T00:00:00Z",
    "dormitory": "Ask the dormitory office about unused fees under its separate rule; no exact entitlement or timing verified",
    "beforeStart": "Full paid tuition only; dormitory and NHIS payments are separate and excluded",
    "admissionFee": "Nonrefundable if separately charged; none charged on this invoice",
    "afterStart": "Manual degree-office assessment; no language-course day table applies",
    "freshman": "Withdraw admission and reapply; leave of absence is not a substitute",
    "destination": "Original payer bank record only, including bank-held SWIFT",
    "settlement": "International office manual international wire (MOCK)",
}


def plan(now, payment, invoice, student_id, account, refusal_id):
    start = datetime.fromisoformat(invoice["refundPolicy"]["classesStart"].replace("Z", "+00:00"))
    before = datetime.fromisoformat(now.replace("Z", "+00:00")) < start
    return {
        "policy": invoice["refundPolicy"],
        "requestedAt": now,
        "deadline": (start + timedelta(days=invoice["refundPolicy"]["paymentWithinDaysAfterClassesStart"]))
        .isoformat()
        .replace("+00:00", "Z")
        if before
        else None,
        "eligibility": "before_start_full_unused" if before else "manual_degree_assessment",
        "claimAmount": payment["receive"],
        "admissionFeeCharged": {"amount": "0.00", "currency": "KRW"},
        "destination": {
            "accountId": account["id"],
            "bank": account["bank"],
            "maskedNumber": account["maskedNumber"],
            "swift": account["swift"],
            "source": "original_payer_bank_record",
        },
        "documents": [
            {"kind": "admission_withdrawal", "signerId": student_id, "status": "prepared"},
            {"kind": "tuition_refund_application", "signerId": student_id, "status": "prepared"},
            {"kind": "visa_denial_letter", "documentId": refusal_id, "status": "attached_MOCK"},
        ],
    }


def reconciliation(payment, currency):
    """Explicit MOCK cross-currency wire, not a percentage university refund charge."""
    from .engine import money

    sent = Decimal(payment["send"]["amount"])
    outbound_fee = Decimal(payment["fees"]["amount"])
    principal = sent - outbound_fee
    # Forward rate was already bank-margined. A separate return cross-rate models
    # KRW -> USD -> home-currency conversion loss; not an executable FX quote.
    loss = (principal * Decimal("0.02")).quantize(Decimal(".01"))
    intermediary = Decimal("375000") if currency == "VND" else Decimal("100")
    costs = [
        ("OUTBOUND_BANK_FEE", outbound_fee, "Original outward bank fee is not refunded"),
        ("FX_MOVEMENT_MOCK", loss, "MOCK KRW to USD to home-currency conversion loss"),
        ("INTERMEDIARY_BANK_FEE_MOCK", intermediary, "MOCK intermediary bank wire fee"),
        (
            "RETENTION",
            Decimal("0"),
            "No admission fee charged; tuition-only claim, no dormitory or insurance payment",
        ),
    ]
    back = sent - sum(amount for _, amount, _ in costs)
    return {
        "sentOut": payment["send"],
        "receivedBack": money(back, currency),
        "conversion": {
            "route": ["KRW", "USD", currency],
            "source": "MOCK return wire board",
            "lossPct": "2.00",
        },
        "lines": [
            {"code": code, "amount": money(amount, currency), "clause": clause}
            for code, amount, clause in costs
        ],
    }
