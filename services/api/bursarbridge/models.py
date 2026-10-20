"""Public camelCase schemas. Decimal strings are never binary floats."""

from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Money(Model):
    amount: str
    currency: Literal["VND", "KRW", "CNY", "AUD", "USD", "EUR"]

    @field_validator("amount")
    @classmethod
    def valid_amount(cls, value):
        try:
            n = Decimal(value)
        except InvalidOperation:
            raise ValueError("Invalid decimal")
        if not n.is_finite() or n < 0 or n > Decimal("1000000000000") or n.as_tuple().exponent < -2:
            raise ValueError("Amount must be finite, nonnegative, at most 2 decimal places")
        return value


class Account(Model):
    id: str
    bank: str
    currency: str
    maskedNumber: str
    balance: Money
    swift: str | None = None


class User(Model):
    admissionDisposition: dict[str, Any] | None = None
    simulatedNow: str | None = None
    id: str
    name: str
    role: Literal["parent", "student", "cosigner", "judge"]
    locale: Literal["vi", "ko", "zh", "en"]
    familyId: str
    accounts: list[Account]
    frozen: bool = False
    frozenReason: str | None = None


class SessionIn(Model):
    persona: Literal["parent_minh", "student_linh", "mother_lan", "parent_wang", "student_hao", "judge"]


class SessionOut(Model):
    token: str
    user: User


class ResetOut(Model):
    ok: bool
    registrationStatus: Literal["pending", "ready"]
    anchorStatus: Literal["pending"]
    recovery: Literal["automatic_retry"]


class Reason(Model):
    ruleId: str
    code: str
    severity: Literal["info", "warn", "block"]
    params: dict[str, Any] = Field(default_factory=dict)


class DocumentField(Model):
    name: str
    value: str
    provenance: Literal["untrusted_doc", "verified_issuer", "bank_record", "user_input"]
    confidence: float


class Document(Model):
    id: str
    kind: str
    filename: str
    sha256: str
    uploadedBy: str
    fields: list[DocumentField]
    warnings: list[Reason]


class PayeeRule(Model):
    type: Literal["credentialed", "name_checked"]
    issuer: str | None = None
    payeeId: str | None = None


class MandateIn(Model):
    purpose: Literal["tuition", "rent", "living"]
    payeeRule: PayeeRule
    cap: Money
    period: Literal["once", "monthly"] = "once"
    expiresAt: str
    cosignerId: str | None = None


class ChainTx(Model):
    txHash: str
    blockNumber: int


class Mandate(MandateIn):
    id: str
    spent: Money
    status: str
    hash: str
    chainTx: ChainTx | None = None


class StudyPlan(Model):
    simulatedNow: str
    clock: Literal["SIMULATED"]
    source: str
    invoiceVersion: str
    seedRefreshRequired: bool = False
    housing: dict[str, Any]
    tuition: Money
    registrationWindow: dict[str, str] | None
    currentPaymentWindow: dict[str, str] | None
    dueAt: str
    instalmentSchedule: list[dict[str, Any]]
    paymentWindowStatus: Literal["open", "not_open", "closed", "settled", "legacy_unspecified"]
    separateObligations: list[dict[str, Any]]
    classesStart: str
    refundPromise: str
    academicTimeline: dict[str, Any]
    admissionDisposition: dict[str, Any] | None = None
    standardAdmissionCertificate: dict[str, Any]
    visaApplication: dict[str, Any]
    sequence: list[str]


class PayeeAccount(Model):
    masked: str
    hashMatch: bool


class PayeeCredential(Model):
    issuer: str
    status: Literal["valid", "revoked", "none"]
    vcId: str | None = None
    chainTx: ChainTx | None = None


class Payee(Model):
    verification: dict[str, Any] | None = None
    id: str
    name: str
    institution: str
    account: PayeeAccount
    credential: PayeeCredential
    nameCheck: Literal["match", "close_match", "no_match"]


class RentSetup(Model):
    purpose: Literal["rent"]
    payeeRule: Literal["verified_landlord_only"]
    landlord: Payee
    monthlyAmount: Money
    missing: list[dict[str, str]]
    mandates: list[Mandate]
    activeMandateId: str | None
    mandateTemplate: MandateIn
    housing: str
    verificationStatus: Literal["ready", "needs"]


class PackDocument(Model):
    kind: str
    status: Literal["ready", "missing"]


class Pack(Model):
    corridor: str
    rulesVersion: str
    documents: list[PackDocument]
    ruleChecks: list[Reason]


