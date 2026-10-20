/**
 * Types for API contract v1 (docs/API.md).
 * Hand-written from the contract until the backend serves /api/openapi.json;
 * then run `pnpm gen:types` and reconcile against src/lib/api/openapi.d.ts.
 *
 * Fields marked "UI extension" are not in contract v1. They are optional, the UI
 * degrades without them, and each one is proposed in docs/status/frontend.md.
 */

export type Locale = "vi" | "ko" | "zh" | "en";
export type CurrencyCode = "VND" | "KRW" | "CNY" | "USD" | "AUD";

export interface Money {
  amount: string;
  currency: CurrencyCode | string;
}

export type PersonaId = "parent_minh" | "student_linh" | "mother_lan" | "parent_wang" | "student_hao" | "judge";
export type Role = "parent" | "student" | "cosigner" | "judge";

export interface Account {
  id: string;
  bank: string;
  currency: string;
  maskedNumber: string;
  balance: Money;
  /** v1.13: fictional bank-held SWIFT of the payer's own bank (never editable, never sent to the LLM). */
  swift?: string | null;
}

export interface AdmissionDisposition {
  status: "refused_before_payment";
  code: "VISA_REFUSED_BEFORE_PAYMENT";
  recordedAt: string;
  invoiceRef: string;
  moneyAtRisk: false;
  refundRequired: false;
  tuitionStopped: true;
  cancelledApprovalIds: string[];
  admissionAction: string;
  admissionWithdrawn: false;
  reconfirmation: string;
  parentNotice: { status: string; at: string; recipientIds: string[]; channel: string; externalMessageSent: false };
}

export interface User {
  id: string;
  name: string;
  role: Role;
  locale: Locale;
  familyId: string;
  accounts: Account[];
  /** UI extension: whether the family is frozen (kill switch). */
  frozen?: boolean;
  admissionDisposition?: AdmissionDisposition | null;
  /** v1.17: the demo's simulated today (same clock as /clock). */
  simulatedNow?: string;
}

export interface Session {
  token: string;
  user: User;
}

export interface Clock {
  now: string;
  simulated: boolean;
}

export type Severity = "info" | "warn" | "block";

export interface Reason {
  ruleId: string;
  code: string;
  severity: Severity;
  params: Record<string, unknown>;
}

export type Disposition = "DENY" | "ESCALATE" | "AUTO_EXECUTE" | "OBSERVE";

export interface ChainTx {
  txHash: string;
  blockNumber: number;
}

// ---------- Agent ----------

export type CardKind = "quote" | "payee" | "pack" | "approval_required" | "blocked" | "needs" | "refund" | "info";

export type AgentEvent =
  | { type: "token"; text: string }
  | { type: "step"; id: string; label: string; status: "running" | "done" | "failed"; tool?: string }
  | { type: "card"; kind: CardKind; data: Record<string, unknown> }
  | { type: "envelope"; envelopeId: string; action: string; requestedTier: string }
  | { type: "disposition"; envelopeId: string; result: Disposition; ruleIds: string[]; reasons: Reason[] }
  | { type: "done"; messageId: string }
  | { type: "error"; code: string; message: string };

export interface AgentMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  createdAt: string;
  /** Persisted events for assistant messages (steps, cards, dispositions). */
  events?: AgentEvent[];
  documentIds?: string[];
  author?: string;
}

export interface Thread {
  threadId: string;
  messages: AgentMessage[];
}

// ---------- Documents ----------

export type DocumentKind = "invoice" | "admission" | "refusal" | "email" | "rental_agreement";
export type Provenance = "untrusted_doc" | "verified_issuer" | "bank_record" | "user_input";

export interface Field {
  name: string;
  value: string;
  provenance: Provenance;
  confidence: number;
}

export interface DocumentRecord {
  id: string;
  kind: DocumentKind;
  filename: string;
  sha256: string;
  uploadedBy: string;
  fields: Field[];
  warnings: Reason[];
  /** UI extension */
  uploadedAt?: string;
}

// ---------- Mandates ----------

export type PayeeRule = { type: "credentialed"; issuer: string } | { type: "name_checked"; payeeId: string };

