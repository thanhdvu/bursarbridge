/**
 * Scripted agent for mock mode. Deterministic, keyword-driven, multilingual, and shaped like the
 * live API's scripted provider (same cards, codes and rule IDs). It never takes payee, amount or
 * destination from text: those come from fixtures that stand in for credentials, mandates and bank records.
 */
import type { AgentEvent, Locale, PersonaId, Reason, AdmissionDisposition } from "@/lib/api/types";
import { appendAudit, commit, emit, nextId, refresh, simIso } from "./db";
import { copy, detectLocale, normalize, type CopyKey } from "./agent-copy";
import {
  createRefundClaimApproval,
  createScamReview,
  createTuitionApproval,
  familyOf,
  packFor,
  payRent,
  quoteCard,
  r,
  rentMissing,
  studentOf,
  tuitionNeeds,
} from "./domain";
import { INSTALMENT_KRW, INSTALMENT_SCHEDULE, REFUND_POLICY, REFUND_PROMISE, RENT_KRW, TUITION_KRW, invoice, landlordPayee } from "./fixtures";

const sleep = (ms: number) => new Promise((res) => setTimeout(res, ms));

function fmtMoney(amount: number, currency: string, locale: Locale) {
  const tag = { vi: "vi-VN", ko: "ko-KR", zh: "zh-CN", en: "en-US" }[locale];
  return new Intl.NumberFormat(tag, { style: "currency", currency, maximumFractionDigits: 0 }).format(amount);
}
function fmtDate(iso: string, locale: Locale) {
  const tag = { vi: "vi-VN", ko: "ko-KR", zh: "zh-CN", en: "en-GB" }[locale];
  return new Intl.DateTimeFormat(tag, { day: "numeric", month: "short", year: "numeric", timeZone: "Asia/Ho_Chi_Minh" }).format(new Date(iso));
}

type Intent =
  | "invoice"
  | "pay_tuition"
  | "discount"
  | "refusal"
  | "refund_redirect"
  | "how_much"
  | "status"
  | "crypto"
  | "passport"
  | "remember_account"
  | "raise_limit"
  | "freeze"
  | "structuring"
  | "police"
  | "rent"
  | "greeting"
  | "unknown";

export function classify(text: string, docSamples: (string | undefined)[]): Intent {
  if (docSamples.includes("discount_email")) return "discount";
  if (docSamples.includes("police")) return "police";
  if (docSamples.includes("refund_agent_email")) return "refund_redirect";
  if (docSamples.includes("refusal")) return "refusal";
  if (docSamples.includes("invoice") || docSamples.includes("admission")) return "invoice";
  if (docSamples.includes("rental_agreement")) return "rent";
  const t = normalize(text);
  if (/(police|cong an|경찰|警察).*(deposit|ky quy|tien|보증금|保证金|押金)|safe account|tai khoan an toan|안전계좌|安全账户/.test(t)) return "police";
  if (/(crypto|bitcoin|btc|usdt|stablecoin|coin|tien ao|tien so|yield|sinh loi|dau tu|invest|코인|투자|加密|比特币|理财|投资|稳定币)/.test(t)) return "crypto";
  if (/(passport|ho chieu|cccd|can cuoc|여권|护照|身份证)/.test(t)) return "passport";
  if (/(remember|save this account|nho tai khoan|luu tai khoan|ghi nho|기억|저장|记住|保存.*账户)/.test(t)) return "remember_account";
  if (/(raise|increase|tang|nang).*(limit|han muc|gioi han)|limit.*(raise|up)|한도.*(올려|늘려)|提高.*额度|额度.*提高/.test(t)) return "raise_limit";
  if (/(split|chia nho|叔叔|舅舅|分开|拆分|分几次|uncle)/.test(t)) return "structuring";
  if (/(rent|tien nha|thue nha|월세|房租)/.test(t)) return "rent";
  if (/(refund|hoan tien|환불|退款).*(account|tai khoan|계좌|账户|faster|nhanh|speed|빨리|加急)|(doi|change|new).*(tai khoan|account).*(hoan|refund)/.test(t)) return "refund_redirect";
  if (/(truot visa|rot visa|tu choi visa|visa.*(tu choi|bi tu choi|refus|denied|rejected)|refused|거절|拒签|签证.*拒)/.test(t)) return "refusal";
  if (/(hoan tien|hoan lai|lay lai|refund|환불|退款|退回|tien ve|bi tru|tru bao nhieu|deduct)/.test(t)) return "refusal";
  if (/(discount|giam gia|giam 15|할인|折扣|优惠)/.test(t)) return "discount";
  if (/(freeze|stop everything|stop all|dong bang|khoa lai|dung het|dung moi|동결|정지|멈춰|멈추|冻结|停止|暂停)/.test(t)) return "freeze";
  if (/(bao nhieu|how much|얼마|多少|due|han chot|het han|when.*pay)/.test(t)) return "how_much";
  if (/(den chua|toi chua|nhan chua|where.*(money|tien)|status|arrived|tien dau|도착|어디|到了|到账|进度|tinh hinh)/.test(t)) return "status";
  if (/(hoc phi|hoc ky|tuition|semester|등록금|학비|学费|chuyen tien|transfer|pay|thanh toan|dong tien|nop tien|송금|납부|付款|汇款|缴)/.test(t)) return "pay_tuition";
  if (/^(hi|hello|hey|chao|xin chao|안녕|你好|嗨)/.test(t)) return "greeting";
  return "unknown";
}

