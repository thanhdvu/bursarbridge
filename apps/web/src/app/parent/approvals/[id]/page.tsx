"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDown, Check, ChevronDown, Code2, FileText, Hourglass, Info, ShieldCheck, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ApproveSheet, Breakdown, PackList, PayeeChecks, RefundClaimCard, useApproval } from "@/components/bb/cards";
import { AdmissionNotice } from "@/components/bb/study-progress";
import { FrozenBanner } from "@/components/bb/frozen-banner";
import { EscalationLetterCard } from "@/components/bb/plan";
import { HashChip } from "@/components/bb/hash";
import { MoneyPath } from "@/components/bb/money-path";
import { CheckRow, Line, Panel, ReasonList, SectionLabel } from "@/components/bb/primitives";
import { AppHeader, DemoToday } from "@/components/bb/shell";
import { useSimClock } from "@/lib/clock";
import { localTerm, plainName, useFormat } from "@/lib/format";
import { usePersona } from "@/lib/persona";
import { paymentPath } from "@/lib/status";
import { cn } from "@/lib/utils";
import { costVsMid } from "@/lib/fx";
import type { Approval } from "@/lib/api/types";

export default function ApprovalPage() {
  const { id } = useParams<{ id: string }>();
  const t = useTranslations("approval");
  const tf = useTranslations("freeze");
  const { user } = usePersona();
  const q = useApproval(id);
  const router = useRouter();
  const a = q.data;

  return (
    <>
      <AppHeader
        left={
          <button type="button" onClick={() => router.push("/parent")} aria-label={t("close")} className="-ml-2 grid size-9 place-items-center rounded-full hover:bg-accent">
            <X className="size-5" />
          </button>
        }
        right={a?.status === "pending" ? <ExpiresIn approval={a} /> : null}
        className="border-b border-transparent"
      />
      {!a ? (
        <div className="space-y-4 p-4">
          <div className="h-48 animate-pulse rounded-2xl bg-muted" />
          <div className="h-32 animate-pulse rounded-2xl bg-muted" />
        </div>
      ) : a.rejectionReason === "VISA_REFUSED_BEFORE_PAYMENT" ? <main className="p-4"><AdmissionNotice /></main> : a.action === "refund_claim" || a.action === "escalation_letter" ? (
        <main className="flex-1 space-y-4 px-4 pt-2 pb-8">
          {a.action === "refund_claim" ? <RefundClaimCard approval={a} /> : <EscalationLetterCard approval={a} />}
        </main>
      ) : user?.frozen && a.status === "pending" ? (
        <main className="space-y-3 p-4"><FrozenBanner /><p className="text-sm text-muted-foreground">{tf("approvalPaused")}</p></main>
      ) : a.status === "pending" && a.disclosure ? (
        <PendingApproval a={a} />
      ) : a.status === "pending" ? (
        <GenericApproval a={a} />
      ) : (
        <DecidedApproval a={a} />
      )}
    </>
  );
}

function ExpiresIn({ approval }: { approval: Approval }) {
  const t = useTranslations("approval");
  const { nowMs } = useSimClock(30_000);
  const ms = Math.max(0, Date.parse(approval.expiresAt) - nowMs);
  const hours = Math.round(ms / 3600_000);
  return (
    <span className={cn("inline-flex items-center gap-1 text-xs", ms < 15 * 60_000 ? "text-attention-ink" : "text-muted-foreground")}>
      <Hourglass className="size-3.5" />
      {ms < 3600_000 ? t("expiresMin", { m: Math.ceil(ms / 60_000) }) : t("expires", { h: hours })}
    </span>
  );
}