export interface Mandate {
  id: string;
  purpose: "tuition" | "rent" | "living";
  payeeRule: PayeeRule;
  cap: Money;
  spent: Money;
  period: "once" | "monthly";
  expiresAt: string;
  cosignerId?: string | null;
  status: "pending_signature" | "active" | "revoked" | "expired" | "suspended";
  hash: string;
  chainTx?: ChainTx | null;
  /** UI extension: display names */
  payeeLabel?: string;
  createdAt?: string;
}

export interface MandateCreate {
  purpose: Mandate["purpose"];
  payeeRule: PayeeRule;
  cap: Money;
  period?: "once" | "monthly";
  expiresAt: string;
  cosignerId?: string;
}

// ---------- Payees, packs, approvals ----------

export interface Payee {
  id: string;
  name: string;
  institution: string;
  account: { masked: string; hashMatch: boolean; bank?: string };
  credential: { issuer: string; status: "valid" | "revoked" | "none"; vcId?: string; chainTx?: ChainTx | null };
  nameCheck: "match" | "close_match" | "no_match";
}

export interface OutboundPack {
  corridor: "VN→KR" | "CN→KR" | "VN→AU";
  rulesVersion: string;
  documents: { kind: string; status: "ready" | "missing" }[];
  ruleChecks: Reason[];
}

export interface FxQuote {
  rate: string;
  midRate: string;
  marginPct: string;
  source: "ECB" | "MOCK";
  quotedAt: string;
}

export interface Disclosure {
  send: Money;
  fx: FxQuote;
  fees: Money;
  receive: Money;
  cancelUntil: string;
}

export type ApprovalAction =
  | "first_payment"
  | "payment"
  | "refund_claim"
  | "escalation_letter"
  | "mandate_change"
  | "share_documents";

export interface InvoiceSummary {
  ref: string;
  issuer: string;
  term: string;
  dueDate: string;
  lines: { label: string; amount: Money }[];
  total: Money;
}

export interface Approval {
  rejectionReason?: string | null;
  id: string;
  status: "pending" | "approved" | "rejected" | "expired" | "cooling_off";
  action: ApprovalAction;
  rawAction: Record<string, unknown>;
  consentHash: string;
  disclosure?: Disclosure;
  payee?: Payee;
  pack?: OutboundPack;
  risk: { score: number; features: Reason[] };
  cooling?: { until: string; cosignRequired: boolean; cosignerId: string };
  requestedBy: "agent";
  createdAt: string;
  expiresAt: string;
  /** UI extension: which invoice this pays (from the university's invoice credential). */
  invoice?: InvoiceSummary;
  /** UI extension: who in the family must approve. */
  approverId?: string;
  /** UI extension: resulting payment / refund id after approval. */
  resultRef?: string;
  decidedAt?: string;
  /** UI extension (mock): the home co-signer signed the review. */
  cosigned?: boolean;
  /** API r5 (simulated UTC). */
  cosignedAt?: string | null;
  /** UI extension: how the approval was signed. */  authenticator?: "platform" | "demo";
  /** v1.17: compact refund claim display (read this, never rawAction). */
  refundSummary?: RefundSummaryView | null;
  /** v1.17: readable fields of a dated MOCK chaser letter (action escalation_letter). */
  correspondence?: Correspondence | null;
}

export interface RefundSummaryView {
  action?: string;
  claimAmount?: Money;
  deadline?: string | null;
  classesStart?: string | null;
  signBefore?: string | null;
  signerId?: string;
  destination?: { bank: string; maskedNumber: string; originalPayerOnly?: boolean };
  estimate?: Reconciliation | null;
  separateObligationsExcluded?: unknown;
  details?: unknown;
}

export interface Correspondence {
  recipient: string;
  preparedAt: string;
  claimReference: string;
  promiseAt: string;
  summary: string;
  formEvidence?: { kind: string; status?: string; consentHash?: string; signedAt?: string }[];
  downloadUrl?: string;
  mock?: boolean;
}

export interface PaymentWindow {
  opensAt: string;
  closesAt: string;
  timeZone?: string;
}

export interface Obligation {
  id: string;
  label: string;
  amount: Money;
  period: "semester" | "monthly" | string;
  collector: string;
  when: string;
  paidThroughBridge: boolean;
  refundPolicy?: string;
  alternativeTo?: string;
  source?: string;
  sourceUrl?: string;
  applicable: boolean;
}

