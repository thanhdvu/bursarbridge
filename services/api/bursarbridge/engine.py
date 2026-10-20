"""Trusted domain operations. All writes occur inside Store.transaction()."""

import copy
import hashlib
import json
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import yaml

from .catalog import (
    ACADEMIC_TIMELINE,
    DUE_AT,
    INSTALMENT_SCHEDULE,
    INSTALMENTS,
    INVOICE_VERSION,
    LATE_PAYMENT_POLICY,
    LINES,
    REGISTRATION_WINDOW,
    SEPARATE_OBLIGATIONS,
    SIMULATED_TODAY,
    TOTAL,
)
from .policy import Context, evaluate, is_structuring
from .refund_policy import POLICY
from .refund_policy import plan as refund_plan
from .refund_policy import reconciliation as refund_reconciliation
from .security import digest
from .store import audit


class DomainError(Exception):
    def __init__(self, code, message, status=400, rule=None):
        self.code, self.message, self.status, self.rule = code, message, status, rule


def require(condition, code="POLICY_DENIED", message="Operation not permitted", status=403, rule=None):
    if not condition:
        raise DomainError(code, message, status, rule)


def dt(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise DomainError("INVALID_TIME", "UTC offset required", 422)
    return result


def iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def later(s, **kwargs):
    return iso(dt(s["now"]) + timedelta(**kwargs))


def uid(prefix):
    return prefix + "_" + secrets.token_hex(8)


def freeze_family(s, family, actor, reason, **extra):
    """Panic stops outbound authority; it never blocks an original-payer credit."""
    start = time.perf_counter()
    revoked = cancelled = suspended = 0
    for grant in s["grants"].values():
        if grant["_family"] == family and not grant["revoked"] and not grant["used"]:
            grant["revoked"] = True
            revoked += 1
    for payment in s["payments"].values():
        if (
            payment["_family"] == family
            and payment["status"] == "sent"
            and dt(s["now"]) < dt(payment["_cancelUntil"])
        ):
            payer = next(
                u for u in s["users"].values() if any(a["id"] == payment["_payer"] for a in u["accounts"])
            )
            cancel(s, payment, payer, actor="freeze")
            payment["_freezeCancelled"] = True
            cancelled += 1
    for mandate in s["mandates"].values():
        if mandate["_family"] == family and mandate["status"] == "active":
            mandate["status"] = "suspended"
            mandate["_freezeSuspended"] = True
            suspended += 1
            event(s, family, "mandate_updated", public(mandate))
    paused = sum(
        a["_family"] == family
        and a["status"] == "pending"
        and a["action"] not in {"refund_claim", "escalation_letter"}
        for a in s["approvals"].values()
    )
    s["frozen"][family] = True
    s.setdefault("frozenReasons", {})[family] = reason
    details = {
        "frozen": True,
        "reason": reason,
        "frozenReason": reason,
        "recovery": "parent_passkey_unfreeze",
        "revokedTokens": revoked,
        "cancelledPayments": cancelled,
        "pausedApprovals": paused,
        "suspendedMandates": suspended,
        "incomingRefundsPaused": False,
        "tookMs": round((time.perf_counter() - start) * 1000, 3),
        **extra,
    }
    audit(
        s,
        actor,
        "freeze",
        "Outbound payments paused; cancellable transfers reversed; refunds continue",
        familyId=family,
        **details,
    )
    event(s, family, "freeze", details)
    return details


def restore_frozen_mandates(s, family):
    restored = 0
    for row in s["mandates"].values():
        # Suspended is only written by Freeze, including pre-marker demo ledgers.
        # Revoked and unsigned mandates are never revived.
        if row["_family"] == family and row["status"] == "suspended":
            row["status"] = "active" if dt(row["expiresAt"]) > dt(s["now"]) else "expired"
            row.pop("_freezeSuspended", None)
            restored += row["status"] == "active"
            event(s, family, "mandate_updated", public(row))
    for approval in s["approvals"].values():
        grant = s["grants"].get(approval.get("_grant"))
        if (
            approval["_family"] == family
            and approval["status"] == "pending"
            and grant
            and grant["revoked"]
            and not grant["used"]
        ):
            approval.pop("_grant", None)  # Fresh single-use grant after the payer signs; never un-revoke.
    return restored


def frozen_reason(s, family):
    return s.get("frozenReasons", {}).get(family, "LEGACY_FREEZE") if s["frozen"].get(family) else None


def money(amount, currency):
    return {
        "amount": str(Decimal(amount).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)),
        "currency": currency,
    }


def public(row):
    result = {
        k: copy.deepcopy(v)
        for k, v in row.items()
        if not k.startswith("_") and not (k == "cancelUntil" and row.get("status") != "sent")
    }
    if "_cosigned" in row:
        result["cosigned"] = bool(row["_cosigned"])
        result.setdefault("cosignedAt", None)  # Older rows did not record this timestamp.
    return result


def family_rows(s, table, user):
    return [public(r) for r in s[table].values() if r.get("_family") == user["familyId"]]


def owned(s, table, ref, user):
    row = s[table].get(ref)
    require(
        row is not None and row.get("_family") == user["familyId"], "NOT_FOUND", "Resource not found", 404
    )
    return row


def parent(user):
    require(user["role"] == "parent", "ROLE_REQUIRED", "Parent approval required")


