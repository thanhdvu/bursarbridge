"""Dated MOCK correspondence, with student consent and no external transmission."""

from .engine import audit, dt, event, later, public, record_operation, require, uid
from .security import digest

ROUTE = {
    "name": "Korea e-People / Ministry of Education",
    "url": "https://www.epeople.go.kr/petition/htp/htp.npaid",
    "ministryUrl": "https://www.moe.go.kr/sub/infoRenew.do?m=010201",
    "submission": "manual_student_only",
    "guaranteesRecovery": False,
    "eligibility": "Student must check portal identity and eligibility requirements; no portal access or filing is provided",
}


def follow_up(s, refund):
    if not refund.get("deadline"):
        return
    received = refund["status"] in {"received", "reconciled"}
    if received:
        if refund.get("followUp"):
            refund["followUp"]["overdue"] = False
            refund["followUp"]["resolvedAt"] = s["now"]
        return
    if dt(s["now"]) < dt(refund["deadline"]):
        return
    student = next(
        u for u in s["users"].values() if u["familyId"] == refund["_family"] and u["role"] == "student"
    )
    case = refund.setdefault(
        "followUp",
        {"overdue": True, "promiseAt": refund["deadline"], "requiresStudentApproval": True, "mock": True},
    )
    case["daysOverdue"] = max(0, (dt(s["now"]) - dt(refund["deadline"])).days)
    if not case.get("escalation"):
        raw = {
            "purpose": "refund_escalation",
            "refundId": refund["id"],
            "claimReference": refund["id"],
            "promiseAt": refund["deadline"],
            "evidenceHashes": refund["paperwork"].get("evidenceHashes", {}),
            "recipient": "Hanbit International Office (MOCK)",
            "preparedAt": s["now"],
            "forms": [
                {k: f[k] for k in ("kind", "status", "consentHash", "signedAt") if k in f}
                for f in refund["paperwork"]["documents"][:2]
            ],
            "channel": "MOCK_LOCAL_OUTBOX",
            "nonce": uid("nonce"),
            "expiry": later(s, days=7),
        }
        approval = {
            "id": uid("apr"),
            "status": "pending",
            "action": "escalation_letter",
            "risk": {"score": 0, "features": []},
            "requestedBy": "agent",
            "rawAction": raw,
            "consentHash": digest(raw),
            "createdAt": s["now"],
            "expiresAt": raw["expiry"],
            "approverId": student["id"],
            "_family": refund["_family"],
            "correspondence": {
                "recipient": raw["recipient"],
                "preparedAt": s["now"],
                "claimReference": refund["id"],
                "promiseAt": refund["deadline"],
                "summary": "Promised tuition refund has not arrived. Please confirm the wire and revised payment date.",
                "formEvidence": raw["forms"],
                "mock": True,
            },
        }
        approval["correspondence"]["downloadUrl"] = f"/api/approvals/{approval['id']}/letter.pdf"
        s["approvals"][approval["id"]] = approval
        case["escalation"] = {
            "approvalId": approval["id"],
            "status": "pending_approval",
            "preparedAt": s["now"],
            **approval["correspondence"],
        }
        audit(
            s,
            "agent",
            "refund_escalation_prepared",
            "Dated MOCK chaser requires student signature",
            reference=refund["id"],
            approvalId=approval["id"],
        )
        event(s, refund["_family"], "approval_created", public(approval))
    sent = case["escalation"].get("submittedAt")
    if sent and (dt(s["now"]) - dt(sent)).days >= 7 and not case.get("complaintPack"):
        case["complaintPack"] = {
            "status": "prepared_MOCK",
            "preparedAt": s["now"],
            "route": ROUTE,
            "downloadUrl": f"/api/refunds/{refund['id']}/complaint-pack.pdf",
            "contains": [
                "dated_cover",
                "claim_and_payment_references",
                "signed_forms_index",
                "denial_letter_hash",
                "promise_and_chaser_timeline",
            ],
            "containsRawIdentityOrBankRecords": False,
            "reason": "No receipt seven simulated days after approved chaser; fictional follow-up interval, not a legal deadline",
        }
        audit(
            s,
            "agent",
            "refund_complaint_pack_prepared",
            "MOCK external-route pack ready for manual student review",
            reference=refund["id"],
        )


def submit(s, approval):
    raw = approval["rawAction"]
    require(
        raw.get("purpose") == "refund_escalation" and digest(raw) == approval["consentHash"],
        "CONSENT_MISMATCH",
    )
    refund = s["refunds"][raw["refundId"]]
    require(
        refund["_family"] == approval["_family"] and refund["status"] not in {"received", "reconciled"},
        "INVALID_STATE",
        "Refund already received or wrong family",
        409,
    )
    case = refund["followUp"]["escalation"]
    require(
        case["approvalId"] == approval["id"] and case["status"] == "pending_approval",
        "INVALID_STATE",
        "Chaser already processed",
        409,
    )
    case.update(status="submitted_MOCK", submittedAt=s["now"])
    s.setdefault("correspondence", {})[approval["id"]] = {
        "sentAt": s["now"],
        "payload": raw.copy(),
        "mock": True,
    }
    record_operation(
        s, "international_office", "refund_escalation", approval["id"], "submitted_MOCK_no_external_send"
    )
    audit(
        s,
        "student",
        "refund_escalation_submitted_MOCK",
        "Student-approved chaser recorded in MOCK outbox",
        reference=refund["id"],
    )
    from .engine import refund_view

    event(s, refund["_family"], "refund_updated", refund_view(s, refund))
    return refund


def letter_lines(refund, approval=None):
    lines = [
        "MOCK / SYNTHETIC - no external submission or recovery guarantee",
        "Claim reference: " + refund["id"],
        "Payment reference: " + refund["paymentId"],
        "Promised payment date: " + refund["deadline"],
        "Paid tuition claim: " + refund["claimAmount"]["amount"] + " KRW",
        "Refund destination stays the original payer; no bank credentials included.",
    ]
    for kind, value in refund["paperwork"].get("evidenceHashes", {}).items():
        lines.append("Evidence SHA-256 " + kind + ": " + value)
    for form in refund["paperwork"]["documents"]:
        lines.append("Evidence: " + form["kind"] + " | " + form.get("status", "attached"))
        if form.get("consentHash"):
            lines.append("Signed consent: " + form["consentHash"])
    if approval:
        lines += [
            "Prepared: " + approval["createdAt"],
            "To: " + approval["rawAction"]["recipient"],
            approval["correspondence"]["summary"],
            "Consent hash: " + approval["consentHash"],
        ]
    else:
        chaser = refund["followUp"]["escalation"]
        lines += [
            "Approved chaser: " + chaser["approvalId"],
            "Submitted (MOCK): " + chaser["submittedAt"],
            "External route: " + ROUTE["name"],
            ROUTE["url"],
            ROUTE["ministryUrl"],
            "Student must review and submit manually through the official portal.",
            "Exhibit index only: attach personal evidence yourself; raw identity/bank files are not exported.",
        ]
    return lines