/** v1.17 GET /study-plan: the family's calendar in simulated time. */
export interface StudyPlan {
  admissionDisposition?: AdmissionDisposition | null;
  academicTimeline?: { acceptedAt?: string; certificateIssuedAt?: string; visaAppliedAt?: string; source?: string };
  sequence?: string[];
  simulatedNow: string;
  clock: "SIMULATED" | string;
  invoiceVersion?: string;
  seedRefreshRequired?: boolean;
  tuition: Money;
  registrationWindow?: PaymentWindow | null;
  currentPaymentWindow?: PaymentWindow | null;
  paymentWindowStatus?: "not_open" | "open" | "closed" | "settled" | "legacy_unspecified" | string;
  dueAt?: string | null;
  instalmentSchedule?: { number: number; amount: string; dueAt: string; paymentWindow?: PaymentWindow }[];
  separateObligations?: Obligation[];
  classesStart?: string | null;
  refundPromise?: string | null;
  standardAdmissionCertificate?: { status: string; issuedAt?: string; downloadUrl?: string };
  visaApplication?: { status: string; appliedAt?: string };
  housing?: { mode: string } | string;
}

/** v1.17 GET /rent: everything the parent needs to set a rent limit to a verified landlord. */
export interface RentSetup {
  purpose: "rent";
  payeeRule: string;
  landlord: Payee & { verification?: { method: string; agreementStatus: string; validFrom?: string; validUntil?: string; agreementId?: string | null; source?: string } };
  monthlyAmount: Money;
  missing: { kind: string; actorId: string; action: string }[];
  mandates: Mandate[];
  activeMandateId: string | null;
  mandateTemplate: MandateCreate;
  housing?: string;
  verificationStatus: string;
}

// ---------- Payments, refunds ----------

export type Actor = "agent" | "parent" | "student" | "bank" | "bursar" | "system";

export interface TimelineEvent {
  at: string;
  code: string;
  actor: Actor;
  params: Record<string, unknown>;
  auditSeq: number;
}

export type PaymentStatus =
  | "awaiting_approval"
  | "executing"
  | "sent"
  | "received_by_bursar"
  | "matched"
  | "cancelled"
  | "failed";

export interface Payment {
  id: string;
  status: PaymentStatus;
  send: Money;
  receive: Money;
  payee: Payee;
  mandateId: string;
  approvalId?: string | null;
  invoiceRef: string;
  timeline: TimelineEvent[];
  chainTx?: ChainTx | null;
  /** UI extension */
  fees?: Money;
  cancelUntil?: string;
  purpose?: "tuition" | "rent" | "living";
  createdAt?: string;
  autoExecuted?: boolean;
}

export type RefundStatus =
  | "manual_review"
  | "refusal_reported"
  | "evidence_verified"
  | "requested"
  | "acknowledged"
  | "approved"
  | "sent"
  | "received"
  | "reconciled";

/** v1.13: the issuer-signed refund contract (fictional HBU-REF-01-v2). */
export interface RefundPolicy {
  id: string;
  source?: string;
  classesStart: string;
  paymentWithinDaysAfterClassesStart: number;
  beforeStart?: string;
  admissionFee?: string;
  afterStart?: string;
  freshman?: string;
  destination?: string;
  settlement?: string;
}

export type RefundEligibility = "before_start_full_unused" | "manual_degree_assessment";

export interface RefundForm {
  kind: "admission_withdrawal" | "tuition_refund_application" | "visa_denial_letter" | string;
  signerId?: string;
  documentId?: string | null;
  status: "prepared" | "signed" | "attached_MOCK" | string;
  signedAt?: string;
  consentHash?: string;
}

/** v1.13: what one student consent binds (Approval.rawAction.paperwork; the signed copy is Refund.paperwork). */
export interface RefundPaperwork {
  policy: RefundPolicy;
  requestedAt: string;
  deadline: string | null;
  eligibility: RefundEligibility | string;
  claimAmount: Money;
  admissionFeeCharged?: Money;
  destination: { accountId: string; bank: string; maskedNumber: string; swift?: string | null; source: string };
  documents: RefundForm[];
}

