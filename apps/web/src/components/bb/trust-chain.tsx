"use client";

import { Anchor as AnchorIcon, Check, Link2Off, X } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { useTranslations } from "next-intl";
import { RuleId } from "@/components/bb/badges";
import { HashChip } from "@/components/bb/hash";
import { useDraftCopy } from "@/components/bb/trust-copy";
import { cn } from "@/lib/utils";
import type { Anchor, AuditEntry } from "@/lib/api/types";

/** Visual state of one link (entry or anchor checkpoint) on the hash-chain spine. */
export type LinkState = "idle" | "checking" | "ok" | "bad" | "untrusted";

const actorTone: Record<string, string> = {
  agent: "bg-route-soft text-route-ink",
  policy: "bg-attention-soft text-attention-ink",
  parent: "bg-verified-soft text-verified-ink",
  student: "bg-verified-soft text-verified-ink",
  bank: "bg-secondary text-foreground",
  bursar: "bg-secondary text-foreground",
  system: "bg-muted text-muted-foreground",
};

/** Spine segment colour for a link state. */
const lineTone: Record<LinkState, string> = {
  idle: "bg-border",
  checking: "bg-brand",
  ok: "bg-verified",
  bad: "bg-blocked",
  untrusted: "bg-[repeating-linear-gradient(to_bottom,var(--border)_0_4px,transparent_4px_8px)]",
};

/**
 * A short visual fingerprint of a hash: four cells in the brand ink, opacity taken from the hash digits.
 * Two matching fingerprints (this entry's prevHash and the previous entry's hash) make the link visible.
 */
export function HashPrint({ value, tone = "brand", className }: { value: string; tone?: "brand" | "blocked" | "muted"; className?: string }) {
  const hex = value.replace(/^0x/, "").padEnd(8, "0");
  const cells = [0, 2, 4, 6].map((i) => 0.25 + (parseInt(hex.slice(i, i + 2), 16) / 255) * 0.75);
  const bg = tone === "blocked" ? "bg-blocked" : tone === "muted" ? "bg-muted-foreground" : "bg-brand";
  return (
    <span className={cn("inline-flex shrink-0 gap-px overflow-hidden rounded-[3px]", className)} aria-hidden>
      {cells.map((o, i) => (
        <span key={i} className={cn("h-2.5 w-1.5", bg)} style={{ opacity: Number.isFinite(o) ? o : 0.4 }} />
      ))}
    </span>
  );
}

function HashPair({ prev, hash, bad }: { prev: string; hash: string; bad: boolean }) {
  return (
    <span className={cn("inline-flex min-w-0 items-center gap-1.5 font-mono text-[10.5px]", bad ? "text-blocked-ink" : "text-muted-foreground")}>
      <HashPrint value={prev} />
      <span className="truncate">{prev.slice(0, 6)}</span>
      <span aria-hidden className="opacity-60">
        →
      </span>
      <HashPrint value={hash} tone={bad ? "blocked" : "brand"} />
      <span className={cn("truncate", !bad && "text-foreground/80")}>{hash.slice(0, 6)}</span>
    </span>
  );
}

function Node({ state, shape = "circle", seq }: { state: LinkState; shape?: "circle" | "anchor" | "genesis"; seq?: number }) {
  const reduce = useReducedMotion();
  const base =
    shape === "anchor"
      ? "size-7 rotate-45 rounded-[7px]"
      : shape === "genesis"
        ? "size-3 rounded-full"
        : "size-6 rounded-full";
  const tone: Record<LinkState, string> = {
    idle: "border-2 border-border bg-card text-muted-foreground",
    checking: "border-2 border-brand bg-brand-soft text-brand-ink",
    ok: "border-2 border-verified bg-verified text-white",
    bad: "border-2 border-blocked bg-blocked text-white",
    untrusted: "border-2 border-dashed border-border bg-card text-muted-foreground/60",
  };
  const icon =
    state === "ok" ? (
      <Check className="size-3.5" strokeWidth={3} />
    ) : state === "bad" ? (
      <X className="size-3.5" strokeWidth={3} />
    ) : shape === "anchor" ? (
      <AnchorIcon className="size-3.5" />
    ) : null;
  return (
    <motion.span
      className={cn("relative z-10 grid place-items-center transition-colors duration-200", base, tone[state])}
      animate={
        reduce
          ? undefined
          : state === "ok"
            ? { scale: [1, 1.18, 1] }
            : state === "bad"
              ? { x: [0, -5, 5, -3, 3, 0], scale: [1, 1.2, 1] }
              : { scale: 1 }
      }
      transition={{ duration: state === "bad" ? 0.45 : 0.25 }}
      aria-hidden
      data-seq={seq}
    >
      <span className={cn("grid place-items-center", shape === "anchor" && "-rotate-45")}>{icon}</span>
      {state === "checking" && !reduce && <span className="absolute -inset-1 animate-pulse-ring rounded-full bg-brand/30" />}
    </motion.span>
  );
}

