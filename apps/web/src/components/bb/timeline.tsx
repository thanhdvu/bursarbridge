"use client";

import { Bot, Building2, GraduationCap, Landmark, Settings2, UserRound } from "lucide-react";
import { motion } from "motion/react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import type { TimelineEvent } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { cn } from "@/lib/utils";

const actorIcon = { agent: Bot, parent: UserRound, student: GraduationCap, bank: Landmark, bursar: Building2, system: Settings2 } as const;

export function Timeline({ events, className }: { events: TimelineEvent[]; className?: string }) {
  const t = useTranslations("timeline");
  const f = useFormat();
  const sorted = [...events].sort((a, b) => a.at.localeCompare(b.at));
  return (
    <ol className={cn("relative", className)}>
      {sorted.map((e, i) => {
        const Icon = actorIcon[e.actor] ?? Settings2;
        const code = e.code.toUpperCase();
        const last = i === sorted.length - 1;
        return (
          <motion.li key={`${e.code}-${e.at}-${i}`} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }} className="relative flex gap-3 pb-4 last:pb-0">
            {!last && <span className="absolute top-8 bottom-0 left-[15px] w-px bg-border" aria-hidden />}
            <span className={cn("relative grid size-8 shrink-0 place-items-center rounded-full border bg-card", last && "border-foreground/30")}>
              <Icon className="size-4 text-muted-foreground" />
            </span>
            <div className="min-w-0 flex-1 pt-1">
              <div className="text-sm font-medium">{t.has(code as never) ? t(code as never) : e.code.replaceAll("_", " ").toLowerCase()}</div>
              <div className="mt-0.5 flex flex-wrap items-center gap-x-2 text-xs text-muted-foreground">
                <span className="tnum">{f.date(e.at, "datetime")}</span>
                <span>· {t.has(`actor.${e.actor}` as never) ? t(`actor.${e.actor}` as never) : e.actor}</span>
                {e.auditSeq > 0 && (
                  <Link href={`/trust?seq=${e.auditSeq}`} className="font-mono text-[11px] hover:text-foreground hover:underline">
                    #{e.auditSeq}
                  </Link>
                )}
              </div>
            </div>
          </motion.li>
        );
      })}
    </ol>
  );
}
