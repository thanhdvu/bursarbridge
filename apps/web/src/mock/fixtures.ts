/**
 * Demo fixtures for mock mode. They mirror the live API's fixed seed exactly
 * (services/api invoice "tuition-2027-v8", API v1.17), so the demo shows one world
 * whichever mode it runs in. Every organisation here is fictional (PRD §7).
 */
import type { InvoiceSummary, Money, Payee, PersonaId, User } from "@/lib/api/types";
import { estimateReturn } from "./refund-math";

export const m = (amount: number, currency: string): Money => ({ amount: amount.toFixed(2), currency });

/** The API's simulated clock starts here on every reset and only moves when a judge advances it. */
/** v1.17: the demo starts inside Hanbit's registration window (12 Jan 2027, 12:00 in Seoul). */
export const SIM_START = "2027-01-12T03:00:00.000Z";

export const BANK = "Lotus Home Bank (MOCK)";
export const UNIVERSITY = "Hanbit University";
export const ISSUER_DID = "did:key:z6MkmqmNUcR8PbGqDHGnQvyDp8aYLwmHeut4wJPMcG1DCoJ4";
export const RULES_VERSION = "2026-10-18.1";
export const INVOICE_VERSION = "tuition-2027-v8";

/** MOCK board: VND→KRW. Rates are "receive per send", exactly as the API returns them. */
export const FX = {
  rate: "0.05289041",
  midRate: "0.05342465753424657534246575342",
  marginPct: "1.00",
  feeVnd: 25_000,
};

/** VND debited (fees included) for a KRW amount, rounded to cents like the API. */
export function vndFor(krw: number) {
  return Math.round((krw / Number(FX.rate) + FX.feeVnd) * 100) / 100;
}

/** v1.17: BursarBridge pays the tuition only; dorm and health insurance are separate obligations. */
export const TUITION_KRW = 7_174_000;
export const INSTALMENT_KRW = 3_587_000;
const SEOUL = "Asia/Seoul";
/** Registration windows open 09:00 and close 17:00 Korea time; dueAt is that 17:00 close. */
export const REGISTRATION_WINDOW = { opensAt: "2027-01-11T00:00:00Z", closesAt: "2027-01-15T08:00:00Z", timeZone: SEOUL };
export const INSTALMENT_SCHEDULE = [
  { number: 1, amount: INSTALMENT_KRW, dueAt: "2027-01-15T08:00:00Z", paymentWindow: REGISTRATION_WINDOW },
  { number: 2, amount: INSTALMENT_KRW, dueAt: "2027-02-15T08:00:00Z", paymentWindow: { opensAt: "2027-02-11T00:00:00Z", closesAt: "2027-02-15T08:00:00Z", timeZone: SEOUL } },
];
export const DORM_KRW = 1_500_000;
export const NHIS_MONTHLY_KRW = 70_000;
export const RENT_KRW = 900_000;

export const users: Record<PersonaId, User> = {
  parent_minh: {
    id: "usr_parent_minh",
    name: "Minh",
    role: "parent",
    locale: "vi",
    familyId: "fam_minh",
    accounts: [{ id: "acct_parent_minh", bank: BANK, currency: "VND", maskedNumber: "•••• 4821", balance: m(1_000_000_000, "VND"), swift: "LOTUVNVX" }],
  },
  student_linh: { id: "usr_student_linh", name: "Linh", role: "student", locale: "vi", familyId: "fam_minh", accounts: [] },
  mother_lan: { id: "usr_mother_lan", name: "Lan", role: "cosigner", locale: "vi", familyId: "fam_minh", accounts: [] },
  parent_wang: {
    id: "usr_parent_wang",
    name: "Wang",
    role: "parent",
    locale: "zh",
    familyId: "fam_wang",
    accounts: [{ id: "acct_parent_wang", bank: BANK, currency: "CNY", maskedNumber: "•••• 4821", balance: m(1_000_000, "CNY"), swift: "LOTUCNBX" }],
  },
  student_hao: { id: "usr_student_hao", name: "Hao", role: "student", locale: "zh", familyId: "fam_wang", accounts: [] },
  judge: { id: "usr_judge", name: "Judge", role: "judge", locale: "en", familyId: "fam_none", accounts: [] },
};