/** One vertical gutter column with the spine line and its node. */
function Gutter({ state, nextState, children, last, top = "top-0" }: { state: LinkState; nextState?: LinkState; children: React.ReactNode; last?: boolean; top?: string }) {
  return (
    <div className="relative flex w-11 shrink-0 justify-center">
      {/* upper half: the link coming into this node */}
      <span className={cn("absolute left-1/2 h-[20px] w-0.5 -translate-x-1/2 transition-colors duration-200", top, lineTone[state])} aria-hidden />
      {/* lower half: the link leaving towards the next node */}
      {!last && <span className={cn("absolute top-[20px] bottom-0 left-1/2 w-0.5 -translate-x-1/2 transition-colors duration-200", lineTone[state === "untrusted" ? "untrusted" : (nextState ?? "idle")])} aria-hidden />}
      <div className="relative pt-2">{children}</div>
    </div>
  );
}

export function ChainEntry({
  e,
  state,
  nextState,
  last,
  selected,
  focus,
  time,
  onSelect,
}: {
  e: AuditEntry;
  state: LinkState;
  nextState?: LinkState;
  last?: boolean;
  selected: boolean;
  focus: boolean;
  time: string;
  onSelect: () => void;
}) {
  const t = useTranslations("trust");
  const bad = state === "bad";
  return (
    <li id={`seq-${e.seq}`} className="flex gap-2 pr-3 sm:pr-4">
      <Gutter state={state} nextState={nextState} last={last}>
        <Node state={state} seq={e.seq} />
        {bad && (
          <span className="absolute -top-3 left-1/2 grid size-5 -translate-x-1/2 place-items-center rounded-full bg-card text-blocked" aria-hidden>
            <Link2Off className="size-3.5" />
          </span>
        )}
      </Gutter>
      <motion.button
        type="button"
        onClick={onSelect}
        aria-pressed={selected}
        animate={bad ? { x: [0, -6, 6, -4, 4, 0] } : { x: 0 }}
        transition={{ duration: 0.45 }}
        className={cn(
          "my-0.5 min-w-0 flex-1 rounded-xl border bg-card px-3 py-2 text-left text-sm transition-[background-color,border-color,opacity,box-shadow] duration-200 hover:border-foreground/20",
          selected && !bad && "border-brand/50 ring-2 ring-brand/25",
          focus && !bad && !selected && "ring-2 ring-route/40",
          state === "ok" && !selected && "border-verified/30",
          bad && "border-blocked/60 bg-blocked-soft shadow-lift",
          state === "untrusted" && "opacity-45 saturate-0",
        )}
      >
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <span className="font-mono text-xs font-semibold text-foreground tnum">#{e.seq}</span>
          <span className={cn("rounded-md px-1.5 py-px text-[11px] font-medium", actorTone[e.actor] ?? actorTone.system)}>{e.actor}</span>
          <span className="font-mono text-xs text-muted-foreground">{e.kind}</span>
          <span className="text-xs text-muted-foreground tnum">{time}</span>
          <span className="ml-auto max-sm:w-full">
            <HashPair prev={e.prevHash} hash={e.hash} bad={bad} />
          </span>
        </div>
        <div className="mt-1 flex flex-wrap items-baseline gap-x-2 gap-y-1">
          <p className={cn("leading-snug text-pretty", bad && "font-medium text-blocked-ink")}>{e.summary}</p>
          {e.ruleIds.map((r) => (
            <RuleId key={r} id={r} />
          ))}
          {bad && <span className="text-[11px] font-semibold text-blocked-ink">{t("mismatch")}</span>}
          {state === "ok" && <span className="sr-only">{t("verified")}</span>}
        </div>
      </motion.button>
    </li>
  );
}