def seed(s, issuer):
    rules = yaml.safe_load(Path(__file__).with_name("rules.yaml").read_text(encoding="utf-8"))
    s.clear()
    s.update(
        {
            "now": SIMULATED_TODAY,
            "_generation": uid("gen"),
            "rulesVersion": rules["version"],
            "rulesHash": digest(rules),
            "rules": rules,
            "audit": [],
            "frozen": {},
            "anchors": [],
            "grants": {},
            "challenges": {},
            "assertions": {},
            "authenticators": {},
            "events": [],
            "operations": [],
            "credentials": {},
            "sessions": {},
            "mandates": {},
            "documents": {},
            "approvals": {},
            "payments": {},
            "refunds": {},
            "threads": {},
            "users": {},
            "invoicePaid": {},
            "denials": {},
        }
    )
    for persona, name, role, locale, family, currency in [
        ("parent_minh", "Minh", "parent", "vi", "fam_minh", "VND"),
        ("student_linh", "Linh", "student", "ko", "fam_minh", None),
        ("mother_lan", "Lan", "cosigner", "vi", "fam_minh", None),
        ("parent_wang", "Wang", "parent", "zh", "fam_wang", "CNY"),
        ("student_hao", "Hao", "student", "zh", "fam_wang", None),
        ("judge", "Judge", "judge", "en", "audit", None),
    ]:
        accounts = (
            []
            if not currency
            else [
                {
                    "id": "acct_" + persona,
                    "bank": "Lotus Home Bank (MOCK)",
                    "currency": currency,
                    "maskedNumber": "•••• 4821",
                    "swift": "LOTUVNVX" if currency == "VND" else "LOTUCNBX",
                    "balance": money("1000000000" if currency == "VND" else "1000000", currency),
                }
            ]
        )
        s["users"][persona] = {
            "id": "usr_" + persona,
            "name": name,
            "role": role,
            "locale": locale,
            "familyId": family,
            "accounts": accounts,
        }
    s["issuer"] = issuer.did
    s["fxPurchases"] = []
    s["bankPayees"] = {
        "payee_landlord": {
            "id": "payee_landlord",
            "name": "Seoul Garden Residence (MOCK)",
            "accountHash": digest("MOCK-RENT-1193"),
            "nameCheck": "match",
            "amount": "900000.00",
            "currency": "KRW",
            "provenance": "bank_record",
            "validFrom": "2027-01-01T00:00:00Z",
            "validUntil": "2027-06-01T00:00:00Z",
        }
    }
    for family in ("fam_minh", "fam_wang"):
        subject = {
            "id": "payee_hanbit",
            "name": "Hanbit University",
            "accountHash": digest("MOCK-HANBIT-VA-883104"),
            "invoiceRef": "HBU-2027-0042-" + family,
            "amount": TOTAL,
            "version": INVOICE_VERSION,
            "term": "Spring 2027 - semester 1",
            "lines": copy.deepcopy(LINES),
            "dueAt": DUE_AT,
            "registrationWindow": copy.deepcopy(REGISTRATION_WINDOW),
            "academicTimeline": copy.deepcopy(ACADEMIC_TIMELINE),
            "separateObligations": copy.deepcopy(SEPARATE_OBLIGATIONS),
            "instalments": INSTALMENTS.copy(),
            "instalmentSchedule": copy.deepcopy(INSTALMENT_SCHEDULE),
            "latePaymentPolicy": copy.deepcopy(LATE_PAYMENT_POLICY),
            "refundPolicy": copy.deepcopy(POLICY),
            "currency": "KRW",
            "familyId": family,
            "type": "PayeeAndInvoiceCredential",
        }
        token = issuer.issue(
            subject, int(dt(s["now"]).timestamp()) - 86400 * 2, int(dt(s["now"]).timestamp()) + 86400 * 365
        )
        s["credentials"][family] = {"jwt": token, "status": "valid", "hash": digest(token)}
    audit(s, "system", "seed", "Synthetic personas and MOCK issuer seeded")


def payee(s, family):
    credential = s["credentials"][family]
    return {
        "id": "payee_hanbit",
        "name": "Hanbit University",
        "institution": "Hanbit University (MOCK)",
        "account": {"masked": "•••• 3104", "hashMatch": True},
        "credential": {
            "issuer": s["issuer"],
            "status": credential["status"],
            "vcId": credential["hash"],
            **({"chainTx": credential["chainTx"]} if "chainTx" in credential else {}),
        },
        "nameCheck": "match",
        "verification": {"method": "issuer_signed_tuition_virtual_account", "purpose": "tuition"},
    }


def verified_invoice(s, family, issuer):
    require(
        not s.get("registrationPending"), "CHAIN_REGISTRATION_PENDING", "Issuer registration is retrying", 503
    )
    require(issuer.chain.available(), "CHAIN_UNAVAILABLE", "Credential verification will retry", 503)
    cred = s["credentials"][family]
    require(cred["status"] == "valid", rule="P-01", message="Issuer credential revoked")
    require(
        issuer.chain.credential_valid(cred["hash"]),
        "CREDENTIAL_REVOKED",
        "Credential registry status invalid",
        403,
        "P-01",
    )
    try:
        data = issuer.verify(cred["jwt"], int(dt(s["now"]).timestamp()))
    except Exception as exc:
        raise DomainError("CREDENTIAL_INVALID", "Issuer signature or validity failed", 403, "P-01") from exc
    require(
        data["familyId"] == family and data["accountHash"] == digest("MOCK-HANBIT-VA-883104"), rule="P-01"
    )
    screening = issuer.screening.screen(data["name"])
    s.setdefault("screenings", {})[family] = screening
    # Screening result is not exposed to the model and includes list versions.
    return data


BOARD = {
    "VND": Decimal("0.000039"),
    "KRW": Decimal("0.00073"),
    "CNY": Decimal("0.14"),
    "AUD": Decimal("0.66"),
    "USD": Decimal("1"),
    "EUR": Decimal("1.08"),
}


def quote(s, from_currency, to_currency, amount, side="send"):
    require(
        from_currency in BOARD and to_currency in BOARD and side in {"send", "receive"},
        "INVALID_QUOTE",
        "Unsupported currency or quote side",
        422,
    )
    try:
        n = Decimal(amount)
        require(n.is_finite() and 0 < n <= Decimal("1000000000000"), "INVALID_AMOUNT", "Invalid amount", 422)
    except Exception as exc:
        raise DomainError("INVALID_AMOUNT", "Invalid decimal amount", 422) from exc
    source, reference_date = "MOCK", None
    snapshot = json_snapshot()
    ecb = {r["quote"]: Decimal(str(r["rate"])) for r in snapshot["rates"]}
    ecb["EUR"] = Decimal(1)
    if from_currency in ecb and to_currency in ecb:
        mid = ecb[to_currency] / ecb[from_currency]
        source = "ECB"
        reference_date = snapshot["rates"][0]["date"]
    else:
        mid = BOARD[from_currency] / BOARD[to_currency]
    rate = (mid * Decimal("0.99")).quantize(Decimal(".00000001"))
    fee = Decimal("25000") if from_currency == "VND" else Decimal("10")
    send = n if side == "send" else (n / rate + fee).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
    require(send > fee, "INVALID_AMOUNT", "Amount below fee", 422)
    receive = (send - fee) * rate if side == "send" else n
    return {
        "rate": str(rate),
        "midRate": str(mid),
        "marginPct": "1.00",
        "source": source,
        "quotedAt": s["now"],
        "send": money(send, from_currency),
        "receive": money(receive, to_currency),
        "fees": money(fee, from_currency),
        "referenceDate": reference_date,
        "execution": "MOCK",
    }


def json_snapshot():
    return json.loads(Path(__file__).with_name("ecb_snapshot.json").read_text(encoding="utf-8"))