class FxReference(Model):
    rate: str
    midRate: str
    marginPct: str
    source: Literal["ECB", "MOCK"]
    quotedAt: str


class FxQuote(FxReference):
    send: Money
    receive: Money
    fees: Money
    referenceDate: str | None = None
    execution: Literal["MOCK"] = "MOCK"


class Disclosure(Model):
    send: Money
    fx: FxReference
    fees: Money
    receive: Money
    cancelUntil: str


class Risk(Model):
    score: int
    features: list[Reason]


class Cooling(Model):
    until: str
    cosignRequired: bool
    cosignerId: str


class InvoiceLine(Model):
    label: str
    amount: Money


class InvoiceSummary(Model):
    registrationWindow: dict[str, str] | None = None
    instalmentSchedule: list[dict[str, Any]] = Field(default_factory=list)
    separateObligations: list[dict[str, Any]] = Field(default_factory=list)
    ref: str
    issuer: str
    term: str
    dueDate: str
    lines: list[InvoiceLine]
    total: Money


class Approval(Model):
    rejectionReason: str | None = None
    refundSummary: dict[str, Any] | None = None
    correspondence: dict[str, Any] | None = None
    cosigned: bool = False
    cosignedAt: str | None = None
    invoice: InvoiceSummary | None = None
    approverId: str | None = None
    resultRef: str | None = None
    id: str
    status: Literal["pending", "approved", "rejected", "expired", "cooling_off"]
    action: Literal[
        "first_payment", "payment", "refund_claim", "escalation_letter", "mandate_change", "share_documents"
    ]
    rawAction: dict[str, Any]
    consentHash: str
    disclosure: Disclosure | None = None
    payee: Payee | None = None
    pack: Pack | None = None
    risk: Risk
    cooling: Cooling | None = None
    requestedBy: str
    createdAt: str
    expiresAt: str


class TimelineEvent(Model):
    at: str
    code: str
    actor: str
    params: dict[str, Any]
    auditSeq: int


class Payment(Model):
    createdAt: str | None = None
    purpose: str | None = None
    fees: Money | None = None
    cancelUntil: str | None = None
    id: str
    status: Literal[
        "awaiting_approval", "executing", "sent", "received_by_bursar", "matched", "cancelled", "failed"
    ]
    send: Money
    receive: Money
    payee: Payee
    mandateId: str
    approvalId: str | None = None
    invoiceRef: str
    timeline: list[TimelineEvent]
    chainTx: ChainTx | None = None


class ReconciliationLine(Model):
    code: str
    amount: Money
    clause: str | None = None


class Reconciliation(Model):
    conversion: dict[str, Any] | None = None
    sentOut: Money
    receivedBack: Money
    lines: list[ReconciliationLine]


class RefundEstimate(Reconciliation):
    kind: Literal["MOCK_ESTIMATE"] = "MOCK_ESTIMATE"
    asOf: str


class Refund(Model):
    followUp: dict[str, Any] | None = None
    estimate: RefundEstimate | None = None
    claimAmount: Money | None = None
    policy: dict[str, Any] | None = None
    paperwork: dict[str, Any] | None = None
    classesStart: str | None = None
    eligibility: str | None = None
    id: str
    paymentId: str
    status: Literal[
        "manual_review",
        "refusal_reported",
        "evidence_verified",
        "requested",
        "acknowledged",
        "approved",
        "sent",
        "received",
        "reconciled",
    ]
    deadline: str | None
    destination: Account
    timeline: list[TimelineEvent]
    reconciliation: Reconciliation | None = None


class MessageIn(Model):
    text: str = Field(default="", max_length=10000)
    documentIds: list[str] = Field(default_factory=list, max_length=10)
    locale: Literal["vi", "ko", "zh", "en"] = "en"


class CredentialIn(Model):
    credential: dict[str, Any]


class AssertionOptions(Model):
    purpose: Literal["mandate", "approval", "freeze", "cosign"]
    refId: str


class AssertionVerify(CredentialIn):
    refId: str


class SignIn(Model):
    assertion: dict[str, Any] | str


class ClockIn(Model):
    days: int = Field(default=0, ge=0, le=365)
    hours: int = Field(default=0, ge=0, le=8760)


class ScenarioIn(Model):
    ids: list[str] | None = None


class TamperIn(Model):
    seq: int = Field(ge=1)


class RejectIn(Model):
    reason: str = Field(default="", max_length=500)


class ScenarioFixtureIn(Model):
    scenario: Literal["T10", "T11", "refund_delay"]
