/**
 * mockFetch: an in-browser implementation of API contract v1.
 * The API client calls this instead of window.fetch in mock mode, so request/response
 * shapes, SSE parsing and error handling are exercised exactly as in live mode.
 */
import type { AgentEvent, AgentMessage, Locale, MandateCreate, PersonaId } from "@/lib/api/types";
import { appendAudit, commit, emit, getDB, nextId, onEvent, refresh, resetDB, restore, simIso, simNow, tamper, verifyAudit } from "./db";
import {
  rentSetup,
  studyPlan,
  approve,
  cancelPayment,
  consentHashOf,
  cosignReview,
  createMandate,
  familyOf,
  freeze,
  ingestDocument,
  quoteFor,
  reject,
  revokeMandate,
  signMandate,
  tick,
  unfreeze,
} from "./domain";
import { runAgent } from "./agent";
import { detectLocale } from "./agent-copy";
import { scenarioTable } from "./scenarios";
import { RENT_KRW, landlordPayee, samples } from "./fixtures";

const PK_KEY = "bb-mock-passkeys";
const mockPasskeys = {
  get(userId: string): string | undefined {
    try {
      return (JSON.parse(localStorage.getItem(PK_KEY) ?? "{}") as Record<string, string>)[userId];
    } catch {
      return undefined;
    }
  },
  set(userId: string, id: string) {
    try {
      const all = JSON.parse(localStorage.getItem(PK_KEY) ?? "{}") as Record<string, string>;
      localStorage.setItem(PK_KEY, JSON.stringify({ ...all, [userId]: id }));
    } catch {
      /* ignore */
    }
  },
};

const sleep = (ms: number) => new Promise((res) => setTimeout(res, ms));

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}
function err(status: number, code: string, message: string, ruleId?: string) {
  return json({ error: { code, message, ruleId, details: {} } }, status);
}

function sse(gen: () => AsyncGenerator<{ event?: string; data: unknown }>, signal?: AbortSignal | null) {
  const enc = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      try {
        for await (const ev of gen()) {
          if (signal?.aborted) break;
          const head = ev.event ? `event: ${ev.event}\n` : "";
          controller.enqueue(enc.encode(`${head}data: ${JSON.stringify(ev.data)}\n\n`));
        }
      } catch (e) {
        controller.enqueue(enc.encode(`event: error\ndata: ${JSON.stringify({ code: "MOCK_ERROR", message: String(e) })}\n\n`));
      }
      controller.close();
    },
  });
  return new Response(stream, { status: 200, headers: { "content-type": "text/event-stream" } });
}

function personaFrom(headers: Headers): PersonaId | null {
  const auth = headers.get("authorization") ?? "";
  const m = auth.match(/^Bearer mock\.(\w+)$/);
  return (m?.[1] as PersonaId) ?? null;
}

const ticking = { started: false };
function ensureTicker() {
  if (ticking.started || typeof window === "undefined") return;
  ticking.started = true;
  window.setInterval(() => tick(), 1000);
}

function stripFamily<T extends { familyId?: string }>(x: T) {
  const { familyId: _f, ...rest } = x as T & { stage?: unknown; sampleId?: unknown };
  void _f;
  delete (rest as { stage?: unknown }).stage;
  return rest;
}

