/**
 * Typed API client for contract v1. One code path for mock and live:
 * in mock mode the transport is src/mock/server.ts (an in-browser implementation),
 * in live mode it is window.fetch against NEXT_PUBLIC_API_URL.
 */
import type {
  AgentEvent,
  Anchor,
  ApiErrorBody,
  Approval,
  AuditEntry,
  ChainStatus,
  Clock,
  DocumentRecord,
  FreezeResult,
  FxQuoteResponse,
  Locale,
  Mandate,
  MandateCreate,
  Payment,
  PersonaId,
  Refund,
  RentSetup,
  Scenario,
  StudyPlan,
  ScenarioEvent,
  Session,
  Thread,
  User,
  VerifyResult,
} from "./types";

export type ApiMode = "mock" | "live";

const ENV_MODE = (process.env.NEXT_PUBLIC_API_MODE as ApiMode) || "mock";
// Default goes through the Next.js rewrite (/bbapi -> BB_API_ORIGIN/api) so the browser never needs CORS.
const ENV_URL = process.env.NEXT_PUBLIC_API_URL || "/bbapi";

export function apiMode(): ApiMode {
  if (typeof window !== "undefined") {
    try {
      const o = localStorage.getItem("bb-api-mode");
      if (o === "mock" || o === "live") return o;
    } catch {
      /* ignore */
    }
  }
  return ENV_MODE;
}
/** For useSyncExternalStore: the server always renders the env default. */
export const serverApiMode = (): ApiMode => ENV_MODE;

export function setApiMode(mode: ApiMode | null) {
  try {
    if (mode) localStorage.setItem("bb-api-mode", mode);
    else localStorage.removeItem("bb-api-mode");
  } catch {
    /* ignore */
  }
}
export const apiBaseUrl = ENV_URL;

/** The UI language (the layout sets <html lang>), passed as ?locale= on presentation reads (API r5). */
function uiLocale(): Locale {
  if (typeof document === "undefined") return "en";
  const l = document.documentElement.lang;
  return (["en", "vi", "ko", "zh"].includes(l) ? l : "en") as Locale;
}
const withLocale = (path: string) => `${path}${path.includes("?") ? "&" : "?"}locale=${uiLocale()}`;

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public ruleId?: string,
  ) {
    super(message);
  }
}

type Transport = (url: string, init: RequestInit) => Promise<Response>;

async function transport(): Promise<Transport> {
  if (apiMode() === "mock") {
    const { mockFetch } = await import("@/mock/server");
    return (url, init) => mockFetch(url, init);
  }
  return (url, init) => fetch(`${ENV_URL}${url}`, init);
}

// ---------- sessions ----------
const TOKEN_KEY = () => `bb-tokens-${apiMode()}`;

function readTokens(): Partial<Record<PersonaId, string>> {
  try {
    return JSON.parse(localStorage.getItem(TOKEN_KEY()) ?? "{}");
  } catch {
    return {};
  }
}
function writeToken(persona: PersonaId, token: string | null) {
  const all = readTokens();
  if (token) all[persona] = token;
  else delete all[persona];
  try {
    localStorage.setItem(TOKEN_KEY(), JSON.stringify(all));
  } catch {
    /* ignore */
  }
}

/** Short fingerprint of the cached session (a backend reset issues new sessions and restarts event ids). */
export function sessionHint(persona: PersonaId) {
  return (readTokens()[persona] ?? "").slice(0, 8);
}

const inflight = new Map<PersonaId, Promise<string>>();

async function tokenFor(persona: PersonaId): Promise<string> {
  const cached = readTokens()[persona];
  if (cached) return cached;
  if (!inflight.has(persona)) {
    inflight.set(
      persona,
      (async () => {
        const t = await transport();
        const res = await t("/session", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ persona }) });
        if (!res.ok) throw await toError(res);
        const s = (await res.json()) as Session;
        writeToken(persona, s.token);
        return s.token;
      })().finally(() => inflight.delete(persona)),
    );
  }
  return inflight.get(persona)!;
}

async function toError(res: Response) {
  try {
    const body = (await res.json()) as ApiErrorBody;
    return new ApiError(res.status, body.error?.code ?? "HTTP_" + res.status, body.error?.message ?? res.statusText, body.error?.ruleId);
  } catch {
    return new ApiError(res.status, "HTTP_" + res.status, res.statusText);
  }
}