export interface Reconciliation {
  sentOut: Money;
  receivedBack: Money;
  lines: { code: string; amount: Money; clause?: string | null }[];
  /** v1.13: MOCK return route, e.g. KRW→USD→VND at lossPct. */
  conversion?: { route?: string[]; source?: string; lossPct?: string } | null;
}

export interface RefundFollowUp {
  overdue: boolean;
  promiseAt?: string | null;
  daysOverdue?: number;
  requiresStudentApproval?: boolean;
  mock?: boolean;
  escalation?: (Correspondence & { approvalId: string; status: "pending_approval" | "submitted_MOCK" | "rejected" | "expired" | string; submittedAt?: string }) | null;
  complaintPack?: {
    status: string;
    preparedAt: string;
    downloadUrl?: string;
    route?: { name?: string; url?: string; ministryUrl?: string; submission?: string; guaranteesRecovery?: boolean; eligibility?: string };
    contains?: string[];
  } | null;
}

/** v1.16: the server's MOCK return-wire projection before receipt (null after receipt and for manual review). */
export interface RefundEstimate extends Reconciliation {
  kind?: "MOCK_ESTIMATE";
  asOf: string;
}

export interface Refund {
  id: string;
  paymentId: string;
  status: RefundStatus;
  /** The school's promise date; null while the degree office assesses by hand (manual_review). */
  deadline: string | null;
  destination: Account;
  timeline: TimelineEvent[];
  reconciliation?: Reconciliation | null;
  /** v1.16 */
  estimate?: RefundEstimate | null;
  /** v1.17: a missed promise and the student-approved MOCK chaser / complaint pack. */
  followUp?: RefundFollowUp | null;
  /** v1.13 */
  claimAmount?: Money | null;
  policy?: RefundPolicy | null;
  paperwork?: RefundPaperwork | null;
  classesStart?: string | null;
  eligibility?: RefundEligibility | string | null;
  /** UI extension */
  createdAt?: string;
  expected?: Money;
}

export interface FxQuoteResponse extends FxQuote {
  send: Money;
  receive: Money;
  fees: Money;
}

// ---------- Notifications ----------

export type AppEventType = "approval_created" | "approval_updated" | "thread_updated" | "payment_updated" | "refund_updated" | "blocked" | "freeze" | "anchor" | "anchor_updated" | "admission_updated" | "mandate_updated";
export interface AppEvent {
  type: AppEventType;
  data: Record<string, unknown>;
}

// ---------- Freeze ----------

export interface FreezeResult {
  frozen: boolean;
  revokedTokens?: number;
  cancelledPayments?: number;
  pausedApprovals?: number;
  incomingRefundsPaused?: false;
  suspendedMandates?: number;
  restoredMandates?: number;
  tookMs?: number;
}

// ---------- Trust center ----------

export interface AuditEntry {
  seq: number;
  at: string;
  actor: string;
  kind: string;
  summary: string;
  ruleIds: string[];
  envelopeId?: string | null;
  prevHash: string;
  hash: string;
  anchoredIn?: number | null;
}

export interface VerifyResult {
  ok: boolean;
  mode?: string;
  onChain?: boolean;
  entries: number;
  anchors: number;
  firstBadSeq?: number | null;
  detail?: string | null;
}

export interface ChainStatus {
  registrationStatus?: "pending" | "ready";
  anchorStatus?: "pending" | "retrying" | "ready";
  network: string;
  connected: boolean;
  blockNumber: number;
  contracts: { name: string; address: string }[];
  /** UI extension */
  mock?: boolean;
  /** v1.1: "fisco" | "local" */
  mode?: string;
}

export interface Anchor {
  root: string;
  firstSeq: number;
  lastSeq: number;
  blockNumber: number;
  txHash: string;
  at: string;
}

// ---------- Scenarios ----------

export interface Scenario {
  id: string;
  title: string;
  priority: "P0" | "P1";
  tags: string[];
}

export type ScenarioEvent =
  | { id: string; status: "running" | "pass" | "fail"; expected: string; actual: string; ms: number; auditSeqs: number[] }
  | { summary: { passed: number; failed: number; total: number } };

export interface ApiErrorBody {
  error: { code: string; message: string; ruleId?: string; details?: Record<string, unknown> };
}