function PendingApproval({ a }: { a: Approval }) {
  const t = useTranslations("approval");
  const f = useFormat();
  const { client } = usePersona();
  const qc = useQueryClient();
  const [sheet, setSheet] = useState(false);
  const [raw, setRaw] = useState(false);
  const [lines, setLines] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const { user } = usePersona();
  const d = a.disclosure!;
  const { total, rate } = costVsMid(d);
  const payeeOk = a.payee?.credential.status === "valid" && a.payee.account.hashMatch && a.payee.nameCheck === "match";
  const packReady = a.pack ? a.pack.documents.every((x) => x.status === "ready") : false;
  const first = a.action === "first_payment";

  return (
    <>
      <main className="flex-1 space-y-6 px-4 pb-8">
        {/* Hero: the exact action, on the bridge it will cross */}
        <motion.section
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
          className="stage-panel stage-scope -mx-1 overflow-hidden rounded-3xl p-5 shadow-lift"
        >
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm text-muted-foreground">{a.invoice ? t("forInvoice", { term: localTerm(a.invoice.term, f.locale) }) : t("title")}</span>
            {first && <span className="rounded-full bg-white/10 px-2 py-0.5 text-xs font-medium text-[oklch(0.88_0.1_85)] ring-1 ring-white/15">{t("firstPayment")}</span>}
          </div>
          <div className="mt-4 text-sm text-muted-foreground">{t("youPay")}</div>
          <div className="mt-1 font-display text-[44px] leading-none font-medium tracking-tight tnum">{f.money(total, d.send.currency)}</div>
          <div className="mt-1.5 text-xs text-muted-foreground">
            {t("fromAccount", { account: (a.rawAction as { payer?: { masked?: string } }).payer?.masked ?? user?.accounts[0]?.maskedNumber ?? "" })}
          </div>
          <MoneyPath
            className="mt-3"
            state="waiting"
            from={{ place: "Đà Nẵng", sub: "Lotus Home Bank" }}
            to={{ place: "Seoul", sub: plainName(a.payee?.institution) }}
          />
          <div className="mt-4 flex items-end justify-between gap-3 border-t border-white/10 pt-4">
            <div className="min-w-0">
              <div className="text-sm text-muted-foreground">{t("theyGet", { payee: plainName(a.payee?.institution) })}</div>
              <div className="mt-1 font-display text-[28px] leading-none font-medium tracking-tight tnum">{f.money(d.receive)}</div>
            </div>
            <span className="inline-flex shrink-0 items-center gap-1.5 text-xs text-muted-foreground">
              <ArrowDown className="size-3.5 -rotate-90" />
              {t("rateLine", { rate: f.number(rate, 2), cur: f.parts(d.send).symbol })}
            </span>
          </div>
        </motion.section>

        {/* Three answers at a glance */}
        <Panel className="divide-y p-0">
          {[
            { ok: payeeOk, title: t("glance.payee", { payee: plainName(a.payee?.institution) }), sub: t("glance.payeeSub"), href: "#payee" },
            { ok: true, title: t("glance.cost", { rate: f.number(rate, 2), fee: f.money(d.fees) }), sub: t("glance.costSub", { total: f.money(total, d.send.currency), receive: f.money(d.receive) }), href: "#cost" },
            { ok: packReady, title: t("glance.pack"), sub: t("glance.packSub"), href: "#pack" },
            { ok: true, title: t("glance.cancel"), sub: t("glance.cancelSub"), href: "#cost" },
          ].map((g) => (
            <a key={g.title} href={g.href} className="flex items-center gap-3 px-4 py-3 hover:bg-accent/40">
              <span className={cn("grid size-6 place-items-center rounded-full", g.ok ? "bg-verified text-white" : "bg-attention-soft text-attention-ink")}>
                {g.ok ? <Check className="size-3.5" strokeWidth={3} /> : <Info className="size-3.5" />}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-medium">{g.title}</span>
                <span className="block text-xs text-muted-foreground">{g.sub}</span>
              </span>
            </a>
          ))}
        </Panel>

        {/* Why you are asked */}
        <section>
          <SectionLabel>{t("why")}</SectionLabel>
          <Panel className="p-4">
            <p className="text-sm leading-relaxed text-pretty">{first ? t("whyFirst", { payee: plainName(a.payee?.institution) }) : t("whyGeneric")}</p>
            <ReasonList reasons={a.risk.features} className="mt-2" />
            {!a.cooling?.cosignRequired && <p className="mt-2 text-xs text-muted-foreground">{t("noCosign")}</p>}
          </Panel>
        </section>

        <section id="cost" className="scroll-mt-16">
          <SectionLabel>{t("breakdown")}</SectionLabel>
          <Panel className="p-4">
            <Breakdown d={d} />
          </Panel>
        </section>

        {a.payee && (
          <section id="payee" className="scroll-mt-16">
            <SectionLabel>{t("payee")}</SectionLabel>
            <Panel className="p-4">
              <PayeeChecks payee={a.payee} />
            </Panel>
          </section>
        )}

        {a.invoice && (
          <section>
            <SectionLabel>{t("invoice")}</SectionLabel>
            <Panel className="p-4">
              <button type="button" onClick={() => setLines(!lines)} className="flex w-full items-center gap-3 text-left" aria-expanded={lines}>
                <span className="grid size-10 place-items-center rounded-xl bg-secondary">
                  <FileText className="size-5" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block font-medium">{a.invoice.ref}</span>
                  <span className="block text-xs text-muted-foreground">{t("due", { date: f.date(a.invoice.dueDate) })}</span>
                  <DemoToday className="-ml-1" />
                </span>
                <ChevronDown className={cn("size-4 text-muted-foreground transition-transform", lines && "rotate-180")} />
              </button>
              <AnimatePresence initial={false}>
                {lines && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                    <div className="mt-3 border-t pt-2">
                      {a.invoice.lines.map((l) => (
                        <Line key={l.label} label={l.label} value={f.money(l.amount)} muted />
                      ))}
                      <Line label={t("total")} value={f.money(a.invoice.total)} strong className="border-t pt-2" />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </Panel>
          </section>
        )}

        {a.pack && (
          <section id="pack" className="scroll-mt-16">
            <SectionLabel>{t("pack")}</SectionLabel>
            <Panel className="p-4">
              <PackList pack={a.pack} />
            </Panel>
          </section>
        )}

        <section>
          <button type="button" onClick={() => setRaw(!raw)} className="flex items-center gap-2 px-1 text-sm font-medium text-muted-foreground hover:text-foreground" aria-expanded={raw}>
            <Code2 className="size-4" />
            {t("raw")}
            <ChevronDown className={cn("size-4 transition-transform", raw && "rotate-180")} />
          </button>
          <AnimatePresence initial={false}>
            {raw && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                <Panel className="mt-2 p-4">
                  <p className="text-xs text-muted-foreground">{t("rawHint")}</p>
                  <div className="mt-2 flex items-center gap-2 text-xs">
                    <span className="text-muted-foreground">{t("consentHash")}</span>
                    <HashChip value={a.consentHash} n={10} />
                  </div>
                </Panel>
              </motion.div>
            )}
          </AnimatePresence>
        </section>
      </main>

      {/* Decision */}
      <div className="sticky bottom-0 z-30 border-t bg-background/92 px-4 pt-3 pb-safe backdrop-blur">
        <Button size="lg" className="h-13 w-full rounded-2xl text-base" onClick={() => setSheet(true)}>
          <ShieldCheck className="size-5" />
          {t("approve")}
        </Button>
        <div className="mt-2 flex items-center justify-between gap-3">
          <p className="text-[11px] leading-snug text-muted-foreground">{t("approveHint")}</p>
          <Button
            variant="ghost"
            size="sm"
            className="shrink-0 text-blocked hover:bg-blocked-soft hover:text-blocked"
            disabled={rejecting}
            onClick={async () => {
              if (!confirm(t("rejectConfirm"))) return;
              setRejecting(true);
              try {
                await client.approvals.reject(a.id, "parent_declined");
                qc.invalidateQueries();
                toast(t("rejected"));
              } finally {
                setRejecting(false);
              }
            }}
          >
            {t("reject")}
          </Button>
        </div>
      </div>
      <ApproveSheet approval={a} open={sheet} onOpenChange={setSheet} onDone={() => qc.invalidateQueries()} />
    </>
  );
}

