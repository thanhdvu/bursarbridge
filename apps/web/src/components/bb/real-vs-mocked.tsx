"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { apiBaseUrl } from "@/lib/api/client";
import { usePersona } from "@/lib/persona";
import { cn } from "@/lib/utils";
import { Pill } from "./badges";

type Kind = "real" | "mock" | "sim" | "browser" | "local" | "scripted";

interface Health {
  chainMode?: "fisco" | "local" | string;
  llmProvider?: string;
  screeningMode?: string;
}

/** Live API run modes (GET /health, no auth). Labels must follow what this run actually uses. */
export function useHealth(enabled: boolean) {
  return useQuery({
    queryKey: ["health"],
    enabled,
    queryFn: async () => (await (await fetch(`${apiBaseUrl}/health`)).json()) as Health,
    staleTime: 30_000,
  });
}

/** Honest inventory of what is real and what is simulated, by API mode. */
export function RealVsMocked({ className }: { className?: string }) {
  const t = useTranslations("rvm");
  const { mode } = usePersona();
  const live = mode === "live";
  const health = useHealth(live).data;
  // Until health answers, say nothing stronger than "in-browser"/unknown: never claim Real by default.
  const chain: Kind = !live ? "browser" : health?.chainMode === "fisco" ? "real" : health ? "local" : "sim";
  const agent: Kind = !live ? "browser" : health?.llmProvider && health.llmProvider !== "scripted" ? "real" : "scripted";
  const rows: { key: string; kind: Kind; note?: string }[] = [
    { key: "policy", kind: live ? "real" : "browser" },
    { key: "audit", kind: "real" },
    { key: "anchor", kind: chain, note: chain === "local" ? "anchorLocal" : undefined },
    { key: "passkey", kind: "real" },
    { key: "credential", kind: live ? "real" : "browser" },
    { key: "agent", kind: agent, note: agent === "scripted" ? "agentScripted" : undefined },
    ...(live && health?.screeningMode
      ? [{ key: "screening", kind: (health.screeningMode === "synthetic" ? "sim" : "real") as Kind, note: health.screeningMode === "synthetic" ? "screeningSynthetic" : undefined }]
      : []),
    { key: "bank", kind: "mock" },
    { key: "bursar", kind: "mock" },
    { key: "fx", kind: "mock" },
    { key: "clock", kind: "sim" },
    { key: "letters", kind: "sim" },
    { key: "orgs", kind: "sim" },
  ];
  const tone = { real: "verified", mock: "mock", sim: "attention", browser: "route", local: "attention", scripted: "attention" } as const;
  return (
    <div className={cn("overflow-hidden rounded-2xl border bg-card", className)}>
      <table className="w-full text-sm">
        <thead className="bg-subtle text-left text-xs text-muted-foreground">
          <tr>
            <th className="px-4 py-2.5 font-medium">{t("component")}</th>
            <th className="px-4 py-2.5 font-medium">{t("status")}</th>
            <th className="hidden px-4 py-2.5 font-medium md:table-cell">{t("notes")}</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {rows.map((r) => (
            <tr key={r.key} className="align-top">
              <td className="px-4 py-3 font-medium">
                {t(`rows.${r.key}.name` as never)}
                <div className="mt-0.5 text-xs font-normal text-muted-foreground md:hidden">{t(`${r.note ? `runNotes.${r.note}` : `rows.${r.key}.note`}` as never)}</div>
              </td>
              <td className="px-4 py-3">
                <Pill tone={tone[r.kind]}>{t(`kind.${r.kind}`)}</Pill>
              </td>
              <td className="hidden px-4 py-3 text-pretty text-muted-foreground md:table-cell">{t(`${r.note ? `runNotes.${r.note}` : `rows.${r.key}.note`}` as never)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
