/**
 * In-browser mock backend state. Implements contract v1 closely enough that the UI
 * code path is identical in mock and live mode (the client talks HTTP-shaped
 * Requests/Responses to src/mock/server.ts).
 *
 * State lives in localStorage and is synced across tabs and iframes with
 * BroadcastChannel, so the demo stage can show Minh's and Linh's phones side by side.
 * The audit log uses real SHA-256 hash chaining, so tamper/verify is genuine even in mock mode.
 */
import { sha256 } from "@noble/hashes/sha2.js";
import { bytesToHex, utf8ToBytes } from "@noble/hashes/utils.js";
import type {
  Anchor,
  AppEvent,
  Approval,
  AuditEntry,
  DocumentRecord,
  Mandate,
  Payment,
  PersonaId,
  Refund,
  Thread,
  User,
} from "@/lib/api/types";
import { SIM_START, users as seedUsers } from "./fixtures";

export interface StoredThread extends Thread {
  owner: PersonaId;
}

export interface DB {
  v: number;
  clock: { baseSim: number; baseReal: number };
  users: Record<PersonaId, User>;
  sessions: Record<string, PersonaId>;
  frozen: Record<string, boolean>;
  mandates: (Mandate & { familyId: string })[];
  approvals: (Approval & { familyId: string })[];
  payments: (Payment & { familyId: string; stage?: { at: number; to: Payment["status"] }[] })[];
  refunds: (Refund & { familyId: string })[];
  documents: (DocumentRecord & { familyId: string; sampleId?: string })[];
  threads: Record<string, StoredThread>;
  audit: AuditEntry[];
  anchors: Anchor[];
  tampered: { seq: number; original: string } | null;
  blockNumber: number;
  story: {
    pendingInvoiceDocId?: string;
    /** A tuition request is waiting for its prerequisites (resumes when they arrive). */
    pendingTuition?: Record<string, boolean>;
    lastRentMonth?: Record<string, string>;
  };
  counters: Record<string, number>;
}

const KEY = "bb-mock-db-v8";
const CHANNEL = "bb-mock";
const DB_VERSION = 8;

export const GENESIS = "0".repeat(64);

export function hex(input: string) {
  return bytesToHex(sha256(utf8ToBytes(input)));
}

export function entryPayload(e: Omit<AuditEntry, "hash" | "anchoredIn">) {
  return JSON.stringify({
    seq: e.seq,
    at: e.at,
    actor: e.actor,
    kind: e.kind,
    summary: e.summary,
    ruleIds: e.ruleIds,
    envelopeId: e.envelopeId ?? null,
    prevHash: e.prevHash,
  });
}

export function merkleRoot(hashes: string[]): string {
  if (hashes.length === 0) return GENESIS;
  let level = hashes.slice();
  while (level.length > 1) {
    const next: string[] = [];
    for (let i = 0; i < level.length; i += 2) {
      const a = level[i];
      const b = level[i + 1] ?? a;
      next.push(hex(a + b));
    }
    level = next;
  }
  return level[0];
}

// ---------------------------------------------------------------------------

let db: DB | null = null;
let channel: BroadcastChannel | null = null;
type Listener = (e: AppEvent & { familyId?: string; persona?: PersonaId }) => void;
const listeners = new Set<Listener>();
const syncListeners = new Set<() => void>();

function isBrowser() {
  return typeof window !== "undefined";
}

export function simNow(d: DB = getDB()): number {
  return d.clock.baseSim;
}
export function simIso(d: DB = getDB()) {
  return new Date(simNow(d)).toISOString();
}

export function nextId(prefix: string, d: DB = getDB()) {
  d.counters[prefix] = (d.counters[prefix] ?? 0) + 1;
  const n = d.counters[prefix];
  const tail = hex(`${prefix}-${n}-bb`).slice(0, 8);
  return `${prefix}_${tail}`;
}

function seed(): DB {
  const now = Date.now();
  const d: DB = {
    v: DB_VERSION,
    clock: { baseSim: Date.parse(SIM_START), baseReal: now },
    users: structuredClone(seedUsers),
    sessions: {},
    frozen: {},
    mandates: [],
    approvals: [],
    payments: [],
    refunds: [],
    documents: [],
    threads: {},
    audit: [],
    anchors: [],
    tampered: null,
    blockNumber: 1290,
    story: { lastRentMonth: {} },
    counters: {},
  };

  return d;
}

function persist(d: DB) {
  if (!isBrowser()) return;
  try {
    localStorage.setItem(KEY, JSON.stringify(d));
  } catch {
    /* quota or privacy mode: keep in memory */
  }
}

function load(): DB | null {
  if (!isBrowser()) return null;
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as DB;
    if (parsed.v !== DB_VERSION) return null;
    return parsed;
  } catch {
    return null;
  }
}

function ensureChannel() {
  if (!isBrowser() || channel) return;
  if (typeof BroadcastChannel === "undefined") return;
  channel = new BroadcastChannel(CHANNEL);
  channel.onmessage = (msg) => {
    const data = msg.data as { kind: "sync" } | { kind: "event"; event: AppEvent & { familyId?: string } };
    const fresh = load();
    if (fresh) db = fresh;
    if (data.kind === "event") listeners.forEach((l) => l(data.event));
    syncListeners.forEach((l) => l());
  };
  window.addEventListener("storage", (e) => {
    if (e.key === KEY) {
      const fresh = load();
      if (fresh) db = fresh;
      syncListeners.forEach((l) => l());
    }
  });
}

export function getDB(): DB {
  ensureChannel();
  if (!db) {
    db = load() ?? seed();
    if (!db.audit.length) bootstrapAudit(db);
    persist(db);
  }
  return db;
}