/** Approvals without a money disclosure (e.g. a mandate change): show the reasons and the exact action. */
function GenericApproval({ a }: { a: Approval }) {
  const t = useTranslations("approval");
  const ta = useTranslations("cards.approval");
  const [sheet, setSheet] = useState(false);
  const qc = useQueryClient();
  return (
    <>
      <main className="flex-1 space-y-5 px-4 pb-8">
        <h1 className="px-1 text-2xl font-semibold tracking-tight">{ta(`title.${a.action}` as never)}</h1>
        <Panel className="p-4">
          <ReasonList reasons={a.risk.features} />
        </Panel>
        <Panel className="p-4">
          <p className="text-xs text-muted-foreground">{t("rawHint")}</p>
          <div className="mt-2 flex items-center gap-2 text-xs">
            <span className="text-muted-foreground">{t("consentHash")}</span>
            <HashChip value={a.consentHash} n={10} />
          </div>
        </Panel>
      </main>
      <div className="sticky bottom-0 z-30 border-t bg-background/92 px-4 pt-3 pb-safe backdrop-blur">
        <Button size="lg" className="h-13 w-full rounded-2xl text-base" onClick={() => setSheet(true)}>
          <ShieldCheck className="size-5" />
          {t("approve")}
        </Button>
      </div>
      <ApproveSheet approval={a} open={sheet} onOpenChange={setSheet} onDone={() => qc.invalidateQueries()} />
    </>
  );
}

