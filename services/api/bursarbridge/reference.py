"""Stable, family-scoped reply reference. This is never payment authority."""

from datetime import timedelta

from .conversation import display_money
from .engine import dt, quote, refund_view
from .localization import localize
from .study import study_plan


def date_text(value, locale):
    date = dt(value)
    return {
        "en": date.strftime("%d %b %Y"),
        "vi": date.strftime("%d/%m/%Y"),
        "ko": f"{date.year}년 {date.month}월 {date.day}일",
        "zh": f"{date.year}年{date.month}月{date.day}日",
    }[locale]


def family_reference(s, user, issuer, locale):
    """Project signed terms on EVERY turn, independent of proposal or topic.

    Signature validity is checked locally for reference reads. Bank execution
    retains its independent live-registry, sanctions, mandate and consent checks.
    No JWT, account, SWIFT, identity record, grant or document text is returned.
    """
    family = user["familyId"]
    try:
        cred = s["credentials"][family]
        if cred["status"] != "valid":
            raise ValueError("Invalid credential")
        invoice = issuer.verify(cred["jwt"], int(dt(s["now"]).timestamp()))
        if invoice["familyId"] != family:
            raise ValueError("Wrong family")
    except Exception:
        return {"status": "unavailable", "reason": "Local issuer signature or credential status invalid"}, {}
    display = {
        "billTotal": display_money({"amount": invoice["amount"], "currency": invoice["currency"]}, locale),
        "billDueDate": date_text(invoice["dueAt"], locale),
        "billInstalmentCount": str(len(invoice["instalments"])),
        "billInstitution": invoice["name"],
        "billTerm": localize({"term": invoice["term"]}, locale)["term"],
        "billInstalmentSchedule": " + ".join(
            display_money({"amount": n, "currency": "KRW"}, locale) for n in invoice["instalments"]
        ),
    }
    for key, value in invoice.get("academicTimeline", {}).items():
        if key.endswith("At"):
            display[key] = date_text(value, locale)
    for index, line in enumerate(invoice["lines"], 1):
        display[f"billLine{index}Amount"] = display_money(line["amount"], locale)
    currency = "CNY" if family == "fam_wang" else "VND"
    q = quote(s, currency, "KRW", invoice["amount"], "receive")
    display["billHomeEstimate"] = display_money(q["send"], locale)
    display["billFxSource"] = (
        {
            "vi": "tỷ giá mô phỏng (MOCK)",
            "en": "MOCK board rate",
            "ko": "모의 고시 환율 (MOCK)",
            "zh": "模拟牌价（MOCK）",
        }[locale]
        if q["source"] == "MOCK"
        else "ECB reference rate"
    )
    schedule = invoice.get("instalmentSchedule") or [
        {"number": i + 1, "amount": amount, "dueAt": invoice["dueAt"]}
        for i, amount in enumerate(invoice["instalments"])
    ]
    for row in schedule:
        display[f"billInstalment{row['number']}Amount"] = display_money(
            {"amount": row["amount"], "currency": "KRW"}, locale
        )
        display[f"billInstalment{row['number']}DueDate"] = date_text(row["dueAt"], locale)
    policy = invoice["refundPolicy"]
    display["classesStart"] = date_text(policy["classesStart"], locale)
    promise = dt(policy["classesStart"]) + timedelta(days=policy["paymentWithinDaysAfterClassesStart"])
    display["policyRefundDeadline"] = date_text(promise.isoformat(), locale)
    calendar = study_plan(s, user, issuer)
    display["simulatedToday"] = date_text(s["now"], locale)
    display["complaintWait"] = {"vi": "7 ngày", "en": "7 days", "ko": "7일", "zh": "7天"}[locale]
    display["rentMonthly"] = display_money(
        {"amount": s["bankPayees"]["payee_landlord"]["amount"], "currency": "KRW"}, locale
    )
    current_window = calendar.get("currentPaymentWindow")
    if current_window:
        display["registrationOpens"] = date_text(current_window["opensAt"], locale)
        display["registrationCloses"] = date_text(current_window["closesAt"], locale)
    for obligation in invoice.get("separateObligations", []):
        key = "dormBudget" if obligation["id"] == "dorm" else "insuranceMonthly"
        display[key] = display_money(obligation["amount"], locale)
    payments = [p for p in s["payments"].values() if p["_family"] == family and p.get("purpose") == "tuition"]
    refunds = [refund_view(s, r) for r in s["refunds"].values() if r["_family"] == family]
    refund_case = None
    if refunds:
        current = refunds[-1]
        refund_case = {
            "status": current["status"],
            "eligibility": current.get("eligibility"),
            "received": bool(current.get("reconciliation")),
            "estimateIsMock": current.get("estimate") is not None,
            "escalationStatus": (current.get("followUp") or {}).get("escalation", {}).get("status"),
            "complaintPackReady": bool((current.get("followUp") or {}).get("complaintPack")),
        }
        if current.get("deadline"):
            display["refundDeadline"] = date_text(current["deadline"], locale)
        amounts = current.get("reconciliation") or current.get("estimate")
        if amounts:
            display["refundReceivedBack"] = display_money(amounts["receivedBack"], locale)
            keys = {
                "OUTBOUND_BANK_FEE": "refundBankFee",
                "FX_MOVEMENT_MOCK": "refundFxLoss",
                "INTERMEDIARY_BANK_FEE_MOCK": "refundWireFee",
                "RETENTION": "refundRetention",
            }
            for line in amounts["lines"]:
                display[keys[line["code"]]] = display_money(line["amount"], locale)
    return {
        "activeRefund": refund_case,
        "safety": {
            "outgoingFrozen": bool(s["frozen"].get(family)),
            "incomingRefundsPaused": False,
            "freezeCancelsOnlyPaymentsStillInsideCancelWindow": True,
            "unfreezeRestoresOriginalSignedLimits": True,
            "cancelledTransfersAreNotAutomaticallyResent": True,
            "expiredOrExplicitlyRevokedMandatesAreNotRevived": True,
        },
        "admissionDisposition": {
            k: v
            for k, v in s.get("admissionDispositions", {}).get(family, {}).items()
            if k
            in {
                "status",
                "moneyAtRisk",
                "refundRequired",
                "tuitionStopped",
                "admissionAction",
                "admissionWithdrawn",
                "reconfirmation",
            }
        },
        "status": "signed_reference_only_not_execution_authority",
        "invoiceVersion": invoice["version"],
        "academicCalendar": {
            "todayFact": "simulatedToday",
            "windowStatus": calendar["paymentWindowStatus"],
            "opensFact": "registrationOpens",
            "closesFact": "registrationCloses",
            "standardCertificate": calendar["standardAdmissionCertificate"]["status"],
            "visaStatus": calendar["visaApplication"]["status"],
            "academicTimeline": {
                "acceptedFact": "acceptedAt",
                "certificateIssuedFact": "certificateIssuedAt",
                "visaAppliedFact": "visaAppliedAt",
                "visaStatusAtSeed": calendar["academicTimeline"].get("visaStatusAtSeed"),
            },
            "sequenceExplanation": "Acceptance and certificate precede D-2 application; tuition is paid while visa processing is pending, before the result. A refusal then triggers the tuition refund process, not another visa application.",
            "sequence": calendar["sequence"],
        },
        "separateObligations": [
            {k: v for k, v in o.items() if k not in {"amount", "sourceUrl"}}
            | {"amountFact": "dormBudget" if o["id"] == "dorm" else "insuranceMonthly"}
            for o in calendar["separateObligations"]
        ],
        "invoiceComposition": [line["label"] for line in invoice["lines"]],
        "invoiceLines": [
            {"label": line["label"], "amountFact": f"billLine{index}Amount"}
            for index, line in enumerate(invoice["lines"], 1)
        ],
        "schedule": [
            {
                "number": row["number"],
                "amountFact": f"billInstalment{row['number']}Amount",
                "dueFact": f"billInstalment{row['number']}DueDate",
            }
            for row in schedule
        ],
        "scheduleMeaning": "Each instalment has its own signed dueFact; use that entry, not the invoice-level first deadline",
        "refundPolicy": policy,
        "rent": {
            "amountFact": "rentMonthly",
            "payee": "Bank name-checked landlord plus verified MOCK rental agreement",
            "requires": "Parent-signed monthly rent cap; this is separate from the university tuition mandate",
        },
        "recoveryLimits": {
            "guaranteedRecovery": False,
            "missedPromise": "Dated chaser cites claim, signed forms and promise; student approval before MOCK outbox",
            "externalRoute": "Korea e-People / Ministry of Education",
            "waitAfterChaserFact": "complaintWait",
            "stalledChaser": "After seven simulated days without receipt, prepare redacted complaint pack for manual e-People / Ministry of Education submission; no real filing",
        },
        "refundCosts": "Family bears original outgoing bank fee, intermediary international-wire fees and KRW to USD to home-currency conversion loss; no net refund is guaranteed",
        "refundEligibility": "Full paid tuition requires filing before classes start; dormitory and NHIS are separate, not covered; after-start claims need manual degree-office assessment",
        "latePaymentPolicy": invoice.get(
            "latePaymentPolicy", {"status": "not_in_this_signed_invoice_version"}
        ),
        "paymentStatuses": [p["status"] for p in payments],
        "hasRefundCase": any(r["_family"] == family for r in s["refunds"].values()),
        "referenceIsNotUploadedDocuments": True,
        "bankRules": {
            "payee": "Tuition: issuer-verified university virtual account only. Rent: bank name-checked landlord plus verified MOCK lease and signed monthly cap. Message or document account text never replaces either destination",
            "cancellation": "An existing sent payment is bank-held during its server-recorded cancellation window; matched payments cannot be cancelled here, and recovery is not guaranteed",
            "laterPayment": "Fresh quote and valid mandate/consent are required; a question schedules no transfer and changes no deadline",
        },
    }, display
