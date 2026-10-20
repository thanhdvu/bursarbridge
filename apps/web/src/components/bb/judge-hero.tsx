"use client";

import { Play, Square } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { useTranslations } from "next-intl";
import { MockBadge } from "@/components/bb/badges";
import { NumberTicker } from "@/components/bb/ticker";
import { useDraftCopy } from "@/components/bb/trust-copy";
import { cn } from "@/lib/utils";

export type RunStatus = "queued" | "running" | "pass" | "fail";

const fmt = (suffix = "") => (n: number) => `${n.toLocaleString("en-US")}${suffix}`;
const fmtPlain = fmt();
const fmtMs = fmt(" ms");

/**
 * Harbour-night header of the Judge console: run control, the score as display numbers, and one bridge
 * hanger per scenario that ticks as results stream in.
 */
export function JudgeHero({
  mock,
  running,
  canRun,
  runLabel,
  onRun,
  onStop,
  hangers,
  passed,
  failed,
  of,
  attacksBlocked,
  attacks,
  avg,
}: {
  mock: boolean;
  running: boolean;
  canRun: boolean;
  runLabel: string;
  onRun: () => void;
  onStop: () => void;
  hangers: { id: string; status?: RunStatus }[];
  passed: number;
  failed: number;
  of: number;
  attacksBlocked: number;
  attacks: number;
  avg: number;
}) {
  const t = useTranslations("judge");
  const d = useDraftCopy("judge");
  return (
    <section className="stage-panel stage-scope relative overflow-hidden rounded-3xl shadow-lift">
      <div className="relative flex flex-wrap items-end justify-between gap-x-8 gap-y-5 px-5 pt-6 pb-5 sm:px-8 sm:pt-8">
        <div className="min-w-0 max-w-2xl">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
            <span className="font-mono tracking-wide whitespace-nowrap">T01–T{String(hangers.length || 20).padStart(2, "0")}</span>
            <span aria-hidden className="max-sm:hidden">·</span>
            <span className="max-sm:hidden">{d("eyebrow", "Scripted scenarios with expected outcomes")}</span>
            {mock && <MockBadge what="harness" className="border-white/30 text-white/70" />}
          </div>
          <h1 className="mt-3 font-display text-4xl font-medium tracking-tight text-balance sm:text-5xl">{t("title")}</h1>
          <p className="mt-2 text-pretty text-[15px] leading-relaxed text-muted-foreground">{t("lead")}</p>
        </div>
        {running ? (
          <button
            type="button"
            onClick={onStop}
            className="inline-flex h-11 items-center gap-2 rounded-xl border border-white/25 px-5 text-sm font-medium transition-colors hover:bg-white/10"
          >
            <Square className="size-4" /> {t("stop")}
          </button>
        ) : (
          <button
            type="button"
            onClick={onRun}
            disabled={!canRun}
            className="inline-flex h-11 items-center gap-2 rounded-xl bg-stage-foreground px-5 text-sm font-semibold text-stage shadow-card transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            <Play className="size-4 fill-current" /> {runLabel}
          </button>
        )}
      </div>

      <Hangers items={hangers} />

      <dl className="relative grid grid-cols-2 border-t border-white/10 md:grid-cols-4">
        <Stat label={t("score.passed")} tone={failed ? undefined : passed ? "verified" : undefined} of={of}>
          <NumberTicker value={passed} format={fmtPlain} duration={0.4} />
        </Stat>
        <Stat label={t("score.failed")} tone={failed ? "blocked" : undefined}>
          <NumberTicker value={failed} format={fmtPlain} duration={0.4} />
        </Stat>
        <Stat label={t("score.attacks")} tone={attacksBlocked ? "verified" : undefined} of={attacks}>
          <NumberTicker value={attacksBlocked} format={fmtPlain} duration={0.4} />
        </Stat>
        <Stat label={t("score.avg")}>
          <NumberTicker value={avg} format={fmtMs} duration={0.4} />
        </Stat>
      </dl>
    </section>
  );
}

function Stat({ label, children, of, tone }: { label: string; children: React.ReactNode; of?: number; tone?: "verified" | "blocked" }) {
  return (
    <div className="min-w-0 border-white/10 px-5 py-4 sm:px-8 [&:not(:first-child)]:border-l max-md:[&:nth-child(3)]:border-l-0 max-md:[&:nth-child(n+3)]:border-t">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd
        className={cn(
          "mt-1 font-display text-[1.75rem] leading-none font-medium tracking-tight tnum transition-colors sm:text-[2.5rem]",
          tone === "verified" && "text-verified",
          tone === "blocked" && "text-[color-mix(in_oklch,var(--blocked)_70%,white)]",
        )}
      >
        {children}
        {of !== undefined && <span className="ml-0.5 text-lg text-muted-foreground sm:text-xl">/{of}</span>}
      </dd>
    </div>
  );
}

/** One hanger per scenario; their tops trace the sag of a suspension cable over the deck. */
function Hangers({ items }: { items: { id: string; status?: RunStatus }[] }) {
  const reduce = useReducedMotion();
  const n = items.length;
  if (!n) return <div className="h-20" />;
  const mid = (n - 1) / 2;
  return (
    <div className="relative px-5 pb-4 sm:px-8" aria-hidden>
      <div className="flex h-12 items-end gap-1 sm:gap-1.5">
        {items.map((it, i) => {
          const k = mid ? (i - mid) / mid : 0;
          const h = 22 + 78 * k * k; // % of the row height
          const s = it.status;
          return (
            <div key={it.id} className="flex h-full min-w-0 flex-1 flex-col items-center justify-end" title={it.id}>
              <motion.span
                className={cn(
                  "block w-full max-w-2.5 rounded-t-full transition-colors duration-300",
                  s === "pass" ? "bg-verified" : s === "fail" ? "bg-[color-mix(in_oklch,var(--blocked)_75%,white)]" : s === "running" ? "bg-brand" : "bg-white/18",
                )}
                style={{ height: `${h}%` }}
                animate={s === "running" && !reduce ? { opacity: [1, 0.45, 1] } : s === "pass" && !reduce ? { scaleY: [0.85, 1.06, 1], opacity: 1 } : { opacity: 1 }}
                transition={s === "running" ? { duration: 0.9, repeat: Infinity } : { duration: 0.35 }}
              />
            </div>
          );
        })}
      </div>
      <div className="h-0.5 rounded-full bg-white/25" />
      <div className="mt-1.5 hidden gap-1 sm:flex sm:gap-1.5">
        {items.map((it) => (
          <span key={it.id} className={cn("min-w-0 flex-1 text-center font-mono text-[9.5px] text-muted-foreground/80", it.status === "fail" && "text-white")}>
            {it.id.replace(/^T/, "")}
          </span>
        ))}
      </div>
    </div>
  );
}
