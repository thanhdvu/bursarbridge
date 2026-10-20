"""Versioned fictional issuer invoice; no amounts are sourced from chat or PDFs."""

INVOICE_VERSION = "tuition-2027-v8"
TOTAL = "7174000.00"
INSTALMENTS = ["3587000.00", "3587000.00"]
SIMULATED_TODAY = "2027-01-12T03:00:00Z"
REGISTRATION_WINDOW = {"opensAt": "2027-01-11T00:00:00Z", "closesAt": "2027-01-15T08:00:00Z", "timeZone": "Asia/Seoul"}
DUE_AT = "2027-01-15T08:00:00Z"
INSTALMENT_SCHEDULE = [
    {
        "number": index + 1,
        "amount": amount,
        "dueAt": DUE_AT if index == 0 else "2027-02-15T08:00:00Z",
        "paymentWindow": REGISTRATION_WINDOW.copy()
        if index == 0
        else {"opensAt": "2027-02-11T00:00:00Z", "closesAt": "2027-02-15T08:00:00Z", "timeZone": "Asia/Seoul"},
    }
    for index, amount in enumerate(INSTALMENTS)
]
LATE_PAYMENT_POLICY = {
    "id": "HBU-LATE-01-v1",
    "source": "Hanbit University fictional contractual policy (MOCK), not Korean law",
    "consequence": "An overdue unpaid instalment puts registration clearance on hold until the bursar confirms payment or issues a revised signed fee notice",
    "extension": "Only the university bursar can approve an extension through a revised signed fee notice; the assistant cannot extend a deadline",
    "lateFee": None,
    "lateFeeStatus": "No monetary late fee is specified in these signed terms; do not invent an amount or assume a fee waiver",
    "automaticEffects": "No automatic admission cancellation, refund, bank transfer or family safety freeze",
}
LINES = [
    {"label": "Semester tuition", "amount": {"amount": "7174000.00", "currency": "KRW"}},
]
SEPARATE_OBLIGATIONS = [
    {
        "id": "dorm",
        "label": "Dormitory March-June (4 months)",
        "amount": {"amount": "1500000.00", "currency": "KRW"},
        "period": "semester",
        "collector": "Hanbit Dormitory Office (MOCK)",
        "when": "Separate dormitory notice before move-in",
        "paidThroughBridge": False,
        "refundPolicy": "Ask the dormitory office about unused fees; no exact entitlement or date verified",
        "alternativeTo": "private_rent",
        "source": "MOCK adviser-based budget, not a payment instruction",
    },
    {
        "id": "health_insurance",
        "label": "Health insurance after arrival",
        "amount": {"amount": "70000.00", "currency": "KRW"},
        "period": "monthly",
        "collector": "NHIS (external public insurance, no integration)",
        "when": "After arrival and enrollment; student pays the actual NHIS bill, e.g. Korean-account auto-debit",
        "paidThroughBridge": False,
        "refundPolicy": "Outside the tuition claim; actual NHIS coverage and billing rules apply",
        "source": "MOCK 70,000/month planning assumption, not a verified NHIS premium",
        "sourceUrl": "https://www.nhis.or.kr/english/wbheaa02900m01.do",
    },
]

ACADEMIC_TIMELINE = {
    "acceptedAt": "2026-12-15T00:00:00Z",
    "certificateIssuedAt": "2026-12-22T00:00:00Z",
    "visaAppliedAt": "2027-01-04T00:00:00Z",
    "visaStatusAtSeed": "processing_MOCK",
    "source": "Fictional Hanbit academic calendar (MOCK); no embassy integration",
}
