"use client";

import { useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useRef, useState } from "react";
import { MockBadge } from "@/components/bb/badges";
import { JudgeHero } from "@/components/bb/judge-hero";
import { ScenarioGroup, type GroupId, type RowState } from "@/components/bb/judge-scenarios";
import { SiteSurface } from "@/components/bb/site";
import { usePersona } from "@/lib/persona";
import { cn } from "@/lib/utils";
import type { Scenario } from "@/lib/api/types";

const ATTACK_IDS = new Set(["T06", "T07", "T09", "T10", "T11", "T12", "T14", "T17", "T19", "T20"]);
const ATTACK_TAGS = ["injection", "taint", "scam", "L-X", "structuring", "sanctions", "privacy", "registry", "out-of-scope"];
const isAttack = (s: { id: string; tags: string[] }) => ATTACK_IDS.has(s.id) || s.tags.some((x) => ATTACK_TAGS.includes(x));

/** What a scenario proves, from its tags: control and refunds first, then attacks, everything else is the everyday flow. */
const GROUP_ORDER: GroupId[] = ["flow", "attack", "refund", "control"];
function groupOf(s: Scenario): GroupId {
  if (s.tags.some((x) => x === "kill-switch" || x === "evidence" || x === "cancel")) return "control";
  if (s.tags.includes("refund")) return "refund";
  if (isAttack(s)) return "attack";
  return "flow";
}

export default function JudgePage() {
  return (
    <SiteSurface>
      <Judge />
    </SiteSurface>
  );
}

function Judge() {
  const t = useTranslations("judge");
  const { client, mode } = usePersona();
  const list = useQuery({ queryKey: ["scenarios"], queryFn: () => client.scenarios.list() });
  const [rows, setRows] = useState<Record<string, RowState>>({});
  const [running, setRunning] = useState(false);
  const [open, setOpen] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "P0" | "attacks">("all");
  const [summary, setSummary] = useState<{ passed: number; failed: number; total: number } | null>(null);
  const ctrl = useRef<AbortController | null>(null);

  const scenarios = (list.data ?? []).filter((s) => (filter === "all" ? true : filter === "P0" ? s.priority === "P0" : isAttack(s)));

  const run = async (ids?: string[]) => {
    const target = ids ?? scenarios.map((s) => s.id);
    setRows(Object.fromEntries(target.map((id) => [id, { status: "queued" }])));
    setSummary(null);
    setRunning(true);
    ctrl.current = new AbortController();
    try {
      for await (const ev of client.scenarios.run(target, { signal: ctrl.current.signal })) {
        if ("summary" in ev) setSummary(ev.summary);
        else setRows((r) => ({ ...r, [ev.id]: { status: ev.status, expected: ev.expected, actual: ev.actual, ms: ev.ms, auditSeqs: ev.auditSeqs } }));
      }
    } catch {
      /* aborted */
    } finally {
      setRunning(false);
    }
  };

  const all = Object.entries(rows);
  const passed = all.filter(([, r]) => r.status === "pass").length;
  const failed = all.filter(([, r]) => r.status === "fail").length;
  const attacks = (list.data ?? []).filter(isAttack);
  const attacksBlocked = attacks.filter((s) => rows[s.id]?.status === "pass").length;
  const msList = all.map(([, r]) => r.ms ?? 0).filter(Boolean);
  const avg = msList.length ? Math.round(msList.reduce((a, b) => a + b, 0) / msList.length) : 0;

  const groups = GROUP_ORDER.map((g) => ({ id: g, items: scenarios.filter((s) => groupOf(s) === g) })).filter((g) => g.items.length);

  return (
    <main className="mx-auto max-w-7xl px-4 pt-6 pb-24 sm:px-6 sm:pt-8">
      <JudgeHero
        mock={mode === "mock"}
        running={running}
        canRun={!!scenarios.length}
        runLabel={t("run", { n: scenarios.length })}
        onRun={() => run()}
        onStop={() => ctrl.current?.abort()}
        hangers={scenarios.map((s) => ({ id: s.id, status: rows[s.id]?.status }))}
        passed={passed}
        failed={failed}
        of={all.length || (list.data?.length ?? 0)}
        attacksBlocked={attacksBlocked}
        attacks={attacks.length}
        avg={avg}
      />

      {mode === "mock" && (
        <div className="mt-4 flex items-start gap-3 rounded-xl border border-dashed border-mock/40 bg-mock-soft/40 px-4 py-3 text-sm text-muted-foreground">
          <MockBadge what="harness" className="mt-0.5" />
          <span className="text-pretty">{t("mockNote")}</span>
        </div>
      )}

      <div className="mt-6 flex flex-wrap items-center gap-2">
        {(["all", "P0", "attacks"] as const).map((f) => (
          <button
            key={f}
            type="button"
            onClick={() => setFilter(f)}
            disabled={running}
            aria-pressed={filter === f}
            className={cn("rounded-full border px-3 py-1.5 text-sm transition-colors disabled:opacity-50", filter === f ? "border-foreground bg-foreground text-background" : "text-muted-foreground hover:bg-accent")}
          >
            {t(`filter.${f}`)}
          </button>
        ))}
        <AnimatePresence>
          {summary && (
            <motion.span
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              className={cn("ml-auto text-sm font-medium", summary.failed ? "text-blocked-ink" : "text-verified-ink")}
              role="status"
            >
              {t("summary", { passed: summary.passed, total: summary.total })}
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Two columns on a laptop: what the agent does for the family, and what it refuses to do. */}
      <div className="mt-4 grid gap-4 lg:grid-cols-2 lg:items-start">
        {[groups.filter((g) => g.id !== "attack"), groups.filter((g) => g.id === "attack")].map((col, i) => (
          <div key={i} className="space-y-4">
            {!list.isLoading &&
              col.map((g) => (
                <ScenarioGroup
                  key={g.id}
                  id={g.id}
                  scenarios={g.items}
                  rows={rows}
                  open={open}
                  onToggle={(id) => setOpen(open === id ? null : id)}
                  onRun={(id) => run([id])}
                  disabled={running}
                />
              ))}
          </div>
        ))}
      </div>

      <p className="mt-4 text-xs text-muted-foreground">
        {t("cli")} <code className="rounded bg-muted px-1.5 py-0.5 font-mono">make judge</code> ·{" "}
        <Link href="/trust" className="underline-offset-4 hover:underline">
          {t("toTrust")}
        </Link>
      </p>
    </main>
  );
}
