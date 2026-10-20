"use client";

import { Check, ChevronDown, CircleDashed, Play, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Panel } from "@/components/bb/primitives";
import { useDraftCopy } from "@/components/bb/trust-copy";
import type { RunStatus } from "@/components/bb/judge-hero";
import { cn } from "@/lib/utils";
import type { Scenario } from "@/lib/api/types";

export type RowState = { status: RunStatus; expected?: string; actual?: string; ms?: number; auditSeqs?: number[] };

export type GroupId = "flow" | "attack" | "refund" | "control";

const GROUP_COPY: Record<GroupId, { title: string; body: string }> = {
  flow: { title: "Everyday payments", body: "The agent helps within the parent’s mandate and asks when it should." },
  attack: { title: "Scams and attacks", body: "Injected text, fake bank details and social engineering are stopped by rules, not by the model." },
  refund: { title: "Refunds", body: "Money goes back to the original payer, and nobody can redirect it." },
  control: { title: "Parent control and evidence", body: "Cancel, freeze everything, and a log that shows any edit." },
};

export function ScenarioGroup({
  id,
  scenarios,
  rows,
  open,
  onToggle,
  onRun,
  disabled,
}: {
  id: GroupId;
  scenarios: Scenario[];
  rows: Record<string, RowState>;
  open: string | null;
  onToggle: (id: string) => void;
  onRun: (id: string) => void;
  disabled: boolean;
}) {
  const d = useDraftCopy("judge");
  const done = scenarios.filter((s) => rows[s.id]?.status === "pass" || rows[s.id]?.status === "fail");
  const passed = done.filter((s) => rows[s.id]?.status === "pass").length;
  const failed = done.length - passed;
  const complete = done.length === scenarios.length && scenarios.length > 0;
  return (
    <Panel className="overflow-hidden" aria-labelledby={`group-${id}`}>
      <header className="flex items-start justify-between gap-4 border-b px-4 py-3.5 sm:px-5">
        <div className="min-w-0 flex-1">
          <h2 id={`group-${id}`} className="font-display text-xl font-medium tracking-tight">
            {d(`groups.${id}.title`, GROUP_COPY[id].title)}
          </h2>
          <p className="mt-0.5 text-sm text-pretty text-muted-foreground">{d(`groups.${id}.body`, GROUP_COPY[id].body)}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2 pt-1.5">
          <span className="hidden gap-1 sm:flex" aria-hidden>
            {scenarios.map((s) => {
              const st = rows[s.id]?.status;
              return <span key={s.id} className={cn("size-2 rounded-full transition-colors duration-300", st === "pass" ? "bg-verified" : st === "fail" ? "bg-blocked" : st === "running" ? "bg-brand animate-pulse" : "bg-border")} />;
            })}
          </span>
          <span className={cn("font-mono text-xs tnum", complete && !failed ? "text-verified-ink" : failed ? "text-blocked-ink" : "text-muted-foreground")}>
            {passed}/{scenarios.length}
          </span>
        </div>
      </header>
      <ul>
        {scenarios.map((s) => (
          <ScenarioRow key={s.id} s={s} r={rows[s.id]} open={open === s.id} onToggle={() => onToggle(s.id)} onRun={() => onRun(s.id)} disabled={disabled} />
        ))}
      </ul>
    </Panel>
  );
}

function StatusNode({ status }: { status?: RunStatus }) {
  const base = "relative grid size-6 shrink-0 place-items-center rounded-full transition-colors duration-200";
  if (status === "pass")
    return (
      <motion.span initial={{ scale: 0.6 }} animate={{ scale: 1 }} className={cn(base, "bg-verified text-white")}>
        <Check className="size-3.5" strokeWidth={3} />
      </motion.span>
    );
  if (status === "fail")
    return (
      <motion.span initial={{ scale: 0.6 }} animate={{ scale: 1, x: [0, -3, 3, 0] }} className={cn(base, "bg-blocked text-white")}>
        <X className="size-3.5" strokeWidth={3} />
      </motion.span>
    );
  if (status === "running")
    return (
      <span className={cn(base, "border-2 border-brand bg-brand-soft")}>
        <span className="absolute -inset-1 animate-pulse-ring rounded-full bg-brand/30" />
      </span>
    );
  return (
    <span className={cn(base, "text-muted-foreground/50")}>
      <CircleDashed className="size-5" />
    </span>
  );
}