// ---------- SSE ----------
export async function* readSSE(res: Response): AsyncGenerator<{ event: string; data: unknown }> {
  if (!res.body) return;
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true }).replace(/\r\n/g, "\n");
      let idx: number;
      while ((idx = buf.indexOf("\n\n")) !== -1) {
        const block = buf.slice(0, idx);
        buf = buf.slice(idx + 2);
        let event = "message";
        const data: string[] = [];
        for (const line of block.split("\n")) {
          if (line.startsWith(":")) continue;
          if (line.startsWith("event:")) event = line.slice(6).trim();
          else if (line.startsWith("data:")) data.push(line.slice(5).replace(/^ /, ""));
        }
        if (!data.length) continue;
        let parsed: unknown = data.join("\n");
        try {
          parsed = JSON.parse(parsed as string);
        } catch {
          /* keep raw */
        }
        yield { event, data: parsed };
      }
    }
  } finally {
    reader.releaseLock();
  }
}

// ---------- client ----------
export interface RequestOpts {
  signal?: AbortSignal;
}

export function createClient(persona: PersonaId) {
  async function raw(method: string, path: string, body?: unknown, opts: RequestOpts & { form?: FormData } = {}, retry = true): Promise<Response> {
    const t = await transport();
    const token = await tokenFor(persona);
    const headers: Record<string, string> = { authorization: `Bearer ${token}` };
    let payload: BodyInit | undefined;
    if (opts.form) payload = opts.form;
    else if (body !== undefined) {
      headers["content-type"] = "application/json";
      payload = JSON.stringify(body);
    }
    const res = await t(path, { method, headers, body: payload, signal: opts.signal });
    if (res.status === 401 && retry) {
      writeToken(persona, null);
      return raw(method, path, body, opts, false);
    }
    return res;
  }

  async function req<T>(method: string, path: string, body?: unknown, opts?: RequestOpts & { form?: FormData }): Promise<T> {
    const res = await raw(method, path, body, opts);
    if (!res.ok) throw await toError(res);
    return (await res.json()) as T;
  }

  return {
    persona,
    me: () => req<User>("GET", "/me"),
    /** v1.2: trusted issuer DID and bank-held name-checked payees for this family. */
    catalog: () =>
      req<{ issuer: string; bankPayees: { id: string; name: string; amount: string; currency: string; nameCheck: string }[]; familyId: string }>("GET", "/catalog"),
    clock: () => req<Clock>("GET", "/clock"),
    /** v1.17: simulated today, registration window, schedule and separate obligations. */
    studyPlan: () => req<StudyPlan>("GET", withLocale("/study-plan")),
    /** v1.17: verified-landlord rent setup (template, lease status, what is missing). */
    rent: () => req<RentSetup>("GET", withLocale("/rent")),
    /** Authenticated PDF read (forms, letters, complaint pack, certificate). */
    async pdf(path: string) {
      const res = await raw("GET", path.replace(/^\/api/, ""));
      if (!res.ok) throw await toError(res);
      return res.blob();
    },
    advanceClock: (b: { days?: number; hours?: number }) => req<{ now: string }>("POST", "/clock/advance", b),
    reset: () => req<{ ok: boolean; registrationStatus: "pending" | "ready"; anchorStatus: "pending"; recovery: "automatic_retry" }>("POST", "/demo/reset"),

    webauthn: {
      registerOptions: () => req<Record<string, unknown>>("POST", "/webauthn/register/options"),
      registerVerify: (credential: unknown) => req<{ ok: boolean }>("POST", "/webauthn/register/verify", { credential }),
      assertOptions: (purpose: "mandate" | "approval" | "freeze" | "cosign", refId: string) =>
        req<Record<string, unknown>>("POST", "/webauthn/assert/options", { purpose, refId }),
      assertVerify: (refId: string, credential: unknown) => req<{ ok: boolean; assertionHash: string }>("POST", "/webauthn/assert/verify", { refId, credential }),
    },

    agent: {
      createThread: () => req<{ threadId: string }>("POST", "/agent/threads"),
      thread: (id: string) => req<Thread>("GET", `/agent/threads/${id}`),
      async *send(id: string, b: { text?: string; documentIds?: string[]; locale: Locale }, opts?: RequestOpts): AsyncGenerator<AgentEvent> {
        const res = await raw("POST", `/agent/threads/${id}/messages`, b, opts);
        if (!res.ok) throw await toError(res);
        for await (const ev of readSSE(res)) {
          if (ev.event === "message" && !(ev.data as { type?: string })?.type) continue;
          yield { ...(ev.data as object), type: ev.event === "message" ? (ev.data as { type: string }).type : ev.event } as AgentEvent;
        }
      },
    },

    documents: {
      upload: (file: File, kind?: string) => {
        const form = new FormData();
        form.append("file", file);
        if (kind) form.append("kind", kind);
        return req<DocumentRecord>("POST", "/documents", undefined, { form });
      },
      get: (id: string) => req<DocumentRecord>("GET", `/documents/${id}`),
      /** Proposed contract addition (GET /documents). */
      list: () => req<DocumentRecord[]>("GET", "/documents"),
    },

    mandates: {
      list: () => req<Mandate[]>("GET", "/mandates"),
      create: (b: MandateCreate) => req<Mandate>("POST", "/mandates", b),
      sign: (id: string, assertion: unknown) => req<Mandate>("POST", `/mandates/${id}/sign`, { assertion }),
      revoke: (id: string) => req<Mandate>("POST", `/mandates/${id}/revoke`),
    },

    approvals: {
      /** r5: `status` may be "all" or a list; the API default stays "pending". */
      list: (status?: Approval["status"] | "all" | Approval["status"][]) =>
        req<Approval[]>("GET", withLocale(`/approvals${status ? `?status=${Array.isArray(status) ? status.join(",") : status}` : ""}`)),
      get: (id: string) => req<Approval>("GET", withLocale(`/approvals/${id}`)),
      approve: (id: string, assertion: unknown) => req<Approval>("POST", `/approvals/${id}/approve`, { assertion }),
      reject: (id: string, reason?: string) => req<Approval>("POST", `/approvals/${id}/reject`, { reason }),
      /** v1.2: the home co-signer signs a scam review (never makes an unverified payee payable). */
      cosign: (id: string, assertion: unknown) => req<Approval>("POST", `/approvals/${id}/cosign`, { assertion }),
      /** v1.13: readable PDF projection of a consent-bound refund form (same family only). */
      async paperwork(id: string, kind: "admission_withdrawal" | "tuition_refund_application") {
        const res = await raw("GET", `/approvals/${id}/paperwork/${kind}`);
        if (!res.ok) throw await toError(res);
        return res.blob();
      },
    },

    payments: {
      list: () => req<Payment[]>("GET", "/payments"),
      get: (id: string) => req<Payment>("GET", `/payments/${id}`),
      cancel: (id: string) => req<Payment>("POST", `/payments/${id}/cancel`),
    },
    refunds: {
      list: () => req<Refund[]>("GET", withLocale("/refunds")),
      get: (id: string) => req<Refund>("GET", withLocale(`/refunds/${id}`)),
    },
    fx: {
      quote: (from: string, to: string, amount: string, side: "send" | "receive" = "send") =>
        req<FxQuoteResponse>("GET", `/fx/quote?from=${from}&to=${to}&amount=${amount}&side=${side}`),
    },

    async *events(opts?: RequestOpts): AsyncGenerator<{ type: string; data: Record<string, unknown> }> {
      const res = await raw("GET", "/events", undefined, opts);
      if (!res.ok) throw await toError(res);
      for await (const ev of readSSE(res)) {
        const d = (ev.data ?? {}) as Record<string, unknown>;
        // Accept `event: type` + payload, and the live API envelope `data: {type, id, data}`.
        const type = ev.event === "message" && typeof d.type === "string" ? d.type : ev.event;
        const inner = d.data && typeof d.data === "object" && (d.type === type || ev.event === "message") ? (d.data as Record<string, unknown>) : d;
        yield { type, data: { ...inner, _eventId: d.id } };
      }
    },

    freeze: (assertion?: unknown) => req<FreezeResult>("POST", "/freeze", { assertion }),
    unfreeze: (assertion: unknown) => req<FreezeResult>("POST", "/unfreeze", { assertion }),

    audit: {
      entries: (after = 0, limit = 500) => req<{ entries: AuditEntry[]; next?: number | null }>("GET", `/audit/entries?after=${after}&limit=${limit}`),
      /** Every entry, following `next` (the API caps a page at 500). */
      async all() {
        const out: AuditEntry[] = [];
        let after = 0;
        for (let i = 0; i < 40; i++) {
          const page = await req<{ entries: AuditEntry[]; next?: number | null }>("GET", `/audit/entries?after=${after}&limit=500`);
          out.push(...page.entries);
          if (page.next === null || page.next === undefined || !page.entries.length) break;
          after = page.next;
        }
        return { entries: out };
      },
      verify: () => req<VerifyResult>("POST", "/audit/verify"),
      tamper: (seq: number) => req<{ ok: boolean }>("POST", "/demo/tamper", { seq }),
      restore: () => req<{ ok: boolean }>("POST", "/demo/restore"),
    },
    chain: {
      status: () => req<ChainStatus>("GET", "/chain/status"),
      anchors: () => req<Anchor[]>("GET", "/chain/anchors"),
    },
    scenarios: {
      list: () => req<Scenario[]>("GET", "/scenarios"),
      async *run(ids?: string[], opts?: RequestOpts): AsyncGenerator<ScenarioEvent> {
        const res = await raw("POST", "/scenarios/run", { ids }, opts);
        if (!res.ok) throw await toError(res);
        for await (const ev of readSSE(res)) yield ev.data as ScenarioEvent;
      },
    },
  };
}

export type Client = ReturnType<typeof createClient>;