export const hanbitPayee: Payee = {
  id: "payee_hanbit",
  name: "Hanbit University",
  institution: "Hanbit University (MOCK)",
  account: { masked: "•••• 3104", hashMatch: true },
  credential: {
    issuer: ISSUER_DID,
    status: "valid",
    vcId: "969e86fc0547b7a8f005d1b76fb3bc7014e5fbe3a9b52a0a2c2de848223bb7df",
    chainTx: { txHash: "0x703362726eb058463a393d76007dc452697ad7f8932d1187b7c544c33ecd48f1", blockNumber: 329 },
  },
  nameCheck: "match",
};

/** Bank-held, name-checked rent payee (catalog `bankPayees`). */
export const landlordPayee: Payee = {
  id: "payee_landlord",
  name: "Seoul Garden Residence (MOCK)",
  institution: "Seoul Garden Residence (MOCK)",
  account: { masked: "•••• 1193", hashMatch: true },
  credential: { issuer: "bank_record", status: "none" },
  nameCheck: "match",
};

export const invoice: InvoiceSummary = {
  ref: "HBU-2027-0042-fam_minh",
  issuer: UNIVERSITY,
  term: "Spring 2027 - semester 1",
  dueDate: "2027-01-15T08:00:00Z",
  // Tuition only. The dorm (dormitory office) and NHIS (after arrival) are the family's separate obligations.
  lines: [{ label: "Semester tuition", amount: m(7_174_000, "KRW") }],
  total: m(TUITION_KRW, "KRW"),
};

export type SampleId = "invoice" | "admission" | "discount_email" | "refusal" | "refund_agent_email" | "police" | "rental_agreement";

export interface SampleDoc {
  id: SampleId;
  kind: "invoice" | "admission" | "refusal" | "email" | "rental_agreement";
  /** The API's own synthetic fixture (public/samples/live), uploaded in both modes. */
  filename: string;
  live: string;
  /** What kind of thing it is, for the doc tray. */
  tone: "safe" | "attack" | "neutral";
  uploadKind: "invoice" | "admission" | "refusal" | "email" | "rental_agreement";
}

export const samples: SampleDoc[] = [
  { id: "invoice", kind: "invoice", filename: "invoice.pdf", live: "invoice.pdf", tone: "safe", uploadKind: "invoice" },
  { id: "admission", kind: "admission", filename: "admission.pdf", live: "admission.pdf", tone: "neutral", uploadKind: "admission" },
  { id: "refusal", kind: "refusal", filename: "refusal.pdf", live: "refusal.pdf", tone: "neutral", uploadKind: "refusal" },
  { id: "discount_email", kind: "email", filename: "fake_invoice.pdf", live: "fake_invoice.pdf", tone: "attack", uploadKind: "email" },
  { id: "refund_agent_email", kind: "email", filename: "refund_agent.pdf", live: "refund_agent.pdf", tone: "attack", uploadKind: "email" },
  { id: "police", kind: "email", filename: "police.pdf", live: "police.pdf", tone: "attack", uploadKind: "email" },
  { id: "rental_agreement", kind: "rental_agreement", filename: "rental_agreement.pdf", live: "rental_agreement.pdf", tone: "safe", uploadKind: "rental_agreement" },
];

/** Fictional HBU-REF-01-v2 degree refund contract, as signed into the API's v4 invoice credential. */
export const REFUND_POLICY = {
  id: "HBU-REF-01-v3",
  source: "Hanbit University fictional contractual policy (MOCK), not Korean law",
  classesStart: "2027-03-02T00:00:00Z",
  paymentWithinDaysAfterClassesStart: 14,
  beforeStart: "Full paid tuition only; dormitory and NHIS payments are separate and excluded",
  admissionFee: "Nonrefundable if separately charged; none charged on this invoice",
  afterStart: "Manual degree-office assessment; no language-course day table applies",
  freshman: "Withdraw admission and reapply; leave of absence is not a substitute",
  destination: "Original payer bank record only, including bank-held SWIFT",
  settlement: "International office manual international wire (MOCK)",
};
/** Before classes start the school promises payment two weeks after the first day of classes. */
export const REFUND_PROMISE = new Date(Date.parse(REFUND_POLICY.classesStart) + REFUND_POLICY.paymentWithinDaysAfterClassesStart * 86_400_000).toISOString().replace(".000Z", "Z");

/**
 * Refund reconciliation exactly as the API computes it (refund_policy.reconciliation): four additive
 * family costs, no percentage charge by the university. Shared with the UI's labelled estimate.
 */
export function refundLines(send: Money, fees: Money) {
  return estimateReturn(send, fees);
}