def create_mandate(s, user, body):
    parent(user)
    require(not s["frozen"].get(user["familyId"]), "FROZEN", "Family frozen")
    require(dt(body["expiresAt"]) > dt(s["now"]), "INVALID_TIME", "Mandate must expire in the future", 422)
    require(
        body["cap"]["currency"] == "KRW" and Decimal(body["cap"]["amount"]) > 0,
        "INVALID_CAP",
        "Tuition cap must be positive KRW",
        422,
    )
    require(
        (
            body["purpose"] == "tuition"
            and body["payeeRule"]["type"] == "credentialed"
            and body["payeeRule"].get("issuer") == s["issuer"]
        )
        or (
            body["purpose"] == "rent"
            and body["payeeRule"]["type"] == "name_checked"
            and body["payeeRule"].get("payeeId") in s["bankPayees"]
            and body["period"] == "monthly"
        ),
        "UNSUPPORTED_MANDATE",
        "Use the trusted tuition issuer or the bank name-checked monthly landlord",
        422,
    )
    require(
        body.get("cosignerId") in {None, "usr_mother_lan"}
        and (body.get("cosignerId") is None or user["familyId"] == "fam_minh"),
        "INVALID_COSIGNER",
        "Invalid co-signer",
        422,
    )
    row = {
        **body,
        "id": uid("mdt"),
        "spent": money(0, "KRW"),
        "status": "pending_signature",
        "_family": user["familyId"],
        "_owner": user["id"],
    }
    row["hash"] = digest({k: v for k, v in row.items() if k not in {"spent", "status"}})
    row["_signedBody"] = {k: copy.deepcopy(v) for k, v in row.items() if k not in {"spent", "status", "hash"}}
    s["mandates"][row["id"]] = row
    audit(s, user["id"], "mandate_created", "Mandate awaiting signature", mandateHash=row["hash"])
    return row


def mandate_valid(s, row):
    return bool(
        row
        and row["status"] == "active"
        and dt(row["expiresAt"]) > dt(s["now"])
        and digest(row["_signedBody"]) == row["hash"]
        and all(row.get(k) == v for k, v in row["_signedBody"].items())
    )


def record_operation(s, actor, action, ref, result):
    s["operations"].append(
        {"at": s["now"], "actor": actor, "action": action, "requestId": ref, "result": result, "mock": True}
    )


def event(s, family, type_, data):
    s["events"].append({"id": len(s["events"]) + 1, "_family": family, "type": type_, "data": data})


def timeline(s, row, code, actor, **params):
    seq = audit(s, actor, code, code.replace("_", " "), reference=row["id"], **params)
    row["timeline"].append({"at": s["now"], "code": code, "actor": actor, "params": params, "auditSeq": seq})


def pack(s, family):
    corridor = "CN→KR" if family == "fam_wang" else "VN→KR"
    kinds = {d["kind"] for d in s["documents"].values() if d["_family"] == family and not d["warnings"]}
    # Identity and relationship are bank-held synthetic KYC records, never model context.
    kinds |= {"identity", "relationship"}
    return {
        "corridor": corridor,
        "rulesVersion": s["rulesVersion"],
        "documents": [
            {"kind": kind, "status": "ready" if kind in kinds else "missing"}
            for kind in s["rules"]["corridors"][corridor]["required"]
        ],
        "ruleChecks": [
            {"ruleId": r, "code": "MOCK_BANK_DOCUMENT_CHECK", "severity": "info", "params": {}}
            for r in s["rules"]["corridors"][corridor]["rules"]
        ],
    }


def payment_context(s, family, mandate, invoice, ready=True):
    history = [
        r
        for r in s.get("fxPurchases", [])
        if r["family"] == family
        and not r.get("reversed")
        and r["beneficiary"] == invoice["id"]
        and r["purpose"] == "tuition"
        and dt(s["now"]) - timedelta(days=365) <= dt(r["at"]) <= dt(s["now"])
    ]
    return Context(
        frozen=s["frozen"].get(family, False),
        mandate_valid=mandate_valid(s, mandate),
        amount=Decimal(invoice["amount"]),
        cap=Decimal(mandate["cap"]["amount"]) - Decimal(mandate["spent"]["amount"])
        if mandate
        else Decimal(0),
        invoice_remaining=Decimal(invoice.get("total", invoice["amount"]))
        - Decimal(s["invoicePaid"].get(invoice["invoiceRef"], "0")),
        documents_ready=ready,
        first_payment=not any(
            p["_family"] == family and p["status"] in {"sent", "matched"} for p in s["payments"].values()
        ),
        sanctions=s.get("screenings", {}).get(family, {}).get("status", "unavailable"),
        structuring=family == "fam_wang" and is_structuring(history),
    )


def resolve_invoice_action(s, invoice, instalment=False):
    result = copy.deepcopy(invoice)
    result["total"] = invoice["amount"]
    paid = Decimal(s["invoicePaid"].get(invoice["invoiceRef"], "0"))
    if instalment:
        cumulative = Decimal(0)
        for index, part in enumerate(invoice["instalments"]):
            if cumulative == paid:
                result["amount"] = part
                result["tranche"] = index
                result["paymentWindow"] = invoice.get(
                    "instalmentSchedule", [{}] * len(invoice["instalments"])
                )[index].get("paymentWindow", invoice.get("registrationWindow"))
                if invoice.get("instalmentSchedule"):
                    result["dueAt"] = invoice["instalmentSchedule"][index]["dueAt"]
                return result
            cumulative += Decimal(part)
        raise DomainError("INVOICE_SETTLED", "No unpaid issuer-defined instalment", 409)
    result["amount"] = str(Decimal(invoice["amount"]) - paid)
    require(Decimal(result["amount"]) > 0, "INVOICE_SETTLED", "Invoice already paid", 409)
    result["tranche"] = "remaining"
    cumulative = Decimal(0)
    for entry in invoice.get("instalmentSchedule", []):
        cumulative += Decimal(entry["amount"])
        if cumulative > paid:
            result["dueAt"] = entry["dueAt"]
            result["paymentWindow"] = entry.get("paymentWindow", invoice.get("registrationWindow"))
            break
    return result