function DecidedApproval({ a }: { a: Approval }) {
  const t = useTranslations("approval");
  const tp = useTranslations("payment");
  const f = useFormat();
  const { client, persona } = usePersona();
  const qc = useQueryClient();
  const { nowMs } = useSimClock();
  // The resulting payment: by resultRef when the API gives one, otherwise the payment that carries this approval id.
  const pay = useQuery({
    queryKey: ["payment-for-approval", persona, a.id],
    queryFn: async () => (a.resultRef ? client.payments.get(a.resultRef) : (await client.payments.list()).find((x) => x.approvalId === a.id) ?? null),
    enabled: a.action !== "refund_claim" && a.status === "approved",
    refetchInterval: 1500,
  });
  const p = pay.data;
  const approved = a.status === "approved";
  const cancelUntil = p?.cancelUntil ?? a.disclosure?.cancelUntil;
  const canCancel = p && cancelUntil && nowMs < Date.parse(cancelUntil) && !["cancelled", "failed"].includes(p.status);
  const mins = cancelUntil ? Math.max(0, Math.ceil((Date.parse(cancelUntil) - nowMs) / 60_000)) : 0;

  return (
    <main className="flex-1 px-4 pb-10">
      <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="flex flex-col items-center pt-6 text-center">
        <motion.span
          initial={{ scale: 0.5 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 300, damping: 14 }}
          className={cn("grid size-16 place-items-center rounded-full text-white", approved ? "bg-verified" : "bg-muted-foreground")}
        >
          {approved ? <Check className="size-8" strokeWidth={2.5} /> : <X className="size-8" />}
        </motion.span>
        <h1 className="mt-4 text-2xl font-semibold tracking-tight">{approved ? t("done.title") : t(`done.${a.status}` as never)}</h1>
        {approved && p && <p className="mt-1 text-sm text-muted-foreground">{tp(`statusLong.${p.status}`)}</p>}
      </motion.div>

      {p && (
        <Panel className="mt-6 p-4">
          <MoneyPath state={paymentPath(p)} from={{ place: "Đà Nẵng", sub: "Lotus Home Bank" }} to={{ place: "Seoul", sub: plainName(p.payee.institution) }} />
          <div className="mt-4 space-y-0.5">
            {(["executing", "sent", "received_by_bursar", "matched"] as const).map((s, i, arr) => {
              const idx = arr.indexOf(p.status as (typeof arr)[number]);
              const state = p.status === "cancelled" ? "pending" : idx >= i ? "ok" : idx + 1 === i ? "running" : "pending";
              return <CheckRow key={s} state={state} title={tp(`step.${s}`)} className="py-1.5" />;
            })}
          </div>
          <div className="mt-3 border-t pt-3">
            <Line label={t("youPay")} value={f.money(p.send)} />
            <Line label={t("theyGet", { payee: plainName(p.payee.institution) })} value={f.money(p.receive)} />
          </div>
        </Panel>
      )}

      <div className="mt-5 space-y-2">
        {canCancel && (
          <Button
            variant="outline"
            size="lg"
            className="h-12 w-full rounded-xl"
            onClick={async () => {
              if (!confirm(t("cancelConfirm"))) return;
              await client.payments.cancel(p!.id);
              qc.invalidateQueries();
            }}
          >
            {t("cancelFree", { m: mins })}
          </Button>
        )}
        {p && (
          <Button asChild variant="ghost" size="lg" className="h-12 w-full rounded-xl">
            <Link href={`/parent/payments/${p.id}`}>{t("viewPayment")}</Link>
          </Button>
        )}
        <Button asChild variant={p ? "ghost" : "default"} size="lg" className="h-12 w-full rounded-xl">
          <Link href="/parent">{t("backHome")}</Link>
        </Button>
      </div>
    </main>
  );
}
