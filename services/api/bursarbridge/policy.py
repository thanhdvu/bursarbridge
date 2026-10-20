"""Pure disposition engine. No model, database, network or mutation capability."""

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class Context:
    action: str = "payment"
    trusted_agent: bool = True
    frozen: bool = False
    mandate_valid: bool = True
    payee_valid: bool = True
    name_match: str = "match"
    provenance: tuple = ("verified_issuer", "bank_record")
    amount: Decimal = Decimal("16000000")
    cap: Decimal = Decimal("16000000")
    invoice_remaining: Decimal = Decimal("16000000")
    structuring: bool = False
    documents_ready: bool = True
    sanctions: str = "clear"
    risk_score: int = 0
    first_payment: bool = True
    chain_available: bool = True


@dataclass(frozen=True)
class Decision:
    result: str
    rule: str
    code: str
    executable: bool = False
    features: list = field(default_factory=list)

    def as_dict(self):
        return {
            "result": self.result,
            "ruleIds": [self.rule],
            "reasons": [
                {
                    "ruleId": self.rule,
                    "code": self.code,
                    "severity": "block" if self.result == "DENY" else "warn",
                    "params": {},
                }
            ],
        }


NEVER = {"raise_limit", "registry_write", "refund_redirect", "crypto", "export_pii", "document_instruction"}


def evaluate(c: Context) -> Decision:
    if not c.trusted_agent:
        return Decision("DENY", "G-01", "UNKNOWN_AGENT")
    if c.action in NEVER:
        return Decision("DENY", "LX-03", "NEVER_ALLOWED")
    if c.frozen or not c.chain_available:
        return Decision("DENY", "G-02", "FROZEN_OR_UNAVAILABLE")
    if not c.mandate_valid:
        return Decision("ESCALATE", "M-01", "MANDATE_REQUIRED")
    if not c.payee_valid:
        return Decision("DENY", "P-01", "PAYEE_UNVERIFIED")
    if c.name_match != "match":
        return Decision("ESCALATE", "P-02", "NAME_MISMATCH")
    if any(p not in {"verified_issuer", "bank_record"} for p in c.provenance):
        return Decision("ESCALATE", "T-01", "TAINTED_PARAMETERS")
    if not c.amount.is_finite() or c.amount <= 0:
        return Decision("DENY", "A-00", "INVALID_AMOUNT")
    if c.amount > c.cap:
        return Decision("ESCALATE", "A-01", "CAP_EXCEEDED")
    if c.amount > c.invoice_remaining:
        return Decision("DENY", "R-VN-01", "FEE_NOTICE_EXCEEDED")
    if c.structuring:
        return Decision("DENY", "R-CN-02", "STRUCTURING")
    if not c.documents_ready:
        return Decision("ESCALATE", "R-VN-02", "DOCUMENTS_REQUIRED")
    if c.sanctions != "clear":
        return Decision("DENY", "S-01", "SANCTIONS_REVIEW")
    if c.risk_score >= 5:
        return Decision("ESCALATE", "S-02", "COOLING_AND_COSIGN_REQUIRED")
    if c.first_payment:
        return Decision("ESCALATE", "L3-01", "FIRST_PAYMENT", executable=True)
    return Decision("AUTO_EXECUTE", "L2-01", "WITHIN_MANDATE", executable=True)


def scam_score(text, new_payee=False, credentialed=True):
    text = text.lower()
    checks = [
        ("NEW_PAYEE", 2, new_payee),
        ("UNVERIFIED_PAYEE", 3, not credentialed),
        ("AUTHORITY", 3, any(x in text for x in ("police", "embassy", "immigration", "court"))),
        ("URGENCY_SECRECY", 2, any(x in text for x in ("urgent", "secret", "immediately"))),
        (
            "SAFE_ACCOUNT",
            3,
            any(x in text for x in ("safe account", "verification deposit", "proof-of-funds")),
        ),
        ("RAIL_MISMATCH", 3, any(x in text for x in ("crypto", "gift card"))),
    ]
    features = [
        {"ruleId": "S-02", "code": code, "severity": "warn", "params": {"weight": weight}}
        for code, weight, hit in checks
        if hit
    ]
    return sum(f["params"]["weight"] for f in features), features


def is_structuring(transfers, quota=Decimal("50000")):
    """Caller supplies the rolling-year, same beneficiary/purpose subset, in USD."""
    payers = {row["payer"] for row in transfers}
    return (
        len(payers) > 1
        and all(Decimal(row["amount"]) <= Decimal(row["remaining"]) for row in transfers)
        and sum(Decimal(row["amount"]) for row in transfers) > quota
    )
