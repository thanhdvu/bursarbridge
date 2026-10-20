"use client";

import { AnimatePresence, motion } from "motion/react";
import { useTranslations } from "next-intl";
import { MockBadge } from "@/components/bb/badges";
import { NumberTicker } from "@/components/bb/ticker";
import { HashPrint } from "@/components/bb/trust-chain";
import { useDraftCopy } from "@/components/bb/trust-copy";
import { shortHash } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ChainStatus } from "@/lib/api/types";

export type Integrity = { kind: "unverified" } | { kind: "checking" } | { kind: "intact" } | { kind: "broken"; seq: number | null };

const fmt = (prefix = "") => (n: number) => prefix + n.toLocaleString("en-US");
const fmtPlain = fmt();
const fmtBlock = fmt("#");

/** The "harbour night" header of the Trust center: network, contracts and the log's vital numbers. */
export function TrustHero({ chain, entries, anchors, integrity, tail }: { chain?: ChainStatus; entries: number; anchors: number; integrity: Integrity; tail: { seq: number; hash: string }[] }) {
  const t = useTranslations("trust");
  const d = useDraftCopy("trust");
  const mock = !!chain && (chain.mock || (!!chain.mode && chain.mode !== "fisco"));
  return (
    <section className="stage-panel stage-scope relative overflow-hidden rounded-3xl shadow-lift">
      {tail.length > 0 && <ChainStrip tail={tail} integrity={integrity} className="absolute top-8 right-8 hidden xl:flex" />}
      <div className="relative px-5 pt-6 pb-5 sm:px-8 sm:pt-8">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="inline-flex h-6 items-center gap-1.5 rounded-full bg-white/10 px-2.5 font-medium">
            <span className="relative inline-flex size-1.5">
              {chain?.connected && <span className="absolute inset-0 animate-pulse-ring rounded-full bg-verified" />}
              <span className={cn("relative inline-flex size-1.5 rounded-full", chain?.connected ? "bg-verified" : "bg-blocked")} />
            </span>
            {chain ? (chain.connected ? t("chain.connected") : t("chain.offline")) : "…"}
          </span>
          <span className="text-muted-foreground">{chain?.network}</span>
          {mock && <MockBadge what="chain" className="border-white/30 text-white/70" />}
        </div>
        <h1 className="mt-4 font-display text-4xl font-medium tracking-tight text-balance sm:text-5xl">{t("title")}</h1>
        <p className="mt-2 max-w-2xl text-pretty text-[15px] leading-relaxed text-muted-foreground">{t("lead")}</p>
      </div>

      <dl className="relative grid grid-cols-3 border-t border-white/10 lg:grid-cols-[1fr_1fr_1fr_1.5fr]">
        <Stat label={t("stats.entries")}>
          <NumberTicker value={entries} animateOnMount format={fmtPlain} />
        </Stat>
        <Stat label={t("stats.anchors")}>
          <NumberTicker value={anchors} animateOnMount format={fmtPlain} />
        </Stat>
        <Stat label={t("stats.block")}>
          <NumberTicker value={chain?.blockNumber ?? 0} animateOnMount format={fmtBlock} />
        </Stat>
        <Stat label={d("hero.integrity", "Integrity")} className="col-span-3 lg:col-span-1">
          <AnimatePresence mode="wait" initial={false}>
            <motion.span
              key={integrity.kind}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.2 }}
              className={cn(
                "inline-block",
                integrity.kind === "intact" && "text-verified",
                integrity.kind === "broken" && "text-[color-mix(in_oklch,var(--blocked)_70%,white)]",
                integrity.kind === "unverified" && "text-muted-foreground",
                integrity.kind === "checking" && "shimmer-text",
              )}
            >
              {integrity.kind === "intact"
                ? d("hero.intact", "Intact")
                : integrity.kind === "broken"
                  ? d("hero.broken", "Broken at #{seq}", { seq: integrity.seq ?? "?" })
                  : integrity.kind === "checking"
                    ? d("hero.checking", "Checking…")
                    : d("hero.unverified", "Not yet verified")}
            </motion.span>
          </AnimatePresence>
        </Stat>
      </dl>

      {chain && chain.contracts.length > 0 && (
        <div className="relative flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-white/10 px-5 py-3 text-xs sm:px-8">
          <span className="font-medium tracking-wide text-muted-foreground uppercase">{d("hero.contracts", "Contracts")}</span>
          {chain.contracts.map((c) => (
            <span key={c.name} className="inline-flex items-center gap-1.5" title={c.address}>
              <span className="text-stage-foreground/85">{c.name}</span>
              <span className="rounded-md bg-white/8 px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground">{shortHash(c.address, 4)}</span>
            </span>
          ))}
        </div>
      )}
    </section>
  );
}

function Stat({ label, children, className }: { label: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("min-w-0 border-white/10 px-4 py-4 sm:px-8 [&:not(:first-child)]:border-l max-lg:[&:nth-child(4)]:border-t max-lg:[&:nth-child(4)]:border-l-0", className)}>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="mt-1 font-display text-[1.75rem] leading-none font-medium tracking-tight tnum sm:text-[2.5rem]">{children}</dd>
    </div>
  );
}

/** The newest links of the real chain, as a small strip of sealed blocks; they take on the verification verdict. */
function ChainStrip({ tail, integrity, className }: { tail: { seq: number; hash: string }[]; integrity: Integrity; className?: string }) {
  const badSeq = integrity.kind === "broken" ? integrity.seq : null;
  return (
    <div className={cn("items-center", className)} aria-hidden>
      <span className="mr-1 font-mono text-[10px] text-muted-foreground">…</span>
      {tail.map((b, i) => {
        const bad = badSeq !== null && b.seq === badSeq;
        const dim = badSeq !== null && b.seq > badSeq;
        const ok = integrity.kind === "intact" || (badSeq !== null && b.seq < badSeq);
        return (
          <div key={b.seq} className="flex items-center">
            {i > 0 && <span className={cn("h-0.5 w-4 transition-colors", bad || dim ? "bg-white/15" : ok ? "bg-verified/70" : "bg-white/25")} />}
            <motion.div
              animate={bad ? { x: [0, -4, 4, -2, 2, 0] } : { x: 0 }}
              transition={{ duration: 0.45 }}
              className={cn(
                "flex flex-col items-start gap-1 rounded-lg border px-2 py-1.5 transition-colors duration-300",
                ok ? "border-verified/60 bg-verified/10" : "border-white/15 bg-white/5",
                bad && "border-[color-mix(in_oklch,var(--blocked)_70%,white)] bg-blocked/25",
                dim && "opacity-40",
              )}
            >
              <span className="font-mono text-[10px] leading-none text-muted-foreground tnum">#{b.seq}</span>
              <HashPrint value={b.hash} tone={bad ? "blocked" : "brand"} />
            </motion.div>
          </div>
        );
      })}
    </div>
  );
}