export async function mockFetch(input: string, init: RequestInit = {}): Promise<Response> {
  ensureTicker();
  const url = new URL(input, "http://mock.local");
  const path = url.pathname.replace(/^\/api/, "");
  const method = (init.method ?? "GET").toUpperCase();
  const headers = new Headers(init.headers);
  const persona = personaFrom(headers);
  let body: Record<string, unknown> = {};
  if (typeof init.body === "string") {
    try {
      body = JSON.parse(init.body);
    } catch {
      body = {};
    }
  }
  // small network latency so loading states are real
  await sleep(method === "GET" ? 60 : 140);

  const seg = path.split("/").filter(Boolean);
  const is = (m: string, pattern: string) => {
    if (m !== method) return null;
    const p = pattern.split("/").filter(Boolean);
    if (p.length !== seg.length) return null;
    const params: Record<string, string> = {};
    for (let i = 0; i < p.length; i++) {
      if (p[i].startsWith(":")) params[p[i].slice(1)] = decodeURIComponent(seg[i]);
      else if (p[i] !== seg[i]) return null;
    }
    return params;
  };

  // ---- unauthenticated ----
  if (is("POST", "/session")) {
    const p = body.persona as PersonaId;
    const d = getDB();
    if (!d.users[p]) return err(400, "UNKNOWN_PERSONA", "Unknown persona");
    return json({ token: `mock.${p}`, user: { ...d.users[p], frozen: !!d.frozen[d.users[p].familyId] } });
  }
  if (is("GET", "/clock")) return json({ now: simIso(), simulated: true });
  if (is("POST", "/demo/reset")) {
    resetDB();
    return json({ ok: true, registrationStatus: "ready", anchorStatus: "pending", recovery: "automatic_retry" });
  }
  if (is("GET", "/demo/samples")) return json(samples);
  if (is("GET", "/scenarios")) return json(scenarioTable.map(({ id, title, priority, tags }) => ({ id, title, priority, tags: [...tags] })));
  if (is("POST", "/scenarios/run")) {
    const ids = (body.ids as string[] | undefined) ?? scenarioTable.map((s) => s.id);
    return sse(async function* () {
      let passed = 0;
      const list = scenarioTable.filter((s) => ids.includes(s.id));
      for (const s of list) {
        yield { data: { id: s.id, status: "running", expected: s.expected, actual: "", ms: 0, auditSeqs: [] } };
        const ms = 180 + ((s.id.charCodeAt(2) * 37) % 420);
        await sleep(ms);
        passed += 1;
        const seq = getDB().audit.length;
        yield { data: { id: s.id, status: "pass", expected: s.expected, actual: s.actual, ms, auditSeqs: [seq] } };
      }
      yield { data: { summary: { passed, failed: list.length - passed, total: list.length } } };
    }, init.signal);
  }
  if (is("GET", "/chain/status")) {
    const d = getDB();
    return json({
      network: "FISCO BCOS (team-operated, 4 nodes)",
      connected: true,
      registrationStatus: "ready",
      anchorStatus: d.audit.length > (d.anchors.at(-1)?.lastSeq ?? 0) ? "retrying" : "ready",
      blockNumber: d.blockNumber,
      mock: true,
      contracts: [
        { name: "AuditAnchor", address: "0x6a2f1c0e9b3d4a5f8e7c1b2a3d4e5f60718293a4" },
        { name: "CredentialRegistry", address: "0x91b4e2d7c8a6f5e3b2d1c0a9f8e7d6c5b4a39281" },
        { name: "MandateGuard", address: "0x3c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d" },
      ],
    });
  }
  if (is("GET", "/chain/anchors")) return json([...getDB().anchors].reverse());
  if (is("GET", "/audit/entries")) {
    const after = Number(url.searchParams.get("after") ?? 0);
    const limit = Number(url.searchParams.get("limit") ?? 100);
    const all = getDB().audit.filter((e) => e.seq > after);
    const entries = all.slice(0, limit);
    return json({ entries, next: all.length > limit ? entries[entries.length - 1].seq : null });
  }
  if (is("POST", "/audit/verify")) {
    await sleep(500);
    return json(verifyAudit(refresh()));
  }
  if (is("POST", "/demo/tamper")) {
    const d = refresh();
    const ok = tamper(d, Number(body.seq));
    commit(d);
    return json({ ok });
  }
  if (is("POST", "/demo/restore")) {
    const d = refresh();
    const ok = restore(d);
    commit(d);
    return json({ ok });
  }
  if (is("POST", "/clock/advance")) {
    const d = refresh();
    const ms = (Number(body.days ?? 0) * 24 + Number(body.hours ?? 0)) * 3600_000;
    d.clock.baseSim += ms;
    appendAudit(d, { actor: "system", kind: "clock.advanced", summary: `Simulated clock advanced by ${body.days ?? 0}d ${body.hours ?? 0}h (demo only)` });
    commit(d);
    tick();
    return json({ now: simIso() });
  }
  if (is("GET", "/fx/quote")) {
    const from = url.searchParams.get("from") ?? "VND";
    const to = url.searchParams.get("to") ?? "KRW";
    const amount = Number(url.searchParams.get("amount") ?? 0);
    const side = (url.searchParams.get("side") ?? "send") as "send" | "receive";
    return json(quoteFor(getDB(), from, to, amount, side));
  }

  // ---- authenticated ----
  if (!persona) return err(401, "UNAUTHENTICATED", "Missing or invalid bearer token");
  const d0 = getDB();
  const user = d0.users[persona];
  const familyId = familyOf(d0, persona);

  if (is("GET", "/me")) return json({ ...user, frozen: !!d0.frozen[familyId], simulatedNow: simIso(d0) });
  if (is("GET", "/study-plan/standard-admission-certificate.pdf")) {
    const pdf = await fetch("/samples/live/admission.pdf");
    return new Response(await pdf.arrayBuffer(), { headers: { "content-type": "application/pdf" } });
  }
  if (is("GET", "/study-plan")) return json(studyPlan(d0, familyId, url.searchParams.get("locale") ?? "en"));
  if (is("GET", "/rent")) return json(rentSetup(d0, familyId));
  if (is("GET", "/catalog"))
    return json({
      issuer: "did:key:z6MkhB7tQkV1nXr9oLzqWb3Hn8e4JfZu2YcPq5sVg6dKxA1u",
      bankPayees: [{ id: landlordPayee.id, name: landlordPayee.name, amount: RENT_KRW.toFixed(2), currency: "KRW", nameCheck: "match", provenance: "bank_record" }],
      familyId,
      bank: "MOCK",
      bursar: "MOCK",
      demo: true,
    });

  // WebAuthn (mock relying party: challenges are consent hashes; demo authenticator accepted)
  if (is("POST", "/webauthn/register/options")) {
    return json({
      rp: { name: "BursarBridge (demo)", id: typeof location !== "undefined" ? location.hostname : "localhost" },
      user: { id: btoa(user.id).replace(/=/g, ""), name: user.name, displayName: user.name },
      challenge: btoa(nextId("chal", d0)).replace(/=/g, ""),
      pubKeyCredParams: [{ alg: -7, type: "public-key" }, { alg: -257, type: "public-key" }],
      authenticatorSelection: { residentKey: "preferred", userVerification: "required", authenticatorAttachment: "platform" },
      timeout: 60000,
      attestation: "none",
    });
  }
  if (is("POST", "/webauthn/register/verify")) {
    // Like the API, remember which device credential belongs to this person so assertions can name it.
    const id = (body.credential as { id?: string } | undefined)?.id;
    if (id) mockPasskeys.set(user.id, id);
    return json({ ok: true });
  }
  if (is("POST", "/webauthn/assert/options")) {
    const refId = String(body.refId ?? "");
    const d = getDB();
    const target =
      d.approvals.find((a) => a.id === refId)?.consentHash ??
      d.mandates.find((x) => x.id === refId)?.hash ??
      consentHashOf({ purpose: body.purpose, refId, at: simIso(d) });
    const bytes = target.match(/.{2}/g)!.map((h) => parseInt(h, 16));
    const b64 = btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
    return json({ challenge: b64, timeout: 60000, rpId: typeof location !== "undefined" ? location.hostname : "localhost", userVerification: "required", allowCredentials: mockPasskeys.get(user.id) ? [{ type: "public-key", id: mockPasskeys.get(user.id) }] : [] });
  }
  if (is("POST", "/webauthn/assert/verify")) {
    const cred = body.credential as { demo?: boolean } | undefined;
    const h = consentHashOf({ refId: body.refId, cred: cred?.demo ? "demo" : "platform" });
    return json({ ok: true, assertionHash: (cred?.demo ? "demo-" : "pk-") + h.slice(0, 40) });
  }

  // Agent
  if (is("POST", "/agent/threads")) {
    const d = refresh();
    const threadId = nextId("thr", d);
    d.threads[threadId] = { threadId, owner: persona, messages: [] };
    commit(d);
    return json({ threadId });
  }
  let p = is("GET", "/agent/threads/:id");
  if (p) {
    const t = getDB().threads[p.id];
    if (!t) return err(404, "NOT_FOUND", "Thread not found");
    return json({ threadId: t.threadId, messages: t.messages });
  }
  p = is("POST", "/agent/threads/:id/messages");
  if (p) {
    const threadId = p.id;
    const d = refresh();
    const t = d.threads[threadId];
    if (!t) return err(404, "NOT_FOUND", "Thread not found");
    const text = String(body.text ?? "");
    const documentIds = (body.documentIds as string[]) ?? [];
    const userMsg: AgentMessage = { id: nextId("msg", d), role: "user", text, createdAt: simIso(d), documentIds, author: user.name };
    t.messages.push(userMsg);
    appendAudit(d, {
      actor: persona.startsWith("student") ? "student" : "parent",
      kind: "chat.message",
      summary: `Chat message received (${text.length} chars${documentIds.length ? `, ${documentIds.length} document(s)` : ""}); treated as untrusted input`,
    });
    commit(d);
    const locale = (body.locale as Locale) ?? user.locale;
    return sse(async function* () {
      const events: AgentEvent[] = [];
      let full = "";
      for await (const ev of runAgent({ persona, text, documentIds, locale })) {
        if (ev.type === "token") {
          full += ev.text;
          const last = events[events.length - 1];
          if (last?.type === "token") last.text += ev.text;
          else events.push({ ...ev });
        } else events.push(ev);
        const { type, ...data } = ev;
        yield { event: type, data };
      }
      const d2 = refresh();
      const msg: AgentMessage = { id: nextId("msg", d2), role: "assistant", text: full.trim(), createdAt: simIso(d2), events };
      d2.threads[threadId].messages.push(msg);
      commit(d2);
      yield { event: "done", data: { messageId: msg.id } };
    }, init.signal);
  }

  // Documents
  if (is("POST", "/documents")) {
    const form = init.body instanceof FormData ? init.body : null;
    const file = form?.get("file");
    const filename = file instanceof File ? file.name : String(form?.get("filename") ?? "document.pdf");
    const kind = form?.get("kind") ? String(form.get("kind")) : undefined;
    const d = refresh();
    const doc = ingestDocument(d, persona, filename, kind);
    commit(d);
    return json(stripFamily(doc));
  }
  p = is("GET", "/documents/:id");
  if (p) {
    const doc = getDB().documents.find((x) => x.id === p!.id);
    return doc ? json(stripFamily(doc)) : err(404, "NOT_FOUND", "Document not found");
  }
  if (is("GET", "/documents")) {
    return json(getDB().documents.filter((x) => x.familyId === familyId && (user.role === "parent" || x.uploadedBy === user.id)).map(stripFamily));
  }

  // Mandates
  if (is("GET", "/mandates")) return json(getDB().mandates.filter((x) => x.familyId === familyId).map(stripFamily));
  if (is("POST", "/mandates")) {
    if (user.role !== "parent") return err(403, "FORBIDDEN", "Only the paying parent can create a mandate");
    const d = refresh();
    const mdt = createMandate(d, persona, body as unknown as MandateCreate);
    commit(d);
    return json(stripFamily(mdt), 201);
  }
  p = is("POST", "/mandates/:id/sign");
  if (p) {
    const d = refresh();
    const a = body.assertion as { demo?: boolean; assertionHash?: string } | undefined;
    const mdt = signMandate(d, persona, p.id, a?.demo || String(a?.assertionHash ?? "").startsWith("demo") ? "demo" : "platform");
    commit(d);
    if (mdt?.purpose === "tuition") void resumePendingTuition(familyId);
    return mdt ? json(stripFamily(mdt)) : err(404, "NOT_FOUND", "Mandate not found");
  }
  p = is("POST", "/mandates/:id/revoke");
  if (p) {
    const d = refresh();
    const mdt = revokeMandate(d, p.id);
    commit(d);
    return mdt ? json(stripFamily(mdt)) : err(404, "NOT_FOUND", "Mandate not found");
  }

  // Approvals
  if (is("GET", "/approvals")) {
    const status = url.searchParams.get("status") ?? "pending"; // same default as the API
    const list = getDB()
      .approvals.filter((a) => a.familyId === familyId)
      .filter((a) => status === "all" || status.split(",").includes(a.status))
      .filter((a) => user.role === "judge" || !a.approverId || a.approverId === user.id || user.role === "parent")
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
    return json(list.map(stripFamily));
  }
  p = is("GET", "/approvals/:id");
  if (p) {
    const a = getDB().approvals.find((x) => x.id === p!.id);
    return a ? json(stripFamily(a)) : err(404, "NOT_FOUND", "Approval not found");
  }
  p = is("POST", "/approvals/:id/approve");
  if (p) {
    const d = refresh();
    const target = d.approvals.find((x) => x.id === p!.id);
    if (!target) return err(404, "NOT_FOUND", "Approval not found");
    if (d.frozen[target.familyId] && !["refund_claim", "escalation_letter"].includes(target.action)) return err(423, "FROZEN", "Family is frozen; unfreeze first", "KILL-01");
    if (target.approverId && target.approverId !== user.id) return err(403, "NOT_APPROVER", "This approval belongs to another family member");
    if (target.status !== "pending") return err(409, "NOT_PENDING", `Approval is ${target.status}`);
    const a = body.assertion as { demo?: boolean; assertionHash?: string } | undefined;
    const res = approve(d, persona, p.id, a?.demo || String(a?.assertionHash ?? "").startsWith("demo") ? "demo" : "platform");
    commit(d);
    return json(stripFamily(res!));
  }
  p = is("POST", "/approvals/:id/cosign");
  if (p) {
    if (user.role !== "cosigner") return err(403, "ROLE_REQUIRED", "Only the home co-signer can co-sign a review");
    const d = refresh();
    const res = cosignReview(d, persona, p.id);
    commit(d);
    if (!res) return err(409, "INVALID_STATE", "No co-sign review pending");
    emit({ type: "approval_updated", data: { approvalId: res.id, status: res.status, cosigned: true, cosignedAt: res.cosignedAt ?? null }, familyId });
    emit({ type: "payment_updated", data: { approvalId: res.id, cosigned: true, cosignedAt: res.cosignedAt ?? null }, familyId });
    return json(stripFamily(res));
  }
  p = is("POST", "/approvals/:id/reject");
  if (p) {
    const d = refresh();
    const target = d.approvals.find((x) => x.id === p!.id);
    if (target && user.role !== (target.action === "refund_claim" ? "student" : "parent")) return err(403, "POLICY_DENIED", "Operation not permitted");
    const res = reject(d, persona, p.id, body.reason as string | undefined);
    commit(d);
    return res ? json(stripFamily(res)) : err(404, "NOT_FOUND", "Approval not found");
  }

  // v1.13: readable projection of a consent-bound refund form. The mock serves the API's static unsigned example.
  p = is("GET", "/approvals/:id/paperwork/:kind");
  if (p) {
    const a = getDB().approvals.find((x) => x.id === p!.id && x.familyId === familyId);
    const kind = p.kind;
    if (!a || a.action !== "refund_claim" || !["admission_withdrawal", "tuition_refund_application"].includes(kind)) return err(404, "NOT_FOUND", "Paperwork not found");
    const pdf = await fetch(`/samples/live/${kind}.pdf`);
    return new Response(await pdf.arrayBuffer(), { status: 200, headers: { "content-type": "application/pdf" } });
  }

  // Payments & refunds
  if (is("GET", "/payments")) {
    return json(
      getDB()
        .payments.filter((x) => x.familyId === familyId)
        .sort((a, b) => (b.createdAt ?? "").localeCompare(a.createdAt ?? ""))
        .map(stripFamily),
    );
  }
  p = is("GET", "/payments/:id");
  if (p) {
    const x = getDB().payments.find((y) => y.id === p!.id);
    return x ? json(stripFamily(x)) : err(404, "NOT_FOUND", "Payment not found");
  }
  p = is("POST", "/payments/:id/cancel");
  if (p) {
    const d = refresh();
    const x = d.payments.find((y) => y.id === p!.id);
    if (!x) return err(404, "NOT_FOUND", "Payment not found");
    if (x.status !== "sent" || !x.cancelUntil || simNow(d) >= Date.parse(x.cancelUntil)) return err(409, "CANCEL_WINDOW_CLOSED", "The 30-minute cancel window has closed");
    const res = cancelPayment(d, p.id);
    commit(d);
    return json(stripFamily(res!));
  }
  // v1.16: destination.balance is the payer's current balance (receipt included), not a filing-time snapshot.
  const withBalance = (x: ReturnType<typeof getDB>["refunds"][number]) => {
    const acct = Object.values(getDB().users).flatMap((u) => u.accounts).find((a) => a.id === x.destination.id);
    return stripFamily({ ...x, destination: acct ? { ...x.destination, balance: acct.balance } : x.destination });
  };
  if (is("GET", "/refunds")) return json(getDB().refunds.filter((x) => x.familyId === familyId).map(withBalance));
  p = is("GET", "/refunds/:id");
  if (p) {
    const x = getDB().refunds.find((y) => y.id === p!.id);
    return x ? json(withBalance(x)) : err(404, "NOT_FOUND", "Refund not found");
  }

  // Freeze
  if (is("POST", "/freeze")) {
    const d = refresh();
    const res = freeze(d, persona);
    commit(d);
    return json(res);
  }
  if (is("POST", "/unfreeze")) {
    if (!body.assertion) return err(400, "ASSERTION_REQUIRED", "Unfreezing needs a passkey assertion");
    const d = refresh();
    const res = unfreeze(d, persona);
    commit(d);
    return json(res);
  }

  // Notifications (SSE, long-lived)
  if (is("GET", "/events")) {
    const signal = init.signal;
    return sse(async function* () {
      const queue: { type: string; data: unknown }[] = [];
      let wake: (() => void) | null = null;
      const off = onEvent((e) => {
        if (e.familyId && e.familyId !== familyId && user.role !== "judge") return;
        queue.push({ type: e.type, data: e.data });
        wake?.();
      });
      try {
        yield { event: "ready", data: {} };
        while (!signal?.aborted) {
          if (!queue.length) await new Promise<void>((res) => { wake = res; setTimeout(res, 15000); });
          wake = null;
          while (queue.length) {
            const ev = queue.shift()!;
            yield { event: ev.type, data: ev.data };
          }
        }
      } finally {
        off();
      }
    }, signal);
  }

  return err(404, "NOT_FOUND", `No mock route for ${method} ${path}`);
}