def prepare_payment(s, user, issuer, instalment=False):
    family = user["familyId"]
    require(user["role"] in {"parent", "student"}, "ROLE_REQUIRED", "Family member required")
    invoice = resolve_invoice_action(s, verified_invoice(s, family, issuer), instalment)
    require_tuition_open(s, family, invoice["invoiceRef"])
    require(
        invoice["version"] == INVOICE_VERSION,
        "DEMO_SEED_REFRESH_REQUIRED",
        "Reset this visitor sandbox to use the tuition-only signed seed",
        409,
    )
    for approval in s["approvals"].values():
        if (
            approval["_family"] == family
            and approval["action"] in {"first_payment", "payment"}
            and approval["status"] == "pending"
            and (dt(s["now"]) - dt(approval["disclosure"]["fx"]["quotedAt"])).total_seconds() > 60
        ):
            approval["status"] = "expired"
            audit(
                s,
                "bank",
                "quote_expired",
                "New quote and consent required",
                consentHash=approval["consentHash"],
            )
        if (
            approval["_family"] == family
            and approval["action"] in {"first_payment", "payment"}
            and approval["status"] == "pending"
            and approval["rawAction"].get("tranche") == invoice["tranche"]
            and dt(approval["expiresAt"]) > dt(s["now"])
            and (dt(s["now"]) - dt(approval["disclosure"]["fx"]["quotedAt"])).total_seconds() <= 60
        ):
            existing_decision = evaluate(
                payment_context(
                    s,
                    family,
                    s["mandates"].get(approval["rawAction"]["mandateId"]),
                    invoice,
                    all(d["status"] == "ready" for d in pack(s, family)["documents"]),
                )
            )
            if existing_decision.executable:
                return approval, existing_decision
    mandates = [
        m
        for m in s["mandates"].values()
        if m["_family"] == family and m["purpose"] == "tuition" and mandate_valid(s, m)
    ]
    mandate = mandates[-1] if mandates else None
    from .study import require_payment_window

    require_payment_window(s, invoice)
    outbound = pack(s, family)
    decision = evaluate(
        payment_context(
            s, family, mandate, invoice, all(d["status"] == "ready" for d in outbound["documents"])
        )
    )
    audit(
        s,
        "agent",
        "disposition",
        decision.code,
        [decision.rule],
        provenance={"amount": "verified_issuer", "payee": "verified_issuer"},
    )
    if not decision.executable:
        return None, decision
    currency = "CNY" if family == "fam_wang" else "VND"
    q = quote(s, currency, "KRW", invoice["amount"], "receive")
    raw = {
        "amount": q["send"]["amount"],
        "currency": currency,
        "payeeAccountHash": invoice["accountHash"],
        "payeeName": invoice["name"],
        "fxRate": q["rate"],
        "fees": q["fees"],
        "receive": q["receive"],
        "purpose": "tuition",
        "mandateId": mandate["id"],
        "invoiceRef": invoice["invoiceRef"],
        "tranche": invoice["tranche"],
        "nonce": uid("nonce"),
        "expiry": later(s, hours=24),
        "payerId": "acct_parent_wang" if family == "fam_wang" else "acct_parent_minh",
    }
    approval = {
        "id": uid("apr"),
        "status": "pending",
        "action": "first_payment" if decision.result == "ESCALATE" else "payment",
        "rawAction": raw,
        "consentHash": digest(raw),
        "disclosure": {
            "send": q["send"],
            "fx": {k: q[k] for k in ("rate", "midRate", "marginPct", "source", "quotedAt")},
            "fees": q["fees"],
            "receive": q["receive"],
            "cancelUntil": later(s, minutes=30),
        },
        "payee": payee(s, family),
        "invoice": {
            "ref": invoice["invoiceRef"],
            "issuer": invoice["name"],
            "term": invoice.get("term", "Spring 2027"),
            "dueDate": invoice["dueAt"],
            "lines": invoice.get("lines", []),
            "total": money(invoice["total"], "KRW"),
            "registrationWindow": invoice.get("registrationWindow"),
            "instalmentSchedule": invoice.get("instalmentSchedule", []),
            "separateObligations": invoice.get("separateObligations", []),
        },
        "approverId": next(
            u["id"] for u in s["users"].values() if u["familyId"] == family and u["role"] == "parent"
        ),
        "pack": outbound,
        "risk": {"score": 0, "features": decision.as_dict()["reasons"]},
        "requestedBy": "agent",
        "createdAt": s["now"],
        "expiresAt": raw["expiry"],
        "_family": family,
    }
    s["approvals"][approval["id"]] = approval
    audit(
        s,
        "agent",
        "approval_created",
        "Exact tuition action prepared",
        consentHash=approval["consentHash"],
        screenHash=digest(public(approval)),
    )
    if decision.result == "AUTO_EXECUTE":
        approval["resultRef"] = bank_execute(s, approval, issuer)["id"]
        approval["status"] = "approved"
        audit(
            s, "agent", "l2_execution", "Issuer-defined instalment executed within signed mandate", ["L2-01"]
        )
        issuer.chain.anchor(s)
    else:
        event(s, family, "approval_created", public(approval))
    return approval, decision


def bank_execute(s, approval, issuer):
    require(issuer.chain.available(), "CHAIN_UNAVAILABLE", "Bank writes paused until chain recovery", 503)
    family = approval["_family"]
    raw = approval["rawAction"]
    require_tuition_open(s, family, raw["invoiceRef"])
    require(
        raw["purpose"] == "tuition" and raw["currency"] == ("CNY" if family == "fam_wang" else "VND"),
        "BINDING_MISMATCH",
        "Payer currency or purpose does not match bank record",
    )
    require(digest(raw) == approval["consentHash"], "CONSENT_MISMATCH", "Action changed after consent")
    require(dt(raw["expiry"]) > dt(s["now"]), "APPROVAL_EXPIRED", "Approval expired", 409)
    require(
        (dt(s["now"]) - dt(approval["disclosure"]["fx"]["quotedAt"])).total_seconds() <= 60,
        "QUOTE_EXPIRED",
        "Quote older than 60 seconds; request a new approval",
        409,
    )
    invoice = resolve_invoice_action(
        s, verified_invoice(s, family, issuer), raw.get("tranche") != "remaining"
    )
    require(raw.get("tranche") == invoice["tranche"], "BINDING_MISMATCH", "Instalment sequence mismatch")
    require(
        invoice["version"] == INVOICE_VERSION,
        "DEMO_SEED_REFRESH_REQUIRED",
        "Historical bundle cannot create a new tuition transfer",
        409,
    )
    mandate = s["mandates"][raw["mandateId"]]
    from .study import require_payment_window

    require_payment_window(s, invoice)
    outbound = pack(s, family)
    decision = evaluate(
        payment_context(
            s, family, mandate, invoice, all(d["status"] == "ready" for d in outbound["documents"])
        )
    )
    require(decision.executable, message=decision.code, rule=decision.rule)
    require(
        raw["payeeAccountHash"] == invoice["accountHash"]
        and raw["payeeName"] == invoice["name"]
        and raw["receive"] == money(invoice["amount"], "KRW"),
        "BINDING_MISMATCH",
        "Instruction does not match signed issuer record",
    )
    # Recompute the full bank quote, not just its consent hash.
    q = quote(s, raw["currency"], "KRW", invoice["amount"], "receive")
    require(
        raw["amount"] == q["send"]["amount"] and raw["fxRate"] == q["rate"] and raw["fees"] == q["fees"],
        "BINDING_MISMATCH",
        "Bank quote binding failed",
    )
    grant_id = approval.get("_grant")
    if grant_id:
        grant = s["grants"][grant_id]
    else:
        grant_id = uid("grt")
        grant = {
            "consentHash": approval["consentHash"],
            "expiresAt": later(s, minutes=10),
            "used": False,
            "revoked": False,
            "_family": family,
        }
        s["grants"][grant_id] = grant
        approval["_grant"] = grant_id
    require(not grant["used"] and not grant["revoked"] and dt(grant["expiresAt"]) > dt(s["now"]))
    require(grant["consentHash"] == digest(raw), "GRANT_MISMATCH", "Bank rejected consent binding")
    payer = next(u for u in s["users"].values() if u["familyId"] == family and u["role"] == "parent")
    account = payer["accounts"][0]
    require(raw["payerId"] == account["id"], "PAYER_MISMATCH", "Original payer binding failed")
    debit = Decimal(raw["amount"])
    require(
        Decimal(account["balance"]["amount"]) >= debit, "INSUFFICIENT_FUNDS", "MOCK balance insufficient", 409
    )
    grant["used"] = True
    account["balance"] = money(Decimal(account["balance"]["amount"]) - debit, raw["currency"])
    mandate["spent"] = money(Decimal(mandate["spent"]["amount"]) + Decimal(invoice["amount"]), "KRW")
    if family == "fam_wang":
        snapshot = json_snapshot()
        rates = {r["quote"]: Decimal(str(r["rate"])) for r in snapshot["rates"]}
        usd = debit / rates["CNY"] * rates["USD"]
        prior = sum(
            Decimal(r["amount"])
            for r in s["fxPurchases"]
            if r["payer"] == account["id"] and not r.get("reversed") and dt(r["at"]).year == dt(s["now"]).year
        )
        s["fxPurchases"].append(
            {
                "payer": account["id"],
                "family": family,
                "beneficiary": invoice["id"],
                "purpose": "tuition",
                "amount": str(usd),
                "remaining": str(max(Decimal(0), Decimal(50000) - prior)),
                "at": s["now"],
            }
        )
    s["invoicePaid"][invoice["invoiceRef"]] = str(
        Decimal(s["invoicePaid"].get(invoice["invoiceRef"], "0")) + Decimal(invoice["amount"])
    )
    payment = {
        "id": uid("pay"),
        "status": "sent",
        "send": money(raw["amount"], raw["currency"]),
        "receive": raw["receive"],
        "payee": payee(s, family),
        "mandateId": mandate["id"],
        "approvalId": approval["id"],
        "invoiceRef": invoice["invoiceRef"],
        "timeline": [],
        "_family": family,
        "_payer": account["id"],
        "createdAt": s["now"],
        "purpose": raw["purpose"],
        "fees": raw["fees"],
        "cancelUntil": later(s, minutes=30),
        "_cancelUntil": later(s, minutes=30),
        "_consentHash": digest(raw),
    }
    s["payments"][payment["id"]] = payment
    if family == "fam_wang":
        s["fxPurchases"][-1]["paymentId"] = payment["id"]
    timeline(s, payment, "payment_executed", "bank", consentHash=digest(raw), grantId=grant_id)
    record_operation(s, "bank", "payment_executed", payment["id"], "debited_held_MOCK")
    event(s, family, "payment_updated", public(payment))
    return payment


