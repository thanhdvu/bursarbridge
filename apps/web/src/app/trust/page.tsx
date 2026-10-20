"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, FlaskConical, Link2, Pencil, RotateCcw, ShieldCheck, X } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useTranslations } from "next-intl";
import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { MockBadge } from "@/components/bb/badges";
import { Panel } from "@/components/bb/primitives";
import { RealVsMocked } from "@/components/bb/real-vs-mocked";
import { SiteSurface } from "@/components/bb/site";
import { ChainAnchor, ChainEntry, ChainGenesis, PendingTail, UntrustedBand, type LinkState } from "@/components/bb/trust-chain";
import { useDraftCopy } from "@/components/bb/trust-copy";
import { TrustHero, type Integrity } from "@/components/bb/trust-hero";
import { useFormat } from "@/lib/format";
import { usePersona } from "@/lib/persona";
import { cn } from "@/lib/utils";
import type { Anchor, AuditEntry, VerifyResult } from "@/lib/api/types";

export default function TrustPage() {
  return (
    <SiteSurface>
      <Trust />
    </SiteSurface>
  );
}

/** The verification walk: a snapshot of the chain at verify time and how far the check has got. */
type Walk = { seqs: number[]; cursor: number; stop: number | null; phase: "fetching" | "walking" | "done" };

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function Trust() {
  const t = useTranslations("trust");
  const d = useDraftCopy("trust");
  const f = useFormat();
  const reduce = useReducedMotion();
  const { client, mode } = usePersona();
  const qc = useQueryClient();
  const [focusSeq, setFocusSeq] = useState<number | null>(null);
  const focusDone = useRef(false);

  const refetchInterval = mode === "live" ? 5000 : false;
  const audit = useQuery({ queryKey: ["audit"], queryFn: () => client.audit.all(), refetchInterval });
  const chain = useQuery({ queryKey: ["chain"], queryFn: () => client.chain.status(), refetchInterval });
  const anchors = useQuery({ queryKey: ["anchors"], queryFn: () => client.chain.anchors(), refetchInterval });

  const [verifying, setVerifying] = useState(false);
  const [verify, setVerify] = useState<VerifyResult | null>(null);
  const [walk, setWalk] = useState<Walk | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [tampered, setTampered] = useState<{ seq: number; before: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const run = useRef(0);
  const listRef = useRef<HTMLOListElement>(null);

  // Oldest first: the chain reads from genesis down, the way verification walks it.
  const chrono = useMemo(() => [...(audit.data?.entries ?? [])].sort((a, b) => a.seq - b.seq), [audit.data]);
  const total = chrono.length;

  // Deep link from the Judge console (/trust?seq=N): select that entry and bring it into view once it has loaded.
  useEffect(() => {
    const seq = Number(new URLSearchParams(window.location.search).get("seq") ?? 0) || null;
    if (!seq || focusDone.current) return;
    const id = setTimeout(() => {
      const el = document.getElementById(`seq-${seq}`);
      setFocusSeq(seq);
      setSelected(seq);
      if (el) {
        focusDone.current = true;
        el.scrollIntoView({ block: "center", behavior: "smooth" });
      }
    }, 400);
    return () => clearTimeout(id);
  }, [total]);

  // Keep the walking cursor in view inside the log (without moving the page).
  useEffect(() => {
    if (!walk || walk.phase !== "walking") return;
    const seq = walk.seqs[Math.min(walk.cursor, walk.seqs.length - 1)];
    const el = document.getElementById(`seq-${seq}`);
    const box = listRef.current;
    if (!el || !box) return;
    if (box.scrollHeight <= box.clientHeight) {
      // Phone: the log is not its own scroller, so follow in the page.
      const r = el.getBoundingClientRect();
      if (r.bottom > window.innerHeight - 24) window.scrollBy({ top: r.bottom - window.innerHeight * 0.6 });
      return;
    }
    const top = el.offsetTop;
    if (top < box.scrollTop || top + el.offsetHeight > box.scrollTop + box.clientHeight) box.scrollTop = top - box.clientHeight / 2;
  }, [walk]);

  const runVerify = async () => {
    const token = ++run.current;
    const seqs = chrono.map((e) => e.seq);
    setVerify(null);
    setVerifying(true);
    setWalk({ seqs, cursor: 0, stop: null, phase: "fetching" });
    // Bring the whole chain into view for the walk (the verdict stays visible in the sticky column).
    const panel = listRef.current?.closest("section");
    if (panel) {
      const top = panel.getBoundingClientRect().top;
      if (top > window.innerHeight * 0.25 || top < 0) window.scrollBy({ top: top - 72, behavior: reduce ? "auto" : "smooth" });
    }
    if (listRef.current) listRef.current.scrollTop = 0;
    try {
      const res = await client.audit.verify();
      if (token !== run.current) return;
      const stopIdx = !res.ok && res.firstBadSeq != null ? seqs.indexOf(res.firstBadSeq) : -1;
      const end = stopIdx >= 0 ? stopIdx : seqs.length;
      if (!reduce && end > 0) {
        // ≈70 ms per link, 0.35–1.4 s in total; long chains advance several links per frame.
        const duration = Math.min(1400, Math.max(350, end * 70));
        const steps = Math.max(1, Math.min(end, Math.round(duration / 45)));
        for (let i = 1; i <= steps; i++) {
          await sleep(duration / steps);
          if (token !== run.current) return;
          setWalk((w) => w && { ...w, phase: "walking", cursor: Math.round((i / steps) * end) });
        }
      }
      setWalk((w) => w && { ...w, cursor: end, stop: stopIdx >= 0 ? stopIdx : null, phase: "done" });
      setVerify(res);
      if (stopIdx >= 0) {
        const el = document.getElementById(`seq-${res.firstBadSeq}`);
        const box = listRef.current;
        if (el && box && box.scrollHeight > box.clientHeight) box.scrollTo({ top: el.offsetTop - box.clientHeight / 4, behavior: reduce ? "auto" : "smooth" });
        else el?.scrollIntoView({ block: "center", behavior: reduce ? "auto" : "smooth" });
      }
    } finally {
      if (token === run.current) setVerifying(false);
    }
  };

  const resetWalk = () => {
    run.current++;
    setVerifying(false);
    setVerify(null);
    setWalk(null);
  };

  const doTamper = async () => {
    // Default target: an entry with a digit (an amount, an account) about two thirds down the chain,
    // so the verification shows trusted links before it and untrusted ones after it.
    const candidates = chrono.filter((e) => /\d/.test(e.summary) && e.kind !== "demo.reset");
    const pool = candidates.length ? candidates : chrono;
    const seq = selected ?? pool[Math.min(pool.length - 1, Math.floor(pool.length * 0.6))]?.seq;
    if (!seq) return;
    setBusy(true);
    const before = audit.data?.entries.find((e) => e.seq === seq)?.summary ?? "";
    await client.audit.tamper(seq);
    setTampered({ seq, before });
    resetWalk();
    await qc.invalidateQueries({ queryKey: ["audit"] });
    setSelected(seq);
    setBusy(false);
  };
  const doRestore = async () => {
    setBusy(true);
    await client.audit.restore();
    setTampered(null);
    resetWalk();
    await qc.invalidateQueries({ queryKey: ["audit"] });
    setBusy(false);
  };
  const tamperedNow = tampered ? audit.data?.entries.find((e) => e.seq === tampered.seq)?.summary : null;

  // ---- link states ----
  const idx = useMemo(() => new Map((walk?.seqs ?? []).map((s, i) => [s, i])), [walk?.seqs]);
  const stopSeq = walk?.phase === "done" && walk.stop !== null ? walk.seqs[walk.stop] : null;

  const entryState = (seq: number): LinkState => {
    if (!walk) return "idle";
    const i = idx.get(seq);
    if (i === undefined) return "idle";
    if (walk.phase === "fetching") return i === 0 ? "checking" : "idle";
    if (walk.phase === "walking") return i < walk.cursor ? "ok" : i === walk.cursor ? "checking" : "idle";
    if (walk.stop === null) return verify?.ok ? "ok" : "idle";
    return i < walk.stop ? "ok" : i === walk.stop ? "bad" : "untrusted";
  };
  const anchorState = (a: Anchor): LinkState => {
    if (!walk || walk.phase === "fetching") return "idle";
    if (walk.phase === "walking") {
      const i = idx.get(a.lastSeq);
      return i !== undefined && i < walk.cursor ? "ok" : "idle";
    }
    if (stopSeq === null) return verify?.ok ? "ok" : "idle";
    if (a.lastSeq < stopSeq) return "ok";
    if (a.firstSeq <= stopSeq) return "bad";
    return "untrusted";
  };

  const anchorByLast = useMemo(() => new Map((anchors.data ?? []).map((a) => [a.lastSeq, a])), [anchors.data]);
  const lastAnchored = Math.max(0, ...(anchors.data ?? []).map((a) => a.lastSeq));
  const pending = chrono.filter((e) => e.seq > lastAnchored).length;

  type Item = { key: string; state: LinkState; render: (next: LinkState | undefined, last: boolean) => React.ReactNode };
  const items: Item[] = [];
  for (const e of chrono as AuditEntry[]) {
    const s = entryState(e.seq);
    items.push({
      key: `e-${e.seq}`,
      state: s,
      render: (next, last) => (
        <ChainEntry
          e={e}
          state={s}
          nextState={next}
          last={last}
          selected={selected === e.seq}
          focus={focusSeq === e.seq}
          time={f.date(e.at, "datetime")}
          onSelect={() => setSelected(e.seq)}
        />
      ),
    });
    if (s === "bad") items.push({ key: `u-${e.seq}`, state: "untrusted", render: () => <UntrustedBand seq={e.seq} /> });
    const a = anchorByLast.get(e.seq);
    if (a) {
      const as = anchorState(a);
      items.push({ key: `a-${a.blockNumber}-${a.lastSeq}`, state: as, render: (next, last) => <ChainAnchor a={a} state={as} nextState={next} last={last} /> });
    }
  }

  const integrity: Integrity = verifying
    ? { kind: "checking" }
    : verify
      ? verify.ok
        ? { kind: "intact" }
        : { kind: "broken", seq: verify.firstBadSeq ?? null }
      : { kind: "unverified" };
  const checked = walk ? Math.min(walk.cursor, walk.seqs.length) : 0;
  const genesisState: LinkState = !walk ? "idle" : walk.phase === "fetching" ? "checking" : "ok";

  return (
    <main className="mx-auto max-w-7xl px-4 pt-6 pb-24 sm:px-6 sm:pt-8">
      <TrustHero chain={chain.data} entries={total} anchors={anchors.data?.length ?? 0} integrity={integrity} tail={chrono.slice(-5)} />

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        {/* The hash chain */}
        <Panel className="min-w-0 overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 border-b px-4 py-3">
            <div className="flex min-w-0 items-center gap-2">
              <Link2 className="size-4 shrink-0 text-muted-foreground" />
              <h2 className="font-semibold">{t("log")}</h2>
              <span className="hidden truncate text-sm text-muted-foreground sm:inline">{d("chainSub", "oldest first; each entry seals the one before")}</span>
            </div>
            {walk && walk.phase !== "done" && (
              <span className="font-mono text-xs text-muted-foreground tnum" aria-live="polite">
                {t("checking", { n: checked, total: walk.seqs.length })}
              </span>
            )}
          </div>
          <ol ref={listRef} className="relative py-2 pl-1 sm:pl-2 lg:max-h-[72vh] lg:overflow-y-auto lg:overscroll-contain" aria-label={t("log")}>
            <ChainGenesis state={genesisState} />
            {items.map((it, i) => (
              <Fragment key={it.key}>{it.render(items[i + 1]?.state, i === items.length - 1 && pending === 0)}</Fragment>
            ))}
            {pending > 0 && total > 0 && <PendingTail n={pending} />}
          </ol>
        </Panel>

        {/* Controls: first on a phone, a sticky column on a laptop */}
        <div className="-order-1 space-y-4 lg:sticky lg:top-20 lg:order-none lg:self-start">
          <Panel className="overflow-hidden">
            <div className="p-4">
              <div className="flex items-center gap-2">
                <ShieldCheck className="size-4" />
                <h2 className="font-semibold">{t("verify.title")}</h2>
              </div>
              <p className="mt-1 text-sm text-pretty text-muted-foreground">{t("verify.body")}</p>
              <Button className="mt-3 h-11 w-full rounded-xl" onClick={runVerify} disabled={verifying || busy || !total}>
                {verifying ? <span className="shimmer-text">{t("verify.running")}</span> : t("verify.cta")}
              </Button>
              {walk && walk.phase !== "done" && (
                <div className="mt-3 h-1 overflow-hidden rounded-full bg-muted">
                  <motion.div className="h-full bg-verified" animate={{ width: `${(checked / Math.max(walk.seqs.length, 1)) * 100}%` }} transition={{ duration: 0.08 }} />
                </div>
              )}
            </div>
            <AnimatePresence>
              {verify && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className={cn("border-t px-4 py-3", verify.ok ? "bg-verified-soft text-verified-ink" : "bg-blocked-soft text-blocked-ink")}
                  role="status"
                >
                  <div className="flex items-center gap-2 font-semibold">
                    {verify.ok ? <Check className="size-4" /> : <X className="size-4" />}
                    {verify.ok ? t("verify.ok") : t("verify.fail", { seq: verify.firstBadSeq ?? "?" })}
                  </div>
                  <p className="mt-1 text-sm text-pretty opacity-90">
                    {verify.ok ? t("verify.okDetail", { entries: verify.entries, anchors: verify.anchors }) : verify.detail}
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </Panel>

          <Panel className="p-4">
            <div className="flex items-center gap-2">
              <FlaskConical className="size-4" />
              <h2 className="font-semibold">{t("tamper.title")}</h2>
              <MockBadge what="generic" className="ml-auto" />
            </div>
            <p className="mt-1 text-sm text-pretty text-muted-foreground">{t("tamper.body")}</p>
            <div className="mt-3 rounded-lg bg-subtle px-3 py-2 text-xs text-muted-foreground">
              {selected ? t("tamper.selected", { seq: selected }) : t("tamper.pick")}
            </div>
            {tampered && tamperedNow && (
              <div className="mt-3 space-y-1 font-mono text-[11px]">
                <div className="rounded-md bg-muted px-2 py-1 line-through decoration-blocked/60">{tampered.before}</div>
                <div className="rounded-md bg-blocked-soft px-2 py-1 text-blocked-ink">{tamperedNow}</div>
              </div>
            )}
            <div className="mt-3 flex gap-2">
              <Button variant="outline" className="h-10 flex-1 rounded-xl" onClick={doTamper} disabled={busy || verifying || !total}>
                <Pencil className="size-4" />
                {t("tamper.cta")}
              </Button>
              <Button variant="ghost" className="h-10 rounded-xl" onClick={doRestore} disabled={busy || verifying || (!tampered && !(verify && !verify.ok))}>
                <RotateCcw className="size-4" />
                {t("tamper.restore")}
              </Button>
            </div>
          </Panel>
        </div>
      </div>

      <section className="mt-12">
        <h2 className="font-display text-2xl font-medium tracking-tight">{t("realVsMocked")}</h2>
        <p className="mt-1 max-w-2xl text-sm text-pretty text-muted-foreground">{t("realVsMockedLead", { mode: mode.toUpperCase() })}</p>
        <RealVsMocked className="mt-4" />
      </section>
    </main>
  );
}