export function ChainAnchor({ a, state, nextState, last }: { a: Anchor; state: LinkState; nextState?: LinkState; last?: boolean }) {
  const t = useTranslations("trust");
  const d = useDraftCopy("trust");
  const broken = state === "bad";
  return (
    <li className="flex gap-2 pr-3 sm:pr-4" aria-label={t("anchoredIn", { n: a.blockNumber })}>
      <Gutter state={state} nextState={nextState} last={last}>
        <Node state={state} shape="anchor" />
      </Gutter>
      <div
        className={cn(
          "my-1.5 flex min-w-0 flex-1 flex-wrap items-center gap-x-3 gap-y-1 rounded-xl border border-dashed px-3 py-2 text-xs transition-colors duration-200",
          state === "ok" && "border-verified/40 bg-verified-soft/50",
          broken && "border-blocked/60 bg-blocked-soft",
          state === "untrusted" && "opacity-45 saturate-0",
          (state === "idle" || state === "checking") && "bg-brand-soft/40 border-brand/30",
        )}
      >
        <span className="font-semibold text-foreground">{t("anchoredIn", { n: a.blockNumber })}</span>
        <span className="text-muted-foreground">{t("chain.range", { from: a.firstSeq, to: a.lastSeq })}</span>
        <span className="inline-flex items-center gap-1.5 text-muted-foreground">
          tx <HashChip value={a.txHash} n={4} />
        </span>
        <span className="ml-auto">
          {broken ? (
            <span className="font-semibold text-blocked-ink">{t("chain.mismatch")}</span>
          ) : state === "ok" ? (
            <span className="inline-flex items-center gap-1.5 font-medium text-verified-ink">
              <Check className="size-3.5" strokeWidth={2.5} />
              {d("chain.rootOk", "Root matches")}
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-muted-foreground">
              root <HashChip value={a.root} n={4} />
            </span>
          )}
        </span>
      </div>
    </li>
  );
}

export function ChainGenesis({ state }: { state: LinkState }) {
  const d = useDraftCopy("trust");
  return (
    <li className="flex gap-2 pr-3 sm:pr-4">
      <div className="relative flex w-11 shrink-0 justify-center">
        <span className={cn("absolute top-[22px] bottom-0 left-1/2 w-0.5 -translate-x-1/2 transition-colors", lineTone[state])} aria-hidden />
        <div className="relative pt-4">
          <Node state={state === "checking" ? "checking" : state === "idle" ? "idle" : "ok"} shape="genesis" />
        </div>
      </div>
      <div className="flex min-w-0 flex-1 items-center gap-2 py-3 font-mono text-[11px] text-muted-foreground">
        <span className="font-sans text-xs font-medium text-foreground">{d("chain.genesis", "Genesis")}</span>
        <HashPrint value="00000000" tone="muted" />
        000000…
      </div>
    </li>
  );
}

export function UntrustedBand({ seq }: { seq: number }) {
  const d = useDraftCopy("trust");
  return (
    <motion.li initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="flex gap-2 pr-3 sm:pr-4" role="note">
      <div className="relative flex w-11 shrink-0 justify-center">
        <span className={cn("absolute inset-y-0 left-1/2 w-0.5 -translate-x-1/2", lineTone.untrusted)} aria-hidden />
      </div>
      <div className="my-1 flex flex-1 items-center gap-2 rounded-lg bg-blocked-soft/70 px-3 py-1.5 text-xs font-medium text-pretty text-blocked-ink">
        <Link2Off className="size-3.5 shrink-0" />
        {d("untrusted", "Nothing after #{seq} can be trusted: every later link builds on the changed entry.", { seq })}
      </div>
    </motion.li>
  );
}

export function PendingTail({ n }: { n: number }) {
  const d = useDraftCopy("trust");
  return (
    <li className="flex gap-2 pr-3 sm:pr-4">
      <div className="relative flex w-11 shrink-0 justify-center">
        <span className={cn("absolute top-0 h-4 left-1/2 w-0.5 -translate-x-1/2", lineTone.untrusted)} aria-hidden />
        <div className="relative pt-4">
          <span className="block size-3 rotate-45 rounded-[3px] border-2 border-dashed border-border" aria-hidden />
        </div>
      </div>
      <div className="py-3 text-xs text-muted-foreground">{d("chain.pending", "{n} newest entries wait for the next anchor", { n })}</div>
    </li>
  );
}