def cancel(s, payment, user, actor="parent"):
    parent(user)
    require(
        payment["status"] == "sent" and dt(s["now"]) < dt(payment["_cancelUntil"]),
        "CANCEL_WINDOW_CLOSED",
        "Payment cannot be cancelled",
        409,
    )
    require(
        not any(r["paymentId"] == payment["id"] for r in s["refunds"].values()),
        "REFUND_ACTIVE",
        "Refund already active",
        409,
    )
    account = user["accounts"][0]
    require(account["id"] == payment["_payer"])
    account["balance"] = money(
        Decimal(account["balance"]["amount"]) + Decimal(payment["send"]["amount"]), account["currency"]
    )
    mandate = s["mandates"][payment["mandateId"]]
    mandate["spent"] = money(
        Decimal(mandate["spent"]["amount"]) - Decimal(payment["receive"]["amount"]), "KRW"
    )
    s["invoicePaid"][payment["invoiceRef"]] = str(
        Decimal(s["invoicePaid"].get(payment["invoiceRef"], "0")) - Decimal(payment["receive"]["amount"])
    )
    for purchase in s["fxPurchases"]:
        if purchase.get("paymentId") == payment["id"]:
            purchase["reversed"] = True
    payment["status"] = "cancelled"
    timeline(s, payment, "payment_cancelled", actor)
    record_operation(s, "bank", "cancel", payment["id"], "reversed")
    event(s, user["familyId"], "payment_updated", public(payment))


def require_tuition_open(s, family, invoice_ref):
    stopped = s.get("admissionDispositions", {}).get(family)
    require(
        (not stopped or stopped["invoiceRef"] != invoice_ref)
        and not any(
            d["_family"] == family and d["kind"] == "refusal" and not d["warnings"]
            for d in s["documents"].values()
        ),
        "ADMISSION_RECONFIRMATION_REQUIRED",
        "Visa refused: ask the university about withdrawal or a new signed admission before paying",
        409,
    )


def refusal_before_payment(s, user, document, issuer):
    """Local documentary notice stops tuition authority; it never claims a refund or withdraws admission."""
    family = user["familyId"]
    require(user["role"] == "student", "ROLE_REQUIRED", "Student refusal evidence required")
    require(
        document["_family"] == family and document["kind"] == "refusal" and not document["warnings"],
        "REFUSAL_DOCUMENT_REQUIRED",
        "Clean family refusal evidence required",
        409,
    )
    require(
        not any(
            p["_family"] == family and p.get("purpose") == "tuition" and p["status"] not in {"cancelled"}
            for p in s["payments"].values()
        ),
        "PAYMENT_EXISTS",
        "Use the existing payment or refund case",
        409,
    )
    previous = s.setdefault("admissionDispositions", {}).get(family)
    if previous:
        return previous
    invoice = issuer.verify(s["credentials"][family]["jwt"], int(dt(s["now"]).timestamp()))
    cancelled = []
    for approval in s["approvals"].values():
        if (
            approval["_family"] == family
            and approval["action"] in {"first_payment", "payment"}
            and approval["status"] == "pending"
            and not approval.get("_riskOnly")
        ):
            approval.update(status="rejected", rejectionReason="VISA_REFUSED_BEFORE_PAYMENT")
            cancelled.append(approval["id"])
            event(s, family, "approval_updated", public(approval))
    for thread in s["threads"].values():
        if thread["_family"] == family and thread.get("_pendingIntent") == "pay":
            thread["_pendingIntent"] = None
    for grant in s["grants"].values():
        if grant.get("approvalId") in cancelled:
            grant["used"] = True
    row = {
        "status": "refused_before_payment",
        "code": "VISA_REFUSED_BEFORE_PAYMENT",
        "recordedAt": s["now"],
        "invoiceRef": invoice["invoiceRef"],
        "moneyAtRisk": False,
        "refundRequired": False,
        "tuitionStopped": True,
        "cancelledApprovalIds": cancelled,
        "admissionAction": "ask_university_to_withdraw_or_reapply_next_intake",
        "admissionWithdrawn": False,
        "reconfirmation": "new_university_signed_admission_and_invoice_required",
        "parentNotice": {
            "status": "available_in_family_app_MOCK",
            "at": s["now"],
            "recipientIds": [
                u["id"] for u in s["users"].values() if u["familyId"] == family and u["role"] == "parent"
            ],
            "channel": "family_app_only",
            "externalMessageSent": False,
        },
    }
    s["admissionDispositions"][family] = row
    audit(
        s,
        user["id"],
        "visa_refused_before_payment",
        "Unpaid tuition stopped; parent notice recorded; no refund or withdrawal submitted",
        familyId=family,
        evidenceHash=document["sha256"],
        cancelledApprovalIds=cancelled,
    )
    event(s, family, "admission_updated", public(row))
    return row