async function* say(text: string): AsyncGenerator<AgentEvent> {
  // Stream like a model: a few characters at a time (word-ish chunks; CJK by characters).
  const chunks = text.match(/[　-鿿가-힯]{1,2}|\S+\s*|\s+/g) ?? [text];
  for (const c of chunks) {
    yield { type: "token", text: c };
    await sleep(c.length > 6 ? 24 : 16);
  }
}

async function* step(id: string, label: string, tool: string, ms = 520): AsyncGenerator<AgentEvent> {
  yield { type: "step", id, label, status: "running", tool };
  await sleep(ms);
  yield { type: "step", id, label, status: "done", tool };
}

export interface AgentInput {
  persona: PersonaId;
  text: string;
  documentIds: string[];
  locale: Locale;
}

export async function* runAgent(input: AgentInput): AsyncGenerator<AgentEvent> {
  let d = refresh();
  const { persona } = input;
  const familyId = familyOf(d, persona);
  const docs = d.documents.filter((x) => input.documentIds.includes(x.id));
  let intent = classify(input.text, docs.map((x) => x.sampleId));
  // A pending tuition request resumes when the missing documents arrive, whatever the message says.
  if (d.story.pendingTuition?.[familyId] && docs.some((x) => x.sampleId === "invoice" || x.sampleId === "admission") && !docs.some((x) => x.warnings.length)) intent = "invoice";
  const existingRefund = () => refresh().refunds.find((x) => x.familyId === familyId);
  const pendingClaim = () => refresh().approvals.find((a) => a.familyId === familyId && a.action === "refund_claim" && a.status === "pending");
  if ((intent === "how_much" || intent === "status" || intent === "refusal" || intent === "unknown") && !docs.length && (existingRefund() || pendingClaim())) intent = "status";
  const askedRefund = intent === "refusal";
  if (intent === "refusal" && persona.startsWith("parent")) intent = "status";
  const loc = detectLocale(input.text, input.locale);
  const L = (k: CopyKey, p?: Record<string, string | number>) => copy(loc, k, p);
  const isParent = persona.startsWith("parent");
  const user = d.users[persona];
  const frozen = !!d.frozen[familyId];
  const tuitionTotal = fmtMoney(TUITION_KRW, "KRW", loc);

  const tuitionPayment = () => refresh().payments.find((p) => p.familyId === familyId && p.purpose === "tuition" && p.status !== "cancelled");
  const pendingTuitionApproval = () => refresh().approvals.find((a) => a.familyId === familyId && a.action === "first_payment" && a.status === "pending");

  const denyTaint = (docId: string, kind: "execute_payment" | "change_refund_destination", account: string, extra: Reason) => {
    const doc = d.documents.find((x) => x.id === docId);
    return {
      attempted: {
        account,
        action: kind,
        payee: { account: { bank: "Unverified document text", hashMatch: false, masked: account }, name: "Unverified document payee" },
        provenance: "untrusted_doc",
        source: { filename: doc?.filename, kind: doc?.kind ?? "email" },
      },
      outOfBandVerificationRequired: kind === "execute_payment",
      reasons: [r("LX-03", "NEVER_ALLOWED", "block"), r("T-01", "UNTRUSTED_INSTRUCTIONS", "block"), r("P-01", "PAYEE_UNVERIFIED", "block"), r("T-01", "TAINTED_PARAMETERS", "block"), extra],
      result: "DENY",
      ruleIds: ["LX-03"],
    };
  };

  switch (intent) {
    case "greeting":
    case "unknown": {
      if (isParent) {
        const pending = pendingTuitionApproval();
        const pay = tuitionPayment();
        const state = pending ? L("reply.status_waiting") : pay ? L("reply.status_moving", { status: pay.status.replaceAll("_", " ") }) : L("reply.status_none");
        yield* say(L("reply.parent_intro", { name: user.name, state: state.replace(/\.$/, "").toLowerCase() }));
      } else if (intent === "greeting") {
        yield* say(L("reply.intro", { name: user.name, uni: loc === "ko" ? "한빛대학교" : loc === "zh" ? "韩光大学" : "Hanbit University" }));
      } else {
        yield* say(L("reply.fallback"));
      }
      return;
    }

    case "pay_tuition":
    case "invoice": {
      if (frozen) {
        yield* say(L("reply.frozen"));
        return;
      }
      const pay = tuitionPayment();
      if (pay) {
        yield* say(pay.status === "matched" ? L("reply.already_paid", { receive: tuitionTotal }) : L("reply.status_moving"));
        return;
      }
      if (pendingTuitionApproval()) {
        yield* say(L("reply.already_pending"));
        return;
      }
      yield* tuitionFlow();
      return;
    }

    case "discount": {
      const doc = docs[0];
      yield* step("s1", L("step.read_doc", { file: doc?.filename ?? "email" }), "documents.parse", 500);
      d = refresh();
      const envelopeId = nextId("env", d);
      appendAudit(d, { actor: "agent", kind: "disposition", summary: "NEVER_ALLOWED", ruleIds: ["LX-03"], envelopeId });
      commit(d);
      emit({ type: "blocked", data: { scenario: "discount_email", envelopeId }, familyId });
      yield { type: "envelope", envelopeId, action: "document_instruction", requestedTier: "L2" };
      yield { type: "disposition", envelopeId, result: "DENY", ruleIds: ["LX-03"], reasons: [r("LX-03", "NEVER_ALLOWED", "block")] };
      yield { type: "card", kind: "blocked", data: denyTaint(doc?.id ?? "", "execute_payment", "MOCK-ATTACKER-9912", r("LX-03", "DOCUMENT_INSTRUCTION", "block")) };
      yield* say(L("reply.blocked_discount"));
      return;
    }

    case "police": {
      const doc = docs[0];
      if (doc) yield* step("s1", L("step.read_doc", { file: doc.filename }), "documents.parse", 500);
      d = refresh();
      const envelopeId = nextId("env", d);
      // Same features and weights as the API's scam score.
      const features: Reason[] = [
        r("S-02", "NEW_PAYEE", "warn", { weight: 2 }),
        r("S-02", "UNVERIFIED_PAYEE", "warn", { weight: 3 }),
        r("S-02", "AUTHORITY", "warn", { weight: 3 }),
        r("S-02", "URGENCY_SECRECY", "warn", { weight: 2 }),
        r("S-02", "SAFE_ACCOUNT", "warn", { weight: 3 }),
      ];
      const score = features.reduce((a, f) => a + Number(f.params.weight), 0);
      const review = createScamReview(d, familyId, score, features);
      commit(d);
      emit({ type: "approval_created", data: { approvalId: review.id, action: review.action, status: review.status }, familyId });
      yield { type: "card", kind: "approval_required", data: { ...review, approvalId: review.id } };
      yield { type: "disposition", envelopeId, result: "ESCALATE", ruleIds: ["S-02"], reasons: [r("S-02", "COOLING_AND_COSIGN_REQUIRED", "warn")] };
      yield {
        type: "card",
        kind: "blocked",
        data: {
          attempted: { action: "scam", provenance: doc ? "untrusted_doc" : "user_input", ...(doc ? { source: { filename: doc.filename, kind: doc.kind } } : {}) },
          cooling: review.cooling,
          executable: false,
          outOfBandVerificationRequired: true,
          reasons: [r("S-02", "COOLING_AND_COSIGN_REQUIRED", "warn"), ...features, r("LX-03", "SCAM", "block")],
          result: "ESCALATE",
          risk: { score, features },
          ruleIds: ["S-02"],
          verificationChecklist: ["Contact the student independently", "Call the university's published number"],
        },
      };
      yield* say(L("reply.police"));
      return;
    }

    case "refusal": {
      const pay = tuitionPayment();
      const doc = docs[0];
      if (doc) yield* step("s1", L("step.read_doc", { file: doc.filename }), "documents.parse", 500);
      yield* step("s2", L("step.find_payment"), "bank.payments", 400);
      if (!pay && (doc?.sampleId === "refusal" || refresh().documents.some(x => x.familyId === familyId && x.sampleId === "refusal" && !x.warnings.length))) {
        d = refresh();
        const stopped = d.approvals.filter(a => a.familyId === familyId && ["first_payment", "payment"].includes(a.action) && a.rawAction?.purpose !== "rent" && ["pending", "cooling_off"].includes(a.status));
        for (const a of stopped) {
          a.status = "rejected";
          a.rejectionReason = "VISA_REFUSED_BEFORE_PAYMENT";
          emit({ type: "approval_updated", data: { approvalId: a.id, status: a.status }, familyId });
        }
        if (d.story.pendingTuition) delete d.story.pendingTuition[familyId];
        const disposition: AdmissionDisposition = {
          status: "refused_before_payment", code: "VISA_REFUSED_BEFORE_PAYMENT", recordedAt: simIso(d), invoiceRef: invoice.ref,
          moneyAtRisk: false, refundRequired: false, tuitionStopped: true, cancelledApprovalIds: stopped.map(a => a.id),
          admissionAction: "ask_university_to_withdraw_or_reapply_next_intake", admissionWithdrawn: false,
          reconfirmation: "new_university_signed_admission_and_invoice_required",
          parentNotice: { status: "available_in_family_app_MOCK", at: simIso(d), recipientIds: Object.values(d.users).filter(u => u.familyId === familyId && u.role === "parent").map(u => u.id), channel: "family_app_only", externalMessageSent: false },
        };
        for (const u of Object.values(d.users).filter(u => u.familyId === familyId)) u.admissionDisposition = disposition;
        appendAudit(d, { actor: user.id, kind: "admission_updated", summary: "Refusal before payment: tuition stopped; family app notice available" });
        commit(d);
        emit({ type: "admission_updated", data: disposition as unknown as Record<string, unknown>, familyId });
        yield { type: "card", kind: "needs", data: { code: disposition.code, admissionDisposition: disposition, missing: [{ kind: "admission_withdrawal", actorId: user.id, action: "contact_university" }] } };
        return;
      }
      if (!pay || pay.status !== "matched") {
        yield { type: "card", kind: "needs", data: { code: pay ? "PAYMENT_SETTLEMENT_REQUIRED" : "REFUSAL_DOCUMENT_REQUIRED", missing: [{ kind: pay ? "payment_settlement" : "refusal", actorId: user.id, action: pay ? "wait" : "upload" }] } };
        return;
      }
      if (!doc && !refresh().documents.some((x) => x.familyId === familyId && x.sampleId === "refusal" && !x.warnings.length)) {
        yield { type: "card", kind: "needs", data: { code: "REFUSAL_DOCUMENT_REQUIRED", missing: [{ kind: "refusal", actorId: user.id, action: "upload" }] } };
        return;
      }
      yield* step("s3", L("step.refund_policy"), "issuer.refundPolicy", 450);
      yield* step("s4", L("step.draft_claim"), "refund.prepare", 450);
      d = refresh();
      const approval = pendingClaim() ?? createRefundClaimApproval(d, familyId, pay);
      commit(d);
      emit({ type: "approval_created", data: { approvalId: approval.id, action: approval.action, status: approval.status }, familyId });
      yield { type: "card", kind: "approval_required", data: { ...approval, approvalId: approval.id } };
      const before = (approval.rawAction as { paperwork?: { deadline?: string | null } }).paperwork?.deadline;
      yield* say(before ? L("reply.refusal", { promise: fmtDate(REFUND_PROMISE, loc), start: fmtDate(REFUND_POLICY.classesStart, loc) }) : L("reply.refusal_after_start"));
      return;
    }

    case "refund_redirect": {
      const doc = docs[0];
      if (doc) yield* step("s1", L("step.read_doc", { file: doc.filename }), "documents.parse", 500);
      d = refresh();
      const envelopeId = nextId("env", d);
      appendAudit(d, { actor: "agent", kind: "disposition", summary: "NEVER_ALLOWED", ruleIds: ["LX-03"], envelopeId });
      commit(d);
      emit({ type: "blocked", data: { scenario: "refund_redirect", envelopeId }, familyId });
      yield { type: "envelope", envelopeId, action: "refund_redirect", requestedTier: "L2" };
      yield { type: "disposition", envelopeId, result: "DENY", ruleIds: ["LX-03"], reasons: [r("LX-03", "NEVER_ALLOWED", "block")] };
      yield { type: "card", kind: "blocked", data: denyTaint(doc?.id ?? "", "change_refund_destination", "MOCK-AGENT-7733", r("LX-03", "REFUND_REDIRECT", "block")) };
      yield* say(L("reply.refund_redirect"));
      return;
    }

    case "how_much": {
      yield* step("s1", L("step.reading_fee"), "invoice.read+fx.quote", 500);
      const q = quoteCard(refresh());
      yield { type: "card", kind: "quote", data: q };
      yield* say(
        L(isParent ? "reply.how_much_parent" : "reply.how_much", {
          ref: "HBU-2027-0042",
          receive: tuitionTotal,
          due: fmtDate(invoice.dueDate, loc),
          send: fmtMoney(Number(q.send.amount), "VND", loc),
        }) +
          " " +
          L("reply.schedule", { part: fmtMoney(INSTALMENT_KRW, "KRW", loc), d1: fmtDate(INSTALMENT_SCHEDULE[0].dueAt, loc), d2: fmtDate(INSTALMENT_SCHEDULE[1].dueAt, loc) }),
      );
      return;
    }

    case "status": {
      yield* step("s1", L("step.status"), "bank.status+bursar.status", 500);
      d = refresh();
      const refund = d.refunds.find((x) => x.familyId === familyId);
      if (refund) {
        yield { type: "card", kind: "refund", data: { refundId: refund.id } };
        const account = `Lotus Home Bank ${refund.destination.maskedNumber}`;
        if (refund.reconciliation) yield* say(L("reply.status_refund_back", { amount: fmtMoney(Number(refund.reconciliation.receivedBack.amount), refund.reconciliation.receivedBack.currency, loc), account }));
        else if (refund.deadline) yield* say(L("reply.status_refund", { deadline: fmtDate(refund.deadline, loc), start: fmtDate(REFUND_POLICY.classesStart, loc), account }));
        else yield* say(L("reply.refusal_after_start"));
        return;
      }
      const claim = pendingClaim();
      if (claim) {
        if (isParent)
          yield { type: "card", kind: "needs", data: { code: "STUDENT_REFUND_REQUEST_REQUIRED", missing: [{ kind: "refusal_and_refund_forms", actorId: d.users[studentOf(d, familyId)].id, action: "upload_and_sign" }] } };
        else yield { type: "card", kind: "approval_required", data: { ...claim, approvalId: claim.id } };
        yield* say(L(isParent ? "reply.refund_parent_wait" : "reply.refund_sign_first"));
        return;
      }
      if (askedRefund && isParent) {
        yield { type: "card", kind: "needs", data: { code: "STUDENT_REFUND_REQUEST_REQUIRED", missing: [{ kind: "refusal_and_refund_forms", actorId: d.users[studentOf(d, familyId)].id, action: "upload_and_sign" }] } };
        yield* say(L("reply.refund_parent_wait"));
        return;
      }
      const pay = tuitionPayment();
      if (pay) {
        if (pay.status === "matched") yield* say(L("reply.already_paid", { receive: tuitionTotal }));
        else yield* say(L("reply.status_moving", { status: pay.status.replaceAll("_", " ") }));
        yield { type: "card", kind: "info", data: { code: "PAYMENT_STATUS", paymentId: pay.id } };
        return;
      }
      yield* say(pendingTuitionApproval() ? L("reply.status_waiting") : L("reply.status_none"));
      return;
    }

    case "rent": {
      if (frozen) {
        yield* say(L("reply.frozen"));
        return;
      }
      d = refresh();
      // v1.17: rent needs a verified lease (student) and a monthly limit (parent) before anything is paid.
      const missing = rentMissing(d, familyId);
      if (missing.length) {
        yield { type: "disposition", envelopeId: nextId("env", d), result: "ESCALATE", ruleIds: ["M-01"], reasons: [r("M-01", "MANDATE_REQUIRED", "warn")] };
        yield { type: "card", kind: "needs", data: { code: "RENT_PREREQUISITES_REQUIRED", missing, reasons: [r("M-01", "MANDATE_REQUIRED", "warn")], result: "ESCALATE", ruleIds: ["M-01"] } };
        yield* say(L(missing.some((x) => x.kind === "rental_agreement") ? "reply.rent_needs_lease" : "reply.rent_needs"));
        return;
      }
      const p = payRent(d, familyId);
      commit(d);
      if (!p) {
        yield* say(L("reply.rent_done"));
        return;
      }
      yield { type: "disposition", envelopeId: nextId("env", refresh()), result: "AUTO_EXECUTE", ruleIds: ["L2-01"], reasons: [r("L2-01", "WITHIN_MANDATE", "info")] };
      yield { type: "card", kind: "info", data: { ...p } as unknown as Record<string, unknown> };
      yield* say(L("reply.rent_paid", { amount: fmtMoney(RENT_KRW, "KRW", loc), payee: landlordPayee.name.replace(" (MOCK)", "") }));
      return;
    }

    case "crypto":
    case "passport":
    case "remember_account":
    case "raise_limit":
    case "structuring": {
      const map = {
        crypto: { key: "reply.crypto", rule: "LX-03", code: "CRYPTO" },
        passport: { key: "reply.passport", rule: "LX-03", code: "EXPORT_PII" },
        remember_account: { key: "reply.remember_account", rule: "LX-03", code: "REGISTRY_WRITE" },
        raise_limit: { key: "reply.raise_limit", rule: "LX-03", code: "RAISE_LIMIT" },
        structuring: { key: "reply.structuring", rule: "R-CN-02", code: "STRUCTURING" },
      } as const;
      const it = map[intent];
      d = refresh();
      const envelopeId = nextId("env", d);
      appendAudit(d, { actor: "agent", kind: "disposition", summary: it.code, ruleIds: [it.rule], envelopeId });
      commit(d);
      // Same shape as the live API: engine reason first, then the LX-03 intent code.
      const base = it.rule === "LX-03" ? r("LX-03", "NEVER_ALLOWED", "block") : r(it.rule, it.code, "block");
      yield { type: "disposition", envelopeId, result: "DENY", ruleIds: [base.ruleId], reasons: [base] };
      yield {
        type: "card",
        kind: "blocked",
        data: { attempted: { action: it.code.toLowerCase(), provenance: "user_input" }, outOfBandVerificationRequired: false, reasons: [base, r("LX-03", it.code, "block")], result: "DENY", ruleIds: [base.ruleId] },
      };
      yield* say(L(it.key));
      return;
    }

    case "freeze": {
      yield* say(L("reply.freeze_hint"));
      yield { type: "card", kind: "info", data: { code: "FREEZE_HINT" } };
      return;
    }
  }

  async function* tuitionFlow(): AsyncGenerator<AgentEvent> {
    if (refresh().users[persona].admissionDisposition) {
      yield { type: "card", kind: "needs", data: { code: "ADMISSION_RECONFIRMATION_REQUIRED", missing: [{ kind: "admission_reconfirmation", actorId: user.id, action: "contact_university" }] } };
      return;
    }
    yield* step("step_0", L("step.reading_fee"), "invoice.read", 500);
    yield* step("step_1", L("step.credential"), "vc.verify(PayeeCredential)", 550);
    yield* step("step_2", L("step.bank_pack"), "pack.build", 500);
    d = refresh();
    yield { type: "card", kind: "quote", data: quoteCard(d) };
    yield { type: "card", kind: "pack", data: packFor(d, familyId) as unknown as Record<string, unknown> };
    const envelopeId = nextId("env", d);
    yield { type: "envelope", envelopeId, action: "execute_payment", requestedTier: "L2" };
    const missing = tuitionNeeds(d, familyId);
    if (missing.length) {
      const reason = missing.some((x) => x.kind === "mandate") ? r("M-01", "MANDATE_REQUIRED", "warn") : r("R-VN-02", "DOCUMENTS_REQUIRED", "warn");
      d.story.pendingTuition = { ...(d.story.pendingTuition ?? {}), [familyId]: true };
      appendAudit(d, { actor: "agent", kind: "disposition", summary: reason.code, ruleIds: [reason.ruleId], envelopeId });
      commit(d);
      yield { type: "disposition", envelopeId, result: "ESCALATE", ruleIds: [reason.ruleId], reasons: [reason] };
      yield { type: "card", kind: "needs", data: { missing, reasons: [reason], result: "ESCALATE", ruleIds: [reason.ruleId] } };
      yield* say(L("reply.needs", { amount: tuitionTotal }));
      return;
    }
    const approval = createTuitionApproval(d, familyId);
    d.story.pendingTuition = { ...(d.story.pendingTuition ?? {}), [familyId]: false };
    commit(d);
    emit({ type: "approval_created", data: { approvalId: approval.id, action: approval.action, status: approval.status }, familyId });
    yield { type: "disposition", envelopeId, result: "ESCALATE", ruleIds: ["L3-01"], reasons: approval.risk.features };
    yield { type: "card", kind: "approval_required", data: { ...approval, approvalId: approval.id } };
    yield* say(L("reply.approval_sent"));
  }
}
