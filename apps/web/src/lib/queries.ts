"use client";

import { useQuery } from "@tanstack/react-query";
import { usePersona } from "@/lib/persona";
import { apiMode } from "@/lib/api/client";

export function useApprovals(status?: "pending" | "all") {
  const { client, persona } = usePersona();
  return useQuery({ queryKey: ["approvals", persona, status ?? "all"], queryFn: () => client.approvals.list(status) });
}
export function usePayments() {
  const { client, persona } = usePersona();
  return useQuery({ queryKey: ["payments", persona], queryFn: () => client.payments.list() });
}
export function usePayment(id: string) {
  const { client, persona } = usePersona();
  return useQuery({ queryKey: ["payment", persona, id], queryFn: () => client.payments.get(id) });
}
export function useRefunds() {
  const { client, persona } = usePersona();
  return useQuery({ queryKey: ["refunds", persona], queryFn: () => client.refunds.list() });
}
export function useMandates() {
  const { client, persona } = usePersona();
  return useQuery({ queryKey: ["mandates", persona], queryFn: () => client.mandates.list() });
}
export function useMe() {
  const { client, persona } = usePersona();
  return useQuery({ queryKey: ["me", persona], queryFn: () => client.me() });
}
export function useAudit() {
  const { client, persona, mode } = usePersona();
  // Live audit evidence is judge-only. Keep its cache separate from family
  // history; a judge visit must never fill a parent's disabled audit query.
  return useQuery({
    queryKey: ["audit", persona, mode],
    // During hydration the context can still hold the server's default mode.
    // Check the actual transport before requesting this privileged endpoint.
    queryFn: () => apiMode() === "live" && persona !== "judge" ? Promise.resolve({ entries: [] }) : client.audit.all(),
    enabled: mode === "mock" || persona === "judge",
  });
}
