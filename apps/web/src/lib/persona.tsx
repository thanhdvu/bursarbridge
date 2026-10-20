"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useContext, useEffect, useMemo, useSyncExternalStore } from "react";
import { apiMode, createClient, serverApiMode, sessionHint, type Client } from "@/lib/api/client";
import type { AppEvent, PersonaId, User } from "@/lib/api/types";

export type Family = "nguyen" | "wang";

const FAMILY_KEY = "bb-family";
const familyListeners = new Set<() => void>();

export function getFamily(): Family {
  if (typeof window === "undefined") return "nguyen";
  try {
    return (localStorage.getItem(FAMILY_KEY) as Family) || "nguyen";
  } catch {
    return "nguyen";
  }
}
export function setFamily(f: Family) {
  try {
    localStorage.setItem(FAMILY_KEY, f);
    // Each family has its own default languages: the Nguyễns read Vietnamese (Linh English), the Wangs Chinese.
    const parent = f === "wang" ? "zh" : "vi";
    const student = f === "wang" ? "zh" : "en";
    document.cookie = `bb-locale-parent=${parent}; path=/; max-age=31536000; samesite=lax`;
    document.cookie = `bb-locale-student=${student}; path=/; max-age=31536000; samesite=lax`;
  } catch {
    /* ignore */
  }
  familyListeners.forEach((l) => l());
}
function subscribeFamily(l: () => void) {
  familyListeners.add(l);
  const onStorage = (e: StorageEvent) => e.key === FAMILY_KEY && l();
  window.addEventListener("storage", onStorage);
  return () => {
    familyListeners.delete(l);
    window.removeEventListener("storage", onStorage);
  };
}
export function useFamily(): Family {
  return useSyncExternalStore(subscribeFamily, getFamily, () => "nguyen");
}

const noopSubscribe = () => () => {};

export function personaFor(role: "parent" | "student" | "judge" | "cosigner", family: Family): PersonaId {
  if (role === "judge") return "judge";
  if (role === "cosigner") return "mother_lan";
  if (family === "wang") return role === "parent" ? "parent_wang" : "student_hao";
  return role === "parent" ? "parent_minh" : "student_linh";
}

interface PersonaCtx {
  persona: PersonaId;
  client: Client;
  user: User | undefined;
  mode: "mock" | "live";
}

const Ctx = createContext<PersonaCtx | null>(null);

type Listener = (e: AppEvent) => void;

export function PersonaProvider({ persona, children, onEvent }: { persona: PersonaId; children: React.ReactNode; onEvent?: Listener }) {
  const client = useMemo(() => createClient(persona), [persona]);
  const qc = useQueryClient();
  const mode = useSyncExternalStore(noopSubscribe, apiMode, serverApiMode);
  const me = useQuery({ queryKey: ["me", persona], queryFn: () => client.me() });
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") (window as unknown as { __bb: unknown }).__bb = { client, qc };
  }, [client, qc]);

  // Notifications: SSE stream; every event refreshes data and is handed to the surface for toasts.
  useEffect(() => {
    // The judge has no family stream in live mode; trust/judge pages refresh by query instead.
    const streamMode = apiMode();
    if (persona === "judge" && streamMode === "live") return;
    const ctrl = new AbortController();
    let stopped = false;
    // The live stream replays history on connect: only toast events newer than the last one seen.
    let seenKey = "";
    let lastSeen = 0;
    let refreshTimer: ReturnType<typeof setTimeout> | undefined;
    // A replay or a bank reversal can contain several related events. Refresh the
    // current view once per burst, rather than cancelling/restarting every query.
    const refreshData = () => {
      if (refreshTimer) return;
      refreshTimer = setTimeout(() => {
        refreshTimer = undefined;
        void qc.invalidateQueries();
      }, 150);
    };
    (async () => {
      let backoff = 1000;
      while (!stopped) {
        const connectedAt = Date.now();
        const key = `bb-seen-${streamMode}-${persona}-${sessionHint(persona)}`;
        if (key !== seenKey) {
          seenKey = key;
          lastSeen = Number(sessionStorage.getItem(seenKey) ?? 0);
        }
        const initTimer = setTimeout(() => sessionStorage.setItem(seenKey + "-init", "1"), 1500);
        try {
          for await (const ev of client.events({ signal: ctrl.signal })) {
            backoff = 1000;
            // A reset can renew the bearer while the stream connects. Read the
            // resulting session before deduplicating this session's event ids.
            const activeKey = `bb-seen-${streamMode}-${persona}-${sessionHint(persona)}`;
            if (activeKey !== seenKey) {
              seenKey = activeKey;
              lastSeen = Number(sessionStorage.getItem(seenKey) ?? 0);
            }
            if (ev.type === "ready") continue;
            const id = Number((ev.data as { _eventId?: number })._eventId ?? 0);
            if (id) {
              if (id <= lastSeen) continue;
              lastSeen = id;
              sessionStorage.setItem(seenKey, String(id));
              refreshData();
              // first connect without memory: swallow the replay burst
              if (Date.now() - connectedAt < 1500 && !sessionStorage.getItem(seenKey + "-init")) continue;
            } else refreshData();
            onEvent?.({ type: ev.type as AppEvent["type"], data: ev.data });
          }
        } catch {
          /* reconnect */
        }
        clearTimeout(initTimer);
        if (stopped) break;
        await new Promise((r) => setTimeout(r, backoff));
        backoff = Math.min(backoff * 2, 15000);
      }
    })();
    return () => {
      stopped = true;
      ctrl.abort();
      clearTimeout(refreshTimer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client]);

  // Mock mode: any state change in another tab or iframe (demo stage) refreshes this one.
  useEffect(() => {
    if (mode !== "mock") return;
    let off: (() => void) | undefined;
    let timer: ReturnType<typeof setTimeout> | undefined;
    if (process.env.NODE_ENV !== "production")
      import("@/mock/server").then((m) => ((window as unknown as { __bbMockFetch: unknown }).__bbMockFetch = m.mockFetch));
    import("@/mock/db").then(({ onSync }) => {
      off = onSync(() => {
        clearTimeout(timer);
        timer = setTimeout(() => qc.invalidateQueries(), 120);
      });
    });
    return () => {
      off?.();
      clearTimeout(timer);
    };
  }, [mode, qc]);

  return <Ctx.Provider value={{ persona, client, user: me.data, mode }}>{children}</Ctx.Provider>;
}

export function usePersona() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("usePersona outside PersonaProvider");
  return ctx;
}

export function useClient() {
  return usePersona().client;
}