def prepare_refund(s, user, issuer):
    require(user["role"] == "student", "ROLE_REQUIRED", "Student must submit refusal evidence")
    family = user["familyId"]
    payments = [
        p
        for p in s["payments"].values()
        if p["_family"] == family and p["status"] == "matched" and p.get("purpose") == "tuition"
    ]
    require(bool(payments), "PAYMENT_REQUIRED", "No paid invoice", 409)
    payment = payments[-1]
    existing = [
        a
        for a in s["approvals"].values()
        if a["action"] == "refund_claim" and a["rawAction"]["paymentId"] == payment["id"]
    ]
    if existing:
        previous = existing[-1]
        require(
            "paperwork" in previous["rawAction"],
            "SEED_REFRESH_REQUIRED",
            "Legacy refund consent cannot be repriced; reset the synthetic sandbox",
            409,
        )
        if previous["status"] == "approved" or (
            previous["status"] == "pending"
            and dt(previous["expiresAt"]) > dt(s["now"])
            and (
                previous["rawAction"]["paperwork"]["eligibility"] != "before_start_full_unused"
                or dt(s["now"]) < dt(previous["rawAction"]["paperwork"]["policy"]["classesStart"])
            )
        ):
            return previous
        if previous["status"] == "pending":
            previous["status"] = "rejected"
            audit(
                s,
                "agent",
                "refund_draft_superseded",
                "Calendar eligibility changed; fresh consent required",
                approvalId=previous["id"],
            )
            event(s, family, "approval_updated", public(previous))
    # Preparing forms is read-only with respect to money. Verify issuer signature
    # locally even during an RPC outage; approval submission still requires chain.
    credential = s["credentials"][family]
    require(credential["status"] == "valid", rule="P-01")
    invoice = issuer.verify(credential["jwt"], int(dt(s["now"]).timestamp()))
    require(
        invoice["familyId"] == family and "refundPolicy" in invoice,
        "SEED_REFRESH_REQUIRED",
        "Reset the synthetic sandbox to adopt the new refund contract",
        409,
    )
    evidence = [
        d
        for d in s["documents"].values()
        if d["_family"] == family and d["kind"] == "refusal" and not d["warnings"]
    ]
    require(bool(evidence), "REFUSAL_REQUIRED", "A verified MOCK denial letter is required", 409)
    payer = next(
        u for u in s["users"].values() if u["accounts"] and u["accounts"][0]["id"] == payment["_payer"]
    )
    paperwork = refund_plan(s["now"], payment, invoice, user["id"], payer["accounts"][0], evidence[-1]["id"])
    paperwork["evidenceHashes"] = {
        "visaDenial": evidence[-1]["sha256"],
        "invoiceCredential": credential["hash"],
    }
    raw = {
        "paperwork": paperwork,
        "paymentId": payment["id"],
        "destinationAccountId": payment["_payer"],
        "purpose": "refund_claim",
        "refundAmount": copy.deepcopy(payment["receive"]),
        "nonce": uid("nonce"),
        "expiry": later(s, hours=24),
    }
    a = {
        "id": uid("apr"),
        "status": "pending",
        "action": "refund_claim",
        "rawAction": raw,
        "consentHash": digest(raw),
        "risk": {"score": 0, "features": []},
        "requestedBy": "agent",
        "createdAt": s["now"],
        "expiresAt": raw["expiry"],
        "_family": family,
        "_student": user["id"],
        "approverId": user["id"],
    }
    a["refundSummary"] = {
        "action": "student_sign_withdrawal_and_tuition_refund",
        "claimAmount": payment["receive"],
        "deadline": paperwork["deadline"],
        "classesStart": paperwork["policy"]["classesStart"],
        "signBefore": paperwork["policy"]["classesStart"]
        if paperwork["eligibility"] == "before_start_full_unused"
        else None,
        "signerId": user["id"],
        "destination": {
            "bank": payer["accounts"][0]["bank"],
            "maskedNumber": payer["accounts"][0]["maskedNumber"],
            "originalPayerOnly": True,
        },
        "estimate": {
            **refund_reconciliation(payment, payment["send"]["currency"]),
            "kind": "MOCK_ESTIMATE",
            "asOf": s["now"],
        }
        if paperwork["eligibility"] == "before_start_full_unused"
        else None,
        "separateObligationsExcluded": ["dormitory", "NHIS"],
        "details": paperwork["policy"],
    }
    s["approvals"][a["id"]] = a
    audit(s, "agent", "refund_approval_created", "Student consent required", consentHash=a["consentHash"])
    event(s, family, "approval_created", public(a))
    return a


def file_refund(s, approval):
    raw = approval["rawAction"]
    payment = s["payments"][raw["paymentId"]]
    require(
        raw.get("refundAmount") == payment["receive"],
        "BINDING_MISMATCH",
        "Refund amount must match original payment",
    )
    require(
        raw["destinationAccountId"] == payment["_payer"],
        rule="LX-03",
        message="Refund only to original payer",
    )
    payer = next(
        u for u in s["users"].values() if u["accounts"] and u["accounts"][0]["id"] == payment["_payer"]
    )
    paperwork = raw["paperwork"]
    require(
        paperwork["eligibility"] != "before_start_full_unused"
        or dt(s["now"]) < dt(paperwork["policy"]["classesStart"]),
        "REFUND_POLICY_CHANGED",
        "Classes have started; prepare a new degree-office assessment",
        409,
    )
    require(paperwork["destination"]["accountId"] == payment["_payer"], rule="LX-03")
    row = {
        "paperwork": copy.deepcopy(paperwork),
        "policy": copy.deepcopy(paperwork["policy"]),
        "claimAmount": copy.deepcopy(raw["refundAmount"]),
        "classesStart": paperwork["policy"]["classesStart"],
        "eligibility": paperwork["eligibility"],
        "id": uid("ref"),
        "paymentId": payment["id"],
        "status": "requested",
        "deadline": paperwork["deadline"],
        "destination": copy.deepcopy(payer["accounts"][0]),
        "timeline": [],
        "_family": payment["_family"],
        "_started": s["now"],
        "_timers": [],
    }
    for form in row["paperwork"]["documents"][:2]:
        form.update(status="signed", consentHash=approval["consentHash"], signedAt=s["now"])
    if row["eligibility"] == "manual_degree_assessment":
        row["status"] = "manual_review"
    s["refunds"][row["id"]] = row
    for code, actor in [
        ("refusal_reported", "student"),
        ("evidence_verified_MOCK", "bursar"),
        ("refund_requested", "agent"),
    ]:
        timeline(s, row, code, actor)
    record_operation(s, "bursar", "refund_request", row["id"], "accepted_MOCK")
    event(s, row["_family"], "refund_updated", refund_view(s, row))
    return row