/**
 * Mirrors API r5: once the last missing step is done (here, the mandate), the family's pending tuition request
 * moves on by itself. The student's latest conversation gets the assistant's follow-up; no user message is invented.
 */
async function resumePendingTuition(familyId: string) {
  const d = refresh();
  if (!d.story.pendingTuition?.[familyId]) return;
  const student = (Object.keys(d.users) as PersonaId[]).find((k) => d.users[k].familyId === familyId && d.users[k].role === "student");
  if (!student) return;
  const docs = d.documents.filter((x) => x.familyId === familyId && (x.sampleId === "invoice" || x.sampleId === "admission") && !x.warnings.length);
  if (!docs.some((x) => x.sampleId === "invoice")) return; // still waiting for the fee notice: the needs card says so
  const thread = Object.values(d.threads)
    .filter((t) => t.owner === student && t.messages.length)
    .sort((x, y) => (x.messages[x.messages.length - 1].createdAt < y.messages[y.messages.length - 1].createdAt ? 1 : -1))[0];
  if (!thread) return;
  const lastUser = [...thread.messages].reverse().find((m) => m.role === "user" && m.text);
  const locale = detectLocale(lastUser?.text ?? "", d.users[student].locale);
  const events: AgentEvent[] = [];
  let full = "";
  for await (const ev of runAgent({ persona: student, text: "", documentIds: docs.map((x) => x.id), locale })) {
    if (ev.type === "token") {
      full += ev.text;
      const last = events[events.length - 1];
      if (last?.type === "token") last.text += ev.text;
      else events.push({ ...ev });
    } else events.push(ev);
  }
  const d2 = refresh();
  if (!d2.threads[thread.threadId]) return;
  d2.threads[thread.threadId].messages.push({ id: nextId("msg", d2), role: "assistant", text: full.trim(), createdAt: simIso(d2), events });
  commit(d2);
}