/** Re-read the freshest state from storage before a mutation (another tab may have written). */
export function refresh(): DB {
  const fresh = load();
  if (fresh) db = fresh;
  return getDB();
}

export function commit(d: DB = getDB()) {
  db = d;
  persist(d);
  channel?.postMessage({ kind: "sync" });
  syncListeners.forEach((l) => l());
}

export function emit(event: AppEvent & { familyId?: string }) {
  listeners.forEach((l) => l(event));
  channel?.postMessage({ kind: "event", event });
}

export function onEvent(l: Listener) {
  ensureChannel();
  listeners.add(l);
  return () => listeners.delete(l);
}

export function onSync(l: () => void) {
  ensureChannel();
  syncListeners.add(l);
  return () => syncListeners.delete(l);
}

export function resetDB() {
  db = seed();
  bootstrapAudit(db);
  commit(db);
  emit({ type: "freeze", data: { reset: true } });
}

// ---------------------------------------------------------------------------
// Audit log

function bootstrapAudit(d: DB) {
  appendAudit(d, { actor: "system", kind: "seed", summary: "Synthetic personas and MOCK issuer seeded", ruleIds: [] });
}

export function appendAudit(
  d: DB,
  e: { actor: string; kind: string; summary: string; ruleIds?: string[]; envelopeId?: string },
  at?: string,
): AuditEntry {
  const prev = d.audit[d.audit.length - 1];
  const seq = prev ? prev.seq + 1 : 1;
  const base = {
    seq,
    at: at ?? simIso(d),
    actor: e.actor,
    kind: e.kind,
    summary: e.summary,
    ruleIds: e.ruleIds ?? [],
    envelopeId: e.envelopeId ?? null,
    prevHash: prev ? prev.hash : GENESIS,
  };
  const entry: AuditEntry = { ...base, hash: hex(entryPayload(base)), anchoredIn: null };
  d.audit.push(entry);
  maybeAnchor(d);
  return entry;
}

const ANCHOR_EVERY = 6;

export function flushAnchors(d: DB) { return maybeAnchor(d, true); }

function maybeAnchor(d: DB, force = false) {
  const lastAnchored = d.anchors.length ? d.anchors[d.anchors.length - 1].lastSeq : 0;
  const pending = d.audit.filter((a) => a.seq > lastAnchored);
  if (!pending.length || (!force && pending.length < ANCHOR_EVERY)) return false;
  const root = merkleRoot(pending.map((p) => p.hash));
  d.blockNumber += 3 + (pending.length % 4);
  const anchor: Anchor = {
    root,
    firstSeq: pending[0].seq,
    lastSeq: pending[pending.length - 1].seq,
    blockNumber: d.blockNumber,
    txHash: "0x" + hex(`anchor:${root}:${d.blockNumber}`),
    at: simIso(d),
  };
  d.anchors.push(anchor);
  pending.forEach((p) => (p.anchoredIn = anchor.blockNumber));
  emit({ type: "anchor", data: { ...anchor } });
  emit({ type: "anchor_updated", data: { status: "ready", registrationStatus: "ready" } });
  return true;
}

export function verifyAudit(d: DB) {
  let prevHash = GENESIS;
  let firstBadSeq: number | null = null;
  let detail: string | null = null;
  for (const e of d.audit) {
    const recomputed = hex(entryPayload({ ...e, prevHash }));
    if (e.prevHash !== prevHash || recomputed !== e.hash) {
      firstBadSeq = e.seq;
      detail = `Entry #${e.seq}: recomputed hash ${recomputed.slice(0, 12)}… does not match stored ${e.hash.slice(0, 12)}…`;
      break;
    }
    prevHash = e.hash;
  }
  let anchorsOk = 0;
  let badAnchor: Anchor | null = null;
  for (const a of d.anchors) {
    const slice = d.audit.filter((e) => e.seq >= a.firstSeq && e.seq <= a.lastSeq);
    const recomputedHashes = slice.map((e, i) => {
      const prev = i === 0 ? d.audit.find((x) => x.seq === e.seq - 1)?.hash ?? GENESIS : slice[i - 1].hash;
      return hex(entryPayload({ ...e, prevHash: prev }));
    });
    if (merkleRoot(recomputedHashes) === a.root) anchorsOk += 1;
    else if (!badAnchor) badAnchor = a;
  }
  if (firstBadSeq && badAnchor) {
    detail += ` Anchor in block #${badAnchor.blockNumber} (entries ${badAnchor.firstSeq}–${badAnchor.lastSeq}) no longer matches its Merkle root.`;
  }
  return {
    ok: firstBadSeq === null && !badAnchor,
    entries: d.audit.length,
    anchors: anchorsOk,
    firstBadSeq,
    detail,
  };
}

export function tamper(d: DB, seq: number) {
  const e = d.audit.find((x) => x.seq === seq);
  if (!e) return false;
  if (d.tampered) restore(d);
  d.tampered = { seq, original: e.summary };
  // Flip one byte: change one character of the summary (e.g. an amount digit or account digit).
  const idx = Math.max(0, e.summary.search(/\d/));
  const ch = e.summary[idx];
  const flipped = ch >= "0" && ch <= "8" ? String.fromCharCode(ch.charCodeAt(0) + 1) : ch === "9" ? "8" : ch === "a" ? "b" : "a";
  e.summary = e.summary.slice(0, idx) + flipped + e.summary.slice(idx + 1);
  return true;
}

export function restore(d: DB) {
  if (!d.tampered) return false;
  const e = d.audit.find((x) => x.seq === d.tampered!.seq);
  if (e) e.summary = d.tampered.original;
  d.tampered = null;
  return true;
}