def refund_view(s, row):
    """Current bank presentation; never change consent-bound paperwork."""
    result = public(row)
    payment = s["payments"][row["paymentId"]]
    account = next(a for u in s["users"].values() for a in u["accounts"] if a["id"] == payment["_payer"])
    require(row["destination"]["id"] == account["id"], rule="LX-03")
    result["destination"] = copy.deepcopy(account)
    if result.get("followUp", {}).get("escalation"):
        details = result["followUp"]["escalation"]
        approval = s["approvals"][details["approvalId"]]
        if approval["status"] in {"rejected", "expired"}:
            details["status"] = approval["status"]
    result["estimate"] = (
        {**refund_reconciliation(payment, account["currency"]), "kind": "MOCK_ESTIMATE", "asOf": s["now"]}
        if row.get("eligibility") == "before_start_full_unused"
        and row.get("policy", {}).get("id") == POLICY["id"]
        and not row.get("reconciliation")
        else None
    )
    return result


def advance(s, days=0, hours=0):
    s["now"] = later(s, days=days, hours=hours)
    final_now = s["now"]
    for payment in sorted(s["payments"].values(), key=lambda p: p.get("_cancelUntil", final_now)):
        if payment["status"] == "sent" and dt(payment["_cancelUntil"]) <= dt(final_now):
            s["now"] = payment["_cancelUntil"]
            if payment.get("purpose") == "rent":
                payment["status"] = "matched"
                timeline(s, payment, "rent_matched", "bank")
                record_operation(s, "bank", "rent_matched", payment["id"], "delivered_MOCK")
            else:
                payment["status"] = "received_by_bursar"
                timeline(s, payment, "received_by_bursar", "bursar")
                record_operation(s, "bursar", "received_by_bursar", payment["id"], "PAID")
                payment["status"] = "matched"
                timeline(s, payment, "payment_matched", "bursar")
                record_operation(s, "bursar", "payment_matched", payment["id"], "PAID")
            payment.pop("cancelUntil", None)
            event(s, payment["_family"], "payment_updated", public(payment))
    s["now"] = final_now
    for a in s["approvals"].values():
        if a["status"] == "pending" and dt(a["expiresAt"]) <= dt(s["now"]):
            a["status"] = "expired"
    for r in s["refunds"].values():
        if r["status"] in {"reconciled", "manual_review"}:
            continue
        if not r.get("policy"):
            # Keep historical contracts readable, never silently reprice a live
            # old claim using new fee or timing assumptions. Demo reset is explicit.
            continue
        elapsed = (dt(s["now"]) - dt(r["_started"])).total_seconds() / 86400
        # Semester-relative settlement; transport and receipt finish by the promise.
        until_promise = (dt(r["deadline"]) - dt(r["_started"])).total_seconds() / 86400
        stages = [
            (1, "acknowledged"),
            (3, "approved"),
            (until_promise - 2, "sent"),
            (until_promise, "received"),
            (until_promise, "reconciled"),
        ]
        order = ["requested"] + [v for _, v in stages]
        milestones = stages + [
            (7, "timer:refund_nudge"),
            (until_promise, "timer:escalation_draft_requires_student_approval"),
            (until_promise, "timer:refund_deadline_breach"),
        ]
        for day, status in sorted(milestones, key=lambda v: v[0]):
            if r["status"] == "reconciled":
                break
            if elapsed < day:
                continue
            s["now"] = iso(dt(r["_started"]) + timedelta(days=day))
            if status.startswith("timer:"):
                if status not in r["_timers"]:
                    r["_timers"].append(status)
                    timeline(s, r, status[6:], "agent")
                continue
            if s.get("refundDelay") and status in {"sent", "received", "reconciled"}:
                continue
            if elapsed >= day and order.index(r["status"]) < order.index(status):
                r["status"] = status
                timeline(
                    s, r, "refund_" + status, "bank" if status in {"received", "reconciled"} else "bursar"
                )
                if status == "received":
                    p = s["payments"][r["paymentId"]]
                    payer = next(
                        u
                        for u in s["users"].values()
                        if u["accounts"] and u["accounts"][0]["id"] == p["_payer"]
                    )
                    require(r["destination"]["id"] == p["_payer"], rule="LX-03")
                    account = payer["accounts"][0]
                    currency = account["currency"]
                    r["reconciliation"] = refund_reconciliation(p, currency)
                    back = Decimal(r["reconciliation"]["receivedBack"]["amount"])
                    account["balance"] = money(Decimal(account["balance"]["amount"]) + back, currency)
                    r["destination"] = copy.deepcopy(account)
                    record_operation(s, "bank", "refund_credit", r["id"], "original_payer_only")
        s["now"] = final_now
        from .escalations import follow_up

        follow_up(s, r)
        event(s, r["_family"], "refund_updated", refund_view(s, r))
    audit(s, "system", "clock_advanced", "Simulated clock advanced", days=days, hours=hours)


def execute_rent(s, user, issuer, allow_cancelled=False):
    """L2 rent: amount and destination resolve from a bank-held standing instruction."""
    family = user["familyId"]
    from .study import rent_setup

    require(
        not rent_setup(s, user)["missing"],
        "RENT_PREREQUISITES_REQUIRED",
        "Verified rental agreement and signed rent mandate required",
        409,
    )
    mandates = [
        m
        for m in s["mandates"].values()
        if m["_family"] == family and m["purpose"] == "rent" and mandate_valid(s, m)
    ]
    require(bool(mandates), "MANDATE_REQUIRED", "A signed monthly rent mandate is required", 409)
    mandate = mandates[-1]
    record = s["bankPayees"][mandate["payeeRule"]["payeeId"]]
    month = s["now"][:7]
    invoice_ref = "RENT-" + family + "-" + month
    existing = [
        p
        for p in s["payments"].values()
        if p["invoiceRef"] == invoice_ref and (p["status"] != "cancelled" or not allow_cancelled)
    ]
    if existing:
        return existing[0], None
    screening = issuer.screening.screen(record["name"])
    amount = Decimal(record["amount"])
    decision = evaluate(
        Context(
            frozen=s["frozen"].get(family, False),
            mandate_valid=mandate_valid(s, mandate),
            payee_valid=record["nameCheck"] == "match",
            name_match=record["nameCheck"],
            provenance=("bank_record",),
            amount=amount,
            cap=Decimal(mandate["cap"]["amount"]),
            invoice_remaining=amount,
            sanctions=screening["status"],
            first_payment=False,
            chain_available=issuer.chain.available(),
        )
    )
    audit(s, "agent", "rent_disposition", decision.code, [decision.rule], screening=screening)
    require(decision.result == "AUTO_EXECUTE", message=decision.code, rule=decision.rule)
    currency = "CNY" if family == "fam_wang" else "VND"
    q = quote(s, currency, "KRW", record["amount"], "receive")
    payer = next(u for u in s["users"].values() if u["familyId"] == family and u["role"] == "parent")
    account = payer["accounts"][0]
    raw = {
        "amount": q["send"]["amount"],
        "currency": currency,
        "payeeAccountHash": record["accountHash"],
        "payeeName": record["name"],
        "receive": q["receive"],
        "fees": q["fees"],
        "fxRate": q["rate"],
        "purpose": "rent",
        "mandateId": mandate["id"],
        "invoiceRef": invoice_ref,
        "nonce": uid("nonce"),
        "expiry": later(s, minutes=10),
        "payerId": account["id"],
    }
    consent = digest(raw)
    grant_id = uid("grt")
    s["grants"][grant_id] = {
        "consentHash": consent,
        "expiresAt": raw["expiry"],
        "used": False,
        "revoked": False,
        "_family": family,
    }
    # The bank validates the instruction independently against its standing record.
    require(
        digest(raw) == s["grants"][grant_id]["consentHash"]
        and raw["payeeAccountHash"] == record["accountHash"]
        and raw["receive"]["amount"] == record["amount"]
        and mandate_valid(s, mandate)
    )
    debit = Decimal(raw["amount"])
    require(
        Decimal(account["balance"]["amount"]) >= debit, "INSUFFICIENT_FUNDS", "MOCK balance insufficient", 409
    )
    s["grants"][grant_id]["used"] = True
    account["balance"] = money(Decimal(account["balance"]["amount"]) - debit, currency)
    mandate["spent"] = money(amount, "KRW")
    s["invoicePaid"][invoice_ref] = record["amount"]
    p = {
        "id": uid("pay"),
        "status": "sent",
        "send": q["send"],
        "receive": q["receive"],
        "payee": {
            "id": record["id"],
            "name": record["name"],
            "institution": "Landlord (MOCK)",
            "verification": rent_setup(s, user)["landlord"]["verification"],
            "account": {"masked": "•••• 1193", "hashMatch": True},
            "credential": {"issuer": "Lotus Home Bank (MOCK)", "status": "none"},
            "nameCheck": "match",
        },
        "mandateId": mandate["id"],
        "invoiceRef": invoice_ref,
        "timeline": [],
        "_family": family,
        "_payer": account["id"],
        "createdAt": s["now"],
        "purpose": "rent",
        "fees": q["fees"],
        "cancelUntil": later(s, minutes=30),
        "_cancelUntil": later(s, minutes=30),
        "_consentHash": consent,
    }
    s["payments"][p["id"]] = p
    timeline(s, p, "rent_auto_executed", "bank", consentHash=consent, grantId=grant_id)
    record_operation(s, "bank", "rent_payment", p["id"], "debited_MOCK")
    event(s, family, "payment_updated", public(p))
    issuer.chain.anchor(s)
    return p, decision


