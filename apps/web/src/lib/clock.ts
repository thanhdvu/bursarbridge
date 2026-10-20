"use client";

import { useQuery } from "@tanstack/react-query";
import { usePersona } from "@/lib/persona";

/** Both modes use the API's simulated clock, which advances only on command. */
export function useSimClock(tickMs = 1000) {
  const { client } = usePersona();
  const q = useQuery({ queryKey: ["clock"], queryFn: () => client.clock(), refetchInterval: Math.max(10_000, tickMs) });
  return { nowMs: q.data ? Date.parse(q.data.now) : 0, simulated: q.data?.simulated ?? true, ready: !!q.data };
}