function ScenarioRow({ s, r, open, onToggle, onRun, disabled }: { s: Scenario; r?: RowState; open: boolean; onToggle: () => void; onRun: () => void; disabled: boolean }) {
  const t = useTranslations("judge");
  const status = r?.status;
  return (
    <li className="border-b last:border-b-0">
      <div className={cn("relative flex items-center gap-3 px-4 py-2.5 transition-colors duration-200 sm:px-5", status === "running" && "bg-brand-soft", status === "fail" && "bg-blocked-soft")}>
        {(status === "running" || status === "fail") && <span className={cn("absolute inset-y-0 left-0 w-[3px]", status === "running" ? "bg-brand" : "bg-blocked")} aria-hidden />}
        <AnimatePresence>
          {status === "pass" && (
            <motion.span key="flash" initial={{ opacity: 0.9 }} animate={{ opacity: 0 }} transition={{ duration: 1.1 }} className="pointer-events-none absolute inset-0 bg-verified-soft" aria-hidden />
          )}
        </AnimatePresence>
        <StatusNode status={status} />
        <span className="relative w-9 shrink-0 font-mono text-xs font-semibold tnum">{s.id}</span>
        <div className="relative min-w-0 flex-1">
          <span className={cn("block text-sm leading-snug text-pretty", status === "running" && "shimmer-text font-medium")}>{s.title}</span>
          <div className="mt-1 flex flex-wrap items-center gap-1">
            {s.priority === "P0" && <span className="rounded bg-foreground px-1 py-px text-[10px] leading-[14px] font-semibold text-background">P0</span>}
            {s.tags.map((tag) => (
              <span key={tag} className="rounded-md bg-muted px-1.5 py-px font-mono text-[10.5px] text-muted-foreground">
                {tag}
              </span>
            ))}
          </div>
        </div>
        <span className="relative flex w-[72px] shrink-0 flex-col items-end gap-0.5">
          {status === "pass" ? (
            <span className="text-xs font-semibold text-verified-ink">{t("status.pass")}</span>
          ) : status === "fail" ? (
            <span className="text-xs font-semibold text-blocked-ink">{t("status.fail")}</span>
          ) : status === "running" ? (
            <span className="text-xs font-medium text-brand-ink">{t("status.running")}</span>
          ) : status === "queued" ? (
            <span className="text-xs text-muted-foreground">{t("status.queued")}</span>
          ) : (
            <button
              type="button"
              onClick={onRun}
              disabled={disabled}
              className="-mr-2 inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-foreground disabled:opacity-40"
            >
              <Play className="size-3" /> {t("runOne")}
            </button>
          )}
          {!!r?.ms && <span className="font-mono text-[10.5px] text-muted-foreground tnum">{r.ms} ms</span>}
        </span>
        <button type="button" onClick={onToggle} aria-expanded={open} aria-label={`${t("details")} ${s.id}`} className="relative grid size-8 shrink-0 place-items-center rounded-full hover:bg-accent">
          <ChevronDown className={cn("size-4 text-muted-foreground transition-transform", open && "rotate-180")} />
        </button>
      </div>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden bg-subtle/60">
            <div className="px-4 pt-1 pb-4 pl-[4.75rem] sm:px-5 sm:pl-[5.25rem]">
              <dl className="grid gap-3 pt-2 text-sm md:grid-cols-2">
                <div>
                  <dt className="text-xs font-medium text-muted-foreground">{t("expected")}</dt>
                  <dd className="mt-0.5 text-pretty">{r?.expected ?? "—"}</dd>
                </div>
                <div>
                  <dt className="text-xs font-medium text-muted-foreground">{t("actual")}</dt>
                  <dd className="mt-0.5 font-mono text-xs text-pretty">{r?.actual || "—"}</dd>
                </div>
              </dl>
              {!!r?.auditSeqs?.length && (
                <div className="mt-2 text-xs text-muted-foreground">
                  {t("evidence")}{" "}
                  {r.auditSeqs.map((seq) => (
                    <Link key={seq} href={`/trust?seq=${seq}`} className="mr-2 font-mono hover:text-foreground hover:underline">
                      #{seq}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </li>
  );
}