def risk_review(s, user, score, features):
    family = user["familyId"]
    # Advisory only: neither co-sign nor waiting makes an unsafe payee executable.
    raw = {
        "purpose": "verify_scam_claim",
        "familyId": family,
        "nonce": uid("nonce"),
        "expiry": later(s, hours=48),
        "verificationRequired": True,
    }
    a = {
        "id": uid("apr"),
        "status": "cooling_off",
        "action": "payment",
        "rawAction": raw,
        "consentHash": digest(raw),
        "risk": {"score": score, "features": features},
        "cooling": {"until": later(s, hours=24), "cosignRequired": True, "cosignerId": "usr_mother_lan"},
        "requestedBy": "agent",
        "createdAt": s["now"],
        "expiresAt": raw["expiry"],
        "_family": family,
        "_riskOnly": True,
        "_cosigned": False,
    }
    s["approvals"][a["id"]] = a
    audit(
        s,
        "agent",
        "scam_cooling_started",
        "24-hour cooling and independent home co-sign required",
        ["S-02"],
        consentHash=a["consentHash"],
        features=features,
    )
    event(s, family, "approval_created", public(a))
    return a


def parse_document(s, user, filename, kind, content, parsed_text=None):
    require(user["role"] in {"student", "parent"}, "ROLE_REQUIRED", "Family member required")
    require(
        0 < len(content) <= 5 * 1024 * 1024, "DOCUMENT_SIZE", "File must be between 1 byte and 5 MiB", 413
    )
    if parsed_text is not None:
        text = parsed_text
    elif content.startswith(b"%PDF"):
        from io import BytesIO

        from pypdf import PdfReader

        try:
            reader = PdfReader(BytesIO(content), strict=True)
            require(len(reader.pages) <= 20, "DOCUMENT_SIZE", "At most 20 pages", 413)
            text = "\n".join(p.extract_text() or "" for p in reader.pages)
        except DomainError:
            raise
        except Exception as exc:
            raise DomainError("INVALID_DOCUMENT", "Cannot parse PDF", 422) from exc
    else:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DomainError("INVALID_DOCUMENT", "PDF or UTF-8 text required", 422) from exc
    family = user["familyId"]
    warnings = []
    lower = text.lower()
    suspicious = any(
        x in lower
        for x in (
            "ignore previous",
            "pre-approved",
            "new account",
            "15%",
            "system prompt",
            "refund agent",
            "proof-of-funds",
            "police",
            "bank details changed",
        )
    )
    if suspicious:
        warnings.append(
            {"ruleId": "T-01", "code": "UNTRUSTED_INSTRUCTIONS", "severity": "block", "params": {}}
        )
    fields = [{"name": "text", "value": text[:12000], "provenance": "untrusted_doc", "confidence": 0.9}]
    for key, pattern in [
        ("invoiceRef", r"HBU-2027-0042"),
        ("amount", r"\b\d{1,3}(?:,\d{3})+(?:\.\d{2})?\b"),
        ("account", r"MOCK-[A-Z0-9-]+\d{4,}"),
    ]:
        match = re.search(pattern, text)
        if match:
            fields.append(
                {"name": key, "value": match.group(), "provenance": "untrusted_doc", "confidence": 1.0}
            )
    parsed = {f["name"]: f["value"] for f in fields}
    if kind == "invoice" and not (
        {"invoiceRef", "amount", "account"}.issubset(parsed)
        and Decimal(parsed["amount"].replace(",", "")) == Decimal(TOTAL)
        and parsed["account"] == "MOCK-HANBIT-VA-883104"
    ):
        warnings.append(
            {"ruleId": "P-01", "code": "INVOICE_RECORD_MISMATCH", "severity": "block", "params": {}}
        )
    if kind == "admission" and not ("hanbit university" in lower and "admission" in lower):
        warnings.append(
            {"ruleId": "R-VN-02", "code": "ADMISSION_RECORD_MISMATCH", "severity": "block", "params": {}}
        )
    row = {
        "id": uid("doc"),
        "kind": kind,
        "filename": Path(filename).name,
        "sha256": hashlib.sha256(content).hexdigest(),
        "uploadedBy": user["id"],
        "fields": fields,
        "warnings": warnings,
        "_family": family,
    }
    # Hash original bytes (not text extraction or the PDF filename).
    if kind == "rental_agreement":
        from .fixtures import pdf

        row["_leaseVerified"] = content == pdf("rental_agreement") and not warnings
        if not row["_leaseVerified"]:
            warnings.append(
                {"ruleId": "P-02", "code": "RENTAL_AGREEMENT_UNVERIFIED", "severity": "block", "params": {}}
            )
    s["documents"][row["id"]] = row
    audit(
        s,
        user["id"],
        "document_parsed",
        "Document fields are tainted",
        documentHash=row["sha256"],
        provenance="untrusted_doc",
        warnings=warnings,
    )
    return row
