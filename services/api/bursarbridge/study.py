"""Signed academic calendar and separate, non-executable family obligations."""

from decimal import Decimal

from .catalog import INVOICE_VERSION
from .engine import DomainError, dt, money, require, resolve_invoice_action


def window_status(now, invoice):
    window = invoice.get("paymentWindow") or invoice.get("registrationWindow")
    if not window:
        return "legacy_unspecified"
    if dt(now) < dt(window["opensAt"]):
        return "not_open"
    if dt(now) > dt(window["closesAt"]):
        return "closed"
    return "open"


def require_payment_window(s, invoice):
    require(
        window_status(s["now"], invoice) in {"open", "legacy_unspecified"},
        "REGISTRATION_WINDOW_REQUIRED",
        "Payment must be inside its signed registration window",
        409,
    )


def study_plan(s, user, issuer):
    family = user["familyId"]
    cred = s["credentials"][family]
    require(cred["status"] == "valid", "CREDENTIAL_REVOKED", "Issuer credential revoked", 403)
    invoice = issuer.verify(cred["jwt"], int(dt(s["now"]).timestamp()))
    require(invoice["familyId"] == family, rule="P-01")
    try:
        payable = resolve_invoice_action(s, invoice)
        window = payable.get("paymentWindow") or invoice.get("registrationWindow")
        status = window_status(s["now"], payable)
    except DomainError as exc:
        if exc.code != "INVOICE_SETTLED":
            raise
        status, window = "settled", invoice.get("registrationWindow")
    private_rent = any(
        m["_family"] == family and m["purpose"] == "rent" and m["status"] == "active"
        for m in s["mandates"].values()
    )
    obligations = [
        {**o, "applicable": not (private_rent and o["id"] == "dorm")}
        for o in invoice.get("separateObligations", [])
    ]
    academic = invoice.get("academicTimeline", {})
    certificate = ({
        "status": "issued_MOCK", "issuedAt": academic["certificateIssuedAt"],
        "basis": "acceptance", "downloadUrl": "/api/study-plan/standard-admission-certificate.pdf",
    } if academic else s.get("standardCertificates", {}).get(family))
    refusal = any(
        d["_family"] == family and d["kind"] == "refusal" and not d["warnings"]
        for d in s["documents"].values()
    )
    return {
        "admissionDisposition": s.get("admissionDispositions", {}).get(family),
        "simulatedNow": s["now"],
        "clock": "SIMULATED",
        "source": "Fictional Hanbit signed academic terms (MOCK)",
        "invoiceVersion": invoice["version"],
        "tuition": money(invoice["amount"], "KRW"),
        "seedRefreshRequired": invoice["version"] != INVOICE_VERSION,
        "registrationWindow": invoice.get("registrationWindow"),
        "dueAt": invoice["dueAt"],
        "instalmentSchedule": invoice.get("instalmentSchedule", []),
        "paymentWindowStatus": status,
        "currentPaymentWindow": window,
        "separateObligations": obligations,
        "housing": {
            "mode": "private_rent" if private_rent else "dormitory_option",
            "mutuallyExclusive": True,
        },
        "classesStart": invoice["refundPolicy"]["classesStart"],
        "refundPromise": invoice["refundPolicy"].get("promiseAt", "2027-03-16T00:00:00Z"),
        "standardAdmissionCertificate": certificate or {"status": "legacy_unspecified"},
        "academicTimeline": academic,
        "visaApplication": {
            "appliedAt": academic.get("visaAppliedAt"),
            "status": "refusal_evidence_received_MOCK"
            if refusal
            else "processing_MOCK"
            if academic
            else "legacy_unspecified",
            "integration": "MOCK sequence only; no embassy application is submitted",
        },
        "sequence": [
            "admission_acceptance",
            "standard_admission_certificate",
            "D2_visa_application",
            "registration_payment_while_visa_pending",
            "visa_decision",
            "tuition_refund_if_refused",
        ],
    }


def rent_setup(s, user):
    from .engine import mandate_valid, public

    family = user["familyId"]
    record = s["bankPayees"]["payee_landlord"]
    student = next(u for u in s["users"].values() if u["familyId"] == family and u["role"] == "student")
    payer = next(u for u in s["users"].values() if u["familyId"] == family and u["role"] == "parent")
    agreement = next(
        (
            d
            for d in s["documents"].values()
            if d["_family"] == family
            and d["kind"] == "rental_agreement"
            and not d["warnings"]
            and d.get("_leaseVerified")
        ),
        None,
    )
    mandates = [m for m in s["mandates"].values() if m["_family"] == family and m["purpose"] == "rent"]
    active = next((m for m in reversed(mandates) if mandate_valid(s, m)), None)
    missing = []
    if not agreement:
        missing.append({"kind": "rental_agreement", "actorId": student["id"], "action": "upload"})
    if active and Decimal(active["cap"]["amount"]) < Decimal(record["amount"]):
        missing.append({"kind": "rent_cap", "actorId": payer["id"], "action": "create_and_sign_higher_limit"})
    if (
        not dt(record.get("validFrom", "2027-01-01T00:00:00Z"))
        <= dt(s["now"])
        < dt(record.get("validUntil", "2027-06-01T00:00:00Z"))
    ):
        missing.append(
            {
                "kind": "current_rental_agreement",
                "actorId": student["id"],
                "action": "request_verified_lease_renewal",
            }
        )
    if not active:
        missing.append({"kind": "rent_mandate", "actorId": payer["id"], "action": "create_and_sign"})
    landlord = {
        "id": record["id"],
        "name": record["name"],
        "institution": "Landlord (MOCK)",
        "account": {"masked": "•••• 1193", "hashMatch": record["nameCheck"] == "match"},
        "credential": {"issuer": "Lotus Home Bank (MOCK)", "status": "none"},
        "nameCheck": record["nameCheck"],
        "verification": {
            "method": "bank_name_check_and_mock_rental_agreement",
            "agreementStatus": "verified_MOCK" if agreement else "required",
            "validFrom": record.get("validFrom"),
            "validUntil": record.get("validUntil"),
            "agreementId": agreement["id"] if agreement else None,
            "source": "Bank-held standing lease; uploaded text never sets account or rent",
        },
    }
    return {
        "purpose": "rent",
        "payeeRule": "verified_landlord_only",
        "landlord": landlord,
        "monthlyAmount": money(record["amount"], "KRW"),
        "missing": missing,
        "mandates": [public(m) for m in mandates],
        "activeMandateId": active["id"] if active else None,
        "mandateTemplate": {
            "purpose": "rent",
            "payeeRule": {"type": "name_checked", "payeeId": record["id"]},
            "cap": money(record["amount"], "KRW"),
            "period": "monthly",
            "expiresAt": "2027-06-01T00:00:00Z",
        },
        "housing": "Private-rent alternative; do not also budget the dormitory",
        "verificationStatus": "ready" if not missing and record["nameCheck"] == "match" else "needs",
    }
