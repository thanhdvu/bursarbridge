"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowRight,
  Building2,
  CalendarClock,
  Check,
  ChevronDown,
  FileCheck2,
  FileText,
  Home,
  Hourglass,
  Landmark,
  Lock,
  Mail,
  OctagonX,
  Paperclip,
  Receipt,
  ShieldCheck,
  Snowflake,
  Undo2,
} from "lucide-react";
import { motion } from "motion/react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useState } from "react";
import type { Approval, Disclosure, Money, OutboundPack, Payee, Payment, Reason, Refund, RefundPaperwork } from "@/lib/api/types";
import { useSimClock } from "@/lib/clock";
import { plainName, useFormat } from "@/lib/format";
import { usePersona } from "@/lib/persona";
import { paymentTone, refundPath } from "@/lib/status";
import { cn } from "@/lib/utils";
import { costVsMid } from "@/lib/fx";
import { isMine } from "@/lib/approval";
import { useErrorToast } from "@/lib/errors";
import { formsOf, openPaperwork, promiseDays, refundPhase, useRefundStory } from "@/lib/refund";
import { CoolingCard, NeedsCard } from "./review";
import { Button } from "@/components/ui/button";
import { MockBadge, Pill, RuleId } from "./badges";
import { HashChip } from "./hash";
import { MoneyPath } from "./money-path";
import { PasskeySheet } from "./passkey";
import { CheckRow, Line, Panel, ReasonList } from "./primitives";
import { DemoToday } from "./shell";
import { EscalationLetterCard, OverdueRefund } from "./plan";

// ---------------------------------------------------------------------------
// Verified payee

export function PayeeChecks({ payee, compact = false }: { payee: Payee; compact?: boolean }) {
  const t = useTranslations("payee");
  const [open, setOpen] = useState(false);
  const credOk = payee.credential.status === "valid";
  return (
    <div>
      <div className="flex items-center gap-3">
        <span className={cn("grid size-10 shrink-0 place-items-center rounded-xl", credOk ? "bg-verified-soft text-verified-ink" : "bg-blocked-soft text-blocked-ink")}>
          <Building2 className="size-5" />
        </span>
        <div className="min-w-0">
          <div className="truncate font-semibold">{payee.name}</div>
          <div className="truncate text-xs text-muted-foreground">
            {payee.account.bank ?? ""} {payee.account.masked}
          </div>
        </div>
        {credOk && (
          <Pill tone="verified" className="ml-auto">
            <ShieldCheck className="size-3.5" />
            {t("verified")}
          </Pill>
        )}
      </div>
      <div className={cn("mt-3", compact ? "space-y-0" : "space-y-0.5")}>
        <CheckRow
          state={credOk ? "ok" : "fail"}
          title={credOk ? t("vouched", { issuer: plainName(payee.institution) }) : t("notVouched")}
          detail={!compact && credOk ? t("vouchedDetail") : undefined}
        />
        <CheckRow
          state={payee.account.hashMatch ? "ok" : "fail"}
          title={payee.account.hashMatch ? t("accountMatch") : t("accountMismatch")}
          detail={!compact ? `${payee.account.bank ?? ""} ${payee.account.masked}` : undefined}
        />
        <CheckRow
          state={payee.nameCheck === "match" ? "ok" : payee.nameCheck === "close_match" ? "warn" : "fail"}
          title={t(`name.${payee.nameCheck}`)}
        />
        {payee.credential.chainTx && !compact && (
          <CheckRow
            state="ok"
            title={t("onChain")}
            detail={
              <span className="inline-flex items-center gap-1.5">
                {t("block", { n: payee.credential.chainTx.blockNumber })}
                <HashChip value={payee.credential.chainTx.txHash} />
              </span>
            }
          />
        )}
      </div>
      {!compact && credOk && (
        <button type="button" onClick={() => setOpen(!open)} className="mt-1 flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
          {t("technical")}
          <ChevronDown className={cn("size-3.5 transition-transform", open && "rotate-180")} />
        </button>
      )}
      {open && (
        <dl className="mt-2 space-y-1.5 rounded-lg bg-subtle p-3 font-mono text-[11px] break-all text-muted-foreground">
          <div>
            <dt className="text-foreground/70">issuer</dt>
            <dd>{payee.credential.issuer}</dd>
          </div>
          {payee.credential.vcId && (
            <div>
              <dt className="text-foreground/70">credential</dt>
              <dd>{payee.credential.vcId}</dd>
            </div>
          )}
        </dl>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Quote / disclosure

/**
 * What you pay, plainly: amount, rate, fee, total payable, amount received. No comparison at the moment
 * of saying yes; the bank's own mid-rate and margin (from the quote itself) sit behind "Rate details".
 */
export function Breakdown({ d, showCancel = true }: { d: Disclosure | (Omit<Disclosure, "cancelUntil"> & { cancelUntil?: string }); showCancel?: boolean }) {
  const t = useTranslations("quote");
  const f = useFormat();
  const [details, setDetails] = useState(false);
  const { total, receive, mid, rate, fees, converted: send } = costVsMid(d);
  return (
    <div>
      <Line label={t("converted")} value={f.money(send, d.send.currency)} muted />
      <Line
        label={
          <span className="inline-flex flex-wrap items-center gap-1.5">
            {t("rate")}
            {d.fx.source === "MOCK" && <MockBadge what="rate" />}
          </span>
        }
        value={`1 ${f.parts(d.receive).symbol} = ${f.number(rate, 2)} ${f.parts(d.send).symbol}`}
        muted
      />
      <Line label={t("fee")} value={f.money(fees, d.fees.currency)} muted />
      <div className="mt-1 border-t border-dashed pt-1.5">
        <Line label={t("youPay")} value={f.money(total, d.send.currency)} strong />
        <Line label={t("theyGet")} value={f.money(receive, d.receive.currency)} strong />
      </div>
      <button type="button" onClick={() => setDetails(!details)} aria-expanded={details} className="mt-1 inline-flex items-center gap-1 px-0.5 text-xs font-medium text-muted-foreground hover:text-foreground">
        {t("details")}
        <ChevronDown className={cn("size-3.5 transition-transform", details && "rotate-180")} />
      </button>
      {details && (
        <p className="mt-1 rounded-lg bg-subtle px-3 py-2 text-xs leading-relaxed text-pretty text-muted-foreground">
          {t("mid", { mid: f.number(mid, 2), margin: f.number(Number(d.fx.marginPct), 2) })} · {t(d.fx.source === "MOCK" ? "sourceMock" : "sourceEcb")}
        </p>
      )}
      {showCancel && d.cancelUntil && (
        <p className="mt-2 flex items-center gap-1.5 px-1 text-xs text-muted-foreground">
          <Hourglass className="size-3.5" />
          {t("cancel")}
        </p>
      )}
    </div>
  );
}

export function QuoteCard({ data }: { data: Record<string, unknown> }) {
  const t = useTranslations("cards");
  const d = data as unknown as Disclosure & { invoiceRef?: string; dueDate?: string; rate: string; midRate: string; marginPct: string; source: "MOCK" | "ECB"; quotedAt: string };
  const f = useFormat();
  return (
    <Panel className="p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold">{t("quote.title")}</h3>
        <span className="text-xs text-muted-foreground">{t("quote.at", { time: f.date(d.quotedAt, "time") })}</span>
      </div>
      <Breakdown
        d={{ send: d.send, fees: d.fees, receive: d.receive, fx: { rate: d.rate, midRate: d.midRate, marginPct: d.marginPct, source: d.source, quotedAt: d.quotedAt } }}
        showCancel={false}
      />
    </Panel>
  );
}

export function PayeeCard({ data }: { data: Record<string, unknown> }) {
  return (
    <Panel className="p-4">
      <PayeeChecks payee={data as unknown as Payee} compact />
    </Panel>
  );
}

// ---------------------------------------------------------------------------
// Paperwork pack

export function PackList({ pack }: { pack: OutboundPack }) {
  const t = useTranslations("pack");
  const ready = pack.documents.filter((d) => d.status === "ready").length;
  return (
    <div>
      <div className="flex items-center gap-3">
        <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-route-soft text-route-ink">
          <FileCheck2 className="size-5" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="font-semibold">{t("ready", { ready, total: pack.documents.length })}</div>
          <div className="text-xs text-muted-foreground">{t("rule", { corridor: pack.corridor })}</div>
        </div>
      </div>
      <ul className="mt-3 grid grid-cols-1 gap-x-4 sm:grid-cols-2">
        {pack.documents.map((d) => (
          <li key={d.kind}>
            <CheckRow state={d.status === "ready" ? "ok" : "pending"} title={<span className="font-normal">{t(`docs.${d.kind}` as never)}</span>} className="py-1" />
          </li>
        ))}
      </ul>
      <p className="mt-2 text-[11px] text-muted-foreground">{t("version", { v: pack.rulesVersion })}</p>
    </div>
  );
}

export function PackCard({ data }: { data: Record<string, unknown> }) {
  return (
    <Panel className="p-4">
      <PackList pack={data as unknown as OutboundPack} />
    </Panel>
  );
}

// ---------------------------------------------------------------------------
// Blocked

interface BlockedData {
  scenario?: string;
  attempted?: {
    action: string;
    account?: string;
    provenance?: string;
    amount?: Money;
    payee?: Payee;
    source?: { kind: string; filename?: string; sender?: string };
  };
  reasons?: Reason[];
  ruleIds?: string[];
  next?: string[];
  disposition?: string;
  result?: string;
  outOfBandVerificationRequired?: boolean;
  cooling?: { until: string; cosignRequired: boolean; cosignerId: string };
  risk?: { score: number; features: Reason[] };
}

/** What a forwarded document asked for, quoted as data (live API cards carry only the decision). */
function useDocumentAsk(docIds: string[] | undefined) {
  const { client, persona } = usePersona();
  return useQuery({
    queryKey: ["doc-ask", persona, docIds?.join(",")],
    enabled: !!docIds?.length,
    queryFn: async () => {
      const docs = await Promise.all(docIds!.map((id) => client.documents.get(id).catch(() => null)));
      const doc = docs.find((d) => d && d.kind !== "invoice" && d.kind !== "admission") ?? docs.find(Boolean) ?? null;
      if (!doc) return null;
      const text = doc.fields.find((x) => x.name === "text")?.value ?? "";
      const line =
        text
          .split("\n")
          .map((l) => l.trim())
          .find((l) => /account|redirect|deposit|tài khoản|계좌|账户/i.test(l)) ??
        doc.fields.find((x) => /account/i.test(x.name))?.value ??
        null;
      const account = line?.match(/(?:account|redirect[^:]*to)[^A-Z0-9]*([A-Z0-9][A-Z0-9-]{3,})/i)?.[1] ?? null;
      return { filename: doc.filename, line, account };
    },
  });
}

export function BlockedCard({ data, contextDocIds }: { data: Record<string, unknown>; contextDocIds?: string[] }) {
  const t = useTranslations("blocked");
  const td = useTranslations("chat.disposition");
  const f = useFormat();
  const d = data as unknown as BlockedData;
  const result = d.disposition ?? d.result ?? "DENY";
  const cooling = !!d.cooling;
  const deny = result === "DENY" && !cooling;
  const typed = d.attempted?.provenance === "user_input" && !cooling;
  const allReasons = d.reasons ?? (d.ruleIds ?? []).map((ruleId) => ({ ruleId, code: ruleId, severity: "block" as const, params: {} }));
  const reasons = typed
    ? allReasons.filter((r, i, all) => (r.code !== "NEVER_ALLOWED" || all.length === 1) && all.findIndex((x) => x.code === r.code) === i)
    : allReasons;
  const redirect = d.attempted?.action === "change_refund_destination";
  const ask = useDocumentAsk(d.attempted?.payee || cooling ? undefined : contextDocIds);
  const next = cooling
    ? (["NEXT_CALL", "NEXT_NO_SECRET", "NEXT_LAN"] as const).map((n) => t(`stepsCooling.${n}`))
    : typed
      ? [t("stepsDefault.NEXT_NOTHING_MOVED")]
      : d.next?.map((n) => t(`steps.${n}` as never)) ??
    (deny
      ? (["NEXT_NOTHING_MOVED", ...(d.outOfBandVerificationRequired ? ["NEXT_VERIFY_OFFICIAL"] : []), "NEXT_DONT_REPLY"] as const).map((n) => t(`stepsDefault.${n}` as never))
      : (reasons.some((r) => r.code === "MANDATE_REQUIRED" || r.code === "CAP_EXCEEDED") ? ["NEXT_SET_LIMIT"] : ["NEXT_SEND_DOCS"]).map((n) => t(`stepsEscalate.${n}` as never)));

  const tone = deny
    ? { border: "border-blocked/30", head: "bg-blocked-soft", ink: "text-blocked-ink", dot: "bg-blocked", mono: "text-blocked" }
    : { border: "border-attention/40", head: "bg-attention-soft", ink: "text-attention-ink", dot: "bg-attention", mono: "text-attention-ink" };

  return (
    <motion.article
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("overflow-hidden rounded-2xl border bg-card shadow-card", tone.border)}
      aria-label={deny ? t("title") : t("titleEscalate")}
    >
      <div className={cn("flex items-start gap-3 px-4 py-3.5", tone.head)}>
        <motion.span
          initial={{ scale: 0.6, rotate: -12 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ type: "spring", stiffness: 400, damping: 15 }}
          className={cn("grid size-9 shrink-0 place-items-center rounded-full text-white", tone.dot)}
        >
          {deny ? <OctagonX className="size-5" /> : cooling ? <Snowflake className="size-5" /> : <Hourglass className="size-5" />}
        </motion.span>
        <div>
          <h3 className={cn("font-semibold", tone.ink)}>{deny ? (redirect ? t("titleRedirect") : typed ? t("titleRefused") : t("title")) : cooling ? t("titleCooling") : t("titleEscalate")}</h3>
          <p className={cn("text-sm opacity-85", tone.ink)}>{deny ? t("nothingMoved") : cooling ? t("nothingMovedCooling") : t("nothingMovedEscalate")}</p>
        </div>
      </div>

      <div className="space-y-4 p-4">
        {d.attempted?.payee ? (
          <div>
            <h4 className="mb-1.5 text-xs font-medium tracking-wide text-muted-foreground uppercase">{t("attempted")}</h4>
            <div className="rounded-xl border border-dashed p-3">
              <p className="text-sm font-medium">
                {redirect
                  ? t("attemptRedirect", { account: (d.attempted.account ?? d.attempted.payee?.account.masked ?? "") })
                  : d.attempted.amount
                    ? t("attemptPay", { amount: f.money(d.attempted.amount), payee: (d.attempted.account ?? d.attempted.payee?.account.masked ?? "") })
                    : t("attemptAccount", { account: (d.attempted.account ?? d.attempted.payee?.account.masked ?? "") })}
              </p>
              <p className="mt-0.5 text-xs text-muted-foreground">{t("attemptDocDetail")}</p>
              {d.attempted.source && (
                <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Mail className="size-3.5" />
                  {t("source", { sender: d.attempted.source.sender ?? d.attempted.source.filename ?? "" })}
                </p>
              )}
              <MoneyPath
                state="blocked"
                compact
                className="mt-2"
                from={{ place: redirect ? "Hanbit University" : "Lotus Home Bank", sub: redirect ? "" : "•••• 4821" }}
                to={{ place: t("unverified"), sub: (d.attempted.account ?? d.attempted.payee?.account.masked ?? "") }}
              />
            </div>
          </div>
        ) : deny && ask.data ? (
          <div>
            <h4 className="mb-1.5 text-xs font-medium tracking-wide text-muted-foreground uppercase">{t("attempted")}</h4>
            <div className="rounded-xl border border-dashed p-3">
              <p className="flex items-center gap-1.5 text-sm font-medium">
                <Mail className="size-4 text-muted-foreground" />
                {t("attemptDoc", { file: ask.data.filename })}
              </p>
              {ask.data.line && <blockquote className="mt-2 border-l-2 border-blocked/50 pl-3 font-mono text-xs text-muted-foreground">{ask.data.line}</blockquote>}
              <p className="mt-2 text-xs text-muted-foreground">{t("attemptDocDetail")}</p>
              <MoneyPath state="blocked" compact className="mt-2" from={{ place: "Lotus Home Bank", sub: "•••• 4821" }} to={{ place: t("unverified"), sub: ask.data.account ?? undefined }} />
            </div>
          </div>
        ) : null}

        {reasons.length > 0 && (
          <div>
            <h4 className="mb-1 text-xs font-medium tracking-wide text-muted-foreground uppercase">{deny ? t("why") : t("whyEscalate")}</h4>
            <ReasonList reasons={reasons} />
          </div>
        )}

        <div>
          <h4 className="mb-1.5 text-xs font-medium tracking-wide text-muted-foreground uppercase">{t("next")}</h4>
          <ul className="space-y-1.5 text-sm">
            {next.map((n) => (
              <li key={n} className="flex gap-2">
                <ArrowRight className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                <span>{n}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="flex flex-wrap items-center gap-1.5 border-t pt-3 text-[11px] text-muted-foreground">
          <span>{t("decidedBy")}</span>
          <span className={cn("font-medium", tone.mono)}>{td.has(result as never) ? td(result as never) : result}</span>
          <span className="mx-1">·</span>
          {[...new Set(reasons.map((r) => r.ruleId))].map((id) => (
            <RuleId key={id} id={id} />
          ))}
        </div>
      </div>
    </motion.article>
  );
}

// ---------------------------------------------------------------------------
// Approval required (live status)

export function useApproval(id: string | undefined) {
  const { client, persona } = usePersona();
  return useQuery({ queryKey: ["approval", persona, id], queryFn: () => client.approvals.get(id!), enabled: !!id });
}

export function ApprovalRequiredCard({ data }: { data: Record<string, unknown> }) {
  const t = useTranslations("cards.approval");
  const ts = useTranslations("studyProgress");
  const f = useFormat();
  const { user } = usePersona();
  const id = (data.approvalId ?? data.id) as string;
  const q = useApproval(id);
  const a = q.data;
  const [sheet, setSheet] = useState(false);
  if (!a) return <Panel className="h-28 animate-pulse p-4" />;
  if (a.rejectionReason === "VISA_REFUSED_BEFORE_PAYMENT") return <Panel className="p-4 text-sm text-muted-foreground">{ts("requestStopped")}</Panel>;
  if (a.status === "cooling_off" || a.rawAction?.purpose === "verify_scam_claim") return <CoolingCard approval={a} viewer={user} />;
  if (a.action === "refund_claim") return <RefundClaimCard approval={a} />;
  if (a.action === "escalation_letter") return <EscalationLetterCard approval={a} />;
  const mine = isMine(a, user);
  const statusTone = a.status === "approved" ? "verified" : a.status === "pending" ? "attention" : "neutral";
  const total = a.disclosure ? Number(a.disclosure.send.amount) : 0;
  return (
    <Panel className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className={cn("grid size-10 shrink-0 place-items-center rounded-xl", a.status === "approved" ? "bg-verified-soft text-verified-ink" : a.status === "pending" ? "bg-attention-soft text-attention-ink" : "bg-secondary text-muted-foreground")}>
            <Landmark className="size-5" />
          </span>
          <div>
            <h3 className="font-semibold">{t(`title.${a.action}`)}</h3>
            {a.status === "pending" && <p className="text-xs text-muted-foreground">{user?.frozen ? ts("approvalPaused") : mine ? t("forYou") : t(`forOther.${a.action}`)}</p>}
          </div>
        </div>
        <Pill tone={statusTone} dot pulse={a.status === "pending"}>
          {t(`status.${a.status}`)}
        </Pill>
      </div>
      {a.disclosure && (
        <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
          <div className="rounded-xl bg-subtle p-3">
            <div className="text-xs text-muted-foreground">{t("youPay")}</div>
            <div className="mt-0.5 font-semibold tnum">{f.money(total, a.disclosure.send.currency)}</div>
          </div>
          <div className="rounded-xl bg-subtle p-3">
            <div className="text-xs text-muted-foreground">{t("hanbitGets")}</div>
            <div className="mt-0.5 font-semibold tnum">{f.money(a.disclosure.receive)}</div>
          </div>
        </div>
      )}
      {a.status === "pending" && mine && !user?.frozen && (
        <div className="mt-3">
          {user?.role === "parent" ? (
            <Button asChild size="lg" className="h-11 w-full rounded-xl">
              <Link href={`/parent/approvals/${a.id}`}>
                {t("review")} <ArrowRight className="size-4" />
              </Link>
            </Button>
          ) : (
            <>
              <Button size="lg" className="h-11 w-full rounded-xl" onClick={() => setSheet(true)}>
                <ShieldCheck className="size-4" /> {t("approveClaim")}
              </Button>
              <ApproveSheet approval={a} open={sheet} onOpenChange={setSheet} />
            </>
          )}
        </div>
      )}
    </Panel>
  );
}

/** Linh's refund consent: two forms, one signature, money back only to the account that paid. */
export function RefundClaimCard({ approval: a }: { approval: Approval }) {
  const t = useTranslations("cards.approval");
  const tr = useTranslations("refund");
  const f = useFormat();
  const { user } = usePersona();
  const [sheet, setSheet] = useState(false);
  // Once signed, the refund carries the signed copy; the approval keeps the prepared version unchanged.
  const filed = useRefund(a.status === "approved" ? a.resultRef : undefined).data;
  const mine = isMine(a, user);
  const raw = a.rawAction as { refundAmount?: Money; paperwork?: RefundPaperwork };
  const pw = raw.paperwork;
  const sum = a.refundSummary;
  const dest = sum?.destination ?? pw?.destination;
  const claim = sum?.claimAmount ?? raw.refundAmount;
  const deadline = sum ? sum.deadline : pw?.deadline;
  const start = sum?.classesStart ?? pw?.policy?.classesStart;
  const est = sum?.estimate?.receivedBack;
  const statusTone = a.status === "approved" ? "verified" : a.status === "pending" ? "attention" : "neutral";
  return (
    <Panel className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className={cn("grid size-10 shrink-0 place-items-center rounded-xl", a.status === "approved" ? "bg-verified-soft text-verified-ink" : a.status === "pending" ? "bg-attention-soft text-attention-ink" : "bg-secondary text-muted-foreground")}>
            <FileText className="size-5" />
          </span>
          <div>
            <h3 className="leading-snug font-semibold text-balance">{t("title.refund_claim")}</h3>
            {a.status === "pending" && <p className="text-xs text-muted-foreground">{mine ? t("refund.forYou") : t("forOther.refund_claim")}</p>}
          </div>
        </div>
        <Pill tone={statusTone} dot pulse={a.status === "pending"}>
          {a.status === "approved" ? t("refund.signed") : t(`status.${a.status}`)}
        </Pill>
      </div>
      <div className="mt-3 divide-y rounded-xl border px-3">
        {claim && (
          <FactRow
            icon={<Undo2 className="size-4" />}
            label={t("refund.claim")}
            value={f.money(claim)}
            sub={est ? t("refund.claimSubEstimate", { amount: f.money(est) }) : t("refund.claimSub")}
          />
        )}
        <FactRow
          icon={<CalendarClock className="size-4" />}
          label={tr("fact.when")}
          value={deadline ? tr("when.promise", { date: f.date(deadline) }) : tr("when.manual")}
          sub={deadline && start ? tr("when.promiseSub", { n: pw?.policy?.paymentWithinDaysAfterClassesStart ?? 14, start: f.date(start) }) : tr("when.manualSub")}
        />
        {a.status === "pending" && (
          <div className="flex justify-end py-1.5">
            <DemoToday />
          </div>
        )}
        <FactRow
          icon={<Lock className="size-4" />}
          label={tr("fact.where")}
          value={dest ? `${plainName(dest.bank)} ${dest.maskedNumber}` : t("refundTo")}
          sub={dest && "swift" in dest && dest.swift ? t("refund.whereSub", { swift: dest.swift }) : tr("where.sub")}
        />
      </div>
      {pw && (
        <>
          <p className="mt-3 px-1 text-xs font-medium text-muted-foreground">{t(mine ? "refund.youSign" : "refund.theySign")}</p>
          <RefundForms refund={filed} approval={a} className="px-1" />
        </>
      )}
      {a.status === "pending" && mine && (
        <div className="mt-3">
          <Button size="lg" className="h-11 w-full rounded-xl" onClick={() => setSheet(true)}>
            <ShieldCheck className="size-4" /> {t("approveClaim")}
          </Button>
          <ApproveSheet approval={a} open={sheet} onOpenChange={setSheet} />
        </div>
      )}
      {a.status === "approved" && a.resultRef && (
        <Link href={`/${user?.role === "parent" ? "parent" : "student"}/refunds/${a.resultRef}`} className="mt-3 inline-flex items-center gap-1 px-1 text-sm font-medium text-route-ink hover:underline">
          {tr("open")} <ArrowRight className="size-3.5" />
        </Link>
      )}
    </Panel>
  );
}

/** Rendered at the end of the assistant message that carried the approval card. */
export function ApprovalAfterLine({ approvalId }: { approvalId: string }) {
  const { user } = usePersona();
  const q = useApproval(approvalId);
  const a = q.data;
  if (!a || a.status !== "approved" || a.action === "refund_claim" || user?.role !== "student") return null;
  return <AfterApproval approval={a} />;
}

/** Linh's side of the story gets an ending: a short thread line once her parent has approved. */
function AfterApproval({ approval }: { approval: Approval }) {
  const t = useTranslations("cards.approval.after");
  const rel = useTranslations("rel");
  const { client, persona } = usePersona();
  const f = useFormat();
  const id = approval.resultRef;
  const pay = useQuery({ queryKey: ["payment", persona, id], queryFn: () => client.payments.get(id!), enabled: !!id && id.startsWith("pay_") });
  const status = pay.data?.status;
  const payee = plainName(approval.payee?.institution) || "Hanbit University";
  const key = status === "cancelled" ? "cancelled" : status === "matched" || status === "received_by_bursar" ? "arrived" : "sent";
  const tone = key === "arrived" ? "text-verified-ink" : key === "cancelled" ? "text-muted-foreground" : "text-brand-ink";
  return (
    <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} className="flex items-start gap-2.5 rounded-xl bg-subtle px-3 py-2.5 text-[13px]" role="status">
      <span className={cn("mt-0.5 grid size-5 shrink-0 place-items-center rounded-full", key === "arrived" ? "bg-verified text-white" : key === "cancelled" ? "bg-muted text-muted-foreground" : "bg-brand text-white")}>
        {key === "sent" ? <ArrowRight className="size-3" strokeWidth={3} /> : <Check className="size-3" strokeWidth={3} />}
      </span>
      <span className="min-w-0 flex-1 text-pretty">
        <span className={cn("font-medium", tone)}>{t(key, { who: rel("parent"), payee })}</span>
        {key === "sent" && pay.data?.cancelUntil && (
          <span className="block text-xs text-muted-foreground">{t("sentSub", { time: f.date(pay.data.cancelUntil, "time"), who: rel("parent") })}</span>
        )}
      </span>
    </motion.div>
  );
}

/** Passkey sheet bound to an approval: signs the consent hash, then calls approve. */
export function ApproveSheet({ approval, open, onOpenChange, onDone }: { approval: Approval; open: boolean; onOpenChange: (o: boolean) => void; onDone?: () => void }) {
  const t = useTranslations("cards.approval");
  const f = useFormat();
  const { client, user } = usePersona();
  const qc = useQueryClient();
  const showError = useErrorToast();
  const total = approval.disclosure ? Number(approval.disclosure.send.amount) : 0;
  const lines =
    approval.action === "refund_claim"
      ? (() => {
          const raw = approval.rawAction as { refundAmount?: Money; paperwork?: RefundPaperwork };
          const dest = raw.paperwork?.destination;
          return [
            { label: t("sign.forms"), value: t("sign.formsValue") },
            ...(raw.refundAmount ? [{ label: t("refund.claim"), value: f.money(raw.refundAmount) }] : []),
            { label: t("sign.to"), value: dest ? `${plainName(dest.bank)} ${dest.maskedNumber}` : t("refundTo") },
            ...(raw.paperwork?.deadline ? [{ label: t("sign.by"), value: f.date(raw.paperwork.deadline) }] : []),
          ];
        })()
      : !approval.disclosure
        ? [{ label: t("sign.claim"), value: approval.action }]
        : [
          { label: user?.role === "parent" ? t("youPayParent") : t("youPay"), value: f.money(total, approval.disclosure!.send.currency) },
          { label: t("hanbitGets"), value: f.money(approval.disclosure!.receive) },
          { label: t("sign.to"), value: `${plainName(approval.payee?.institution)} ${approval.payee?.account.masked}` },
        ];
  return (
    <PasskeySheet
      open={open}
      onOpenChange={onOpenChange}
      purpose="approval"
      refId={approval.id}
      hash={approval.consentHash}
      title={t(`sign.title.${approval.action}`)}
      lines={lines}
      onSigned={async (assertion) => {
        try {
          await client.approvals.approve(approval.id, assertion);
          qc.invalidateQueries();
          onDone?.();
        } catch (e) {
          showError(e);
          throw e;
        }
      }}
    />
  );
}

// ---------------------------------------------------------------------------
// Refund

export function useRefund(id: string | undefined) {
  const { client, persona } = usePersona();
  return useQuery({ queryKey: ["refund", persona, id], queryFn: () => client.refunds.get(id!), enabled: !!id });
}

export function DeadlineRing({ deadline, start, nowMs, size = 56 }: { deadline: string; start: string; nowMs: number; size?: number }) {
  const t = useTranslations("refund");
  const total = Date.parse(deadline) - Date.parse(start);
  const left = Math.max(0, Date.parse(deadline) - nowMs);
  const k = total > 0 ? left / total : 0;
  const days = Math.ceil(left / 86400_000);
  const r = size / 2 - 4;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative grid shrink-0 place-items-center" style={{ width: size, height: size }} role="img" aria-label={t("daysLeft", { n: days })}>
      <svg width={size} height={size} className="-rotate-90" aria-hidden>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border)" strokeWidth="4" />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={k < 0.1 ? "var(--attention)" : "var(--route)"}
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={c}
          initial={false}
          animate={{ strokeDashoffset: c * (1 - k) }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        />
      </svg>
      <div className="absolute text-center leading-none" aria-hidden>
        <div className="text-base font-semibold tnum">{days}</div>
        <div className="text-[9px] text-muted-foreground uppercase">{t("days")}</div>
      </div>
    </div>
  );
}

function FactRow({ icon, label, value, sub, className }: { icon: React.ReactNode; label: string; value: React.ReactNode; sub?: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex items-start gap-3 py-2.5", className)}>
      <span className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-lg bg-subtle text-muted-foreground">{icon}</span>
      <div className="min-w-0 flex-1">
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="text-[15px] leading-snug font-medium text-pretty">{value}</div>
        {sub && <div className="mt-0.5 text-xs leading-relaxed text-pretty text-muted-foreground">{sub}</div>}
      </div>
    </div>
  );
}

/**
 * The refund in four answers a parent can read on a phone: how much comes back, when, to which
 * account, and why it is a little less than what went out. No clause numbers.
 */
export function RefundSummary({ refund, linkBase, showStatementLink = true }: { refund: Refund; linkBase?: string; showStatementLink?: boolean }) {
  const t = useTranslations("refund");
  const f = useFormat();
  const { nowMs } = useSimClock();
  const story = useRefundStory(refund);
  const phase = refundPhase(refund);
  const done = phase === "back";
  const start = refund.classesStart ?? refund.policy?.classesStart ?? refund.paperwork?.policy?.classesStart;
  const back = story.statement?.receivedBack;
  const bank = plainName(refund.destination.bank);
  return (
    <div>
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold">{t("title")}</h3>
            <Pill tone={done ? "verified" : phase === "manual" ? "neutral" : "attention"} dot pulse={!done && phase !== "manual"}>
              {t(`status.${refund.status}` as never)}
            </Pill>
          </div>
          <p className="mt-1.5 font-display text-[22px] leading-tight font-medium tracking-tight text-balance tnum">
            {phase === "manual"
              ? t("hero.manual")
              : back
                ? done
                  ? t("hero.back", { amount: f.money(back) })
                  : t("hero.estimate", { amount: f.money(back) })
                : t("hero.whole")}
          </p>
          {!done && story.estimate && (
            <p className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
              {t("hero.estimateNote")} <MockBadge what="bank" />
            </p>
          )}
        </div>
        {!done && refund.deadline && story.requestedAt && !refund.followUp?.overdue && <DeadlineRing deadline={refund.deadline} start={story.requestedAt} nowMs={nowMs} />}
      </div>

      <div className="mt-3 divide-y rounded-xl border px-3">
        <FactRow
          icon={<CalendarClock className="size-4" />}
          label={t("fact.when")}
          value={
            done && story.backAt
              ? t("when.back", { date: f.date(story.backAt) })
              : refund.deadline
                ? t("when.promise", { date: f.date(refund.deadline) })
                : t("when.manual")
          }
          sub={
            done && refund.deadline
              ? t("when.backSub", { date: f.date(refund.deadline) })
              : refund.deadline && start
                ? t("when.promiseSub", { n: promiseDays(refund), start: f.date(start) })
                : t("when.manualSub")
          }
        />
        {!done && (
          <div className="flex justify-end py-1.5">
            <DemoToday />
          </div>
        )}
        <FactRow
          icon={<Lock className="size-4" />}
          label={t("fact.where")}
          value={`${bank} ${refund.destination.maskedNumber}`}
          sub={t("where.sub")}
        />
        {story.less !== null && story.statement && (
          <FactRow
            icon={<Receipt className="size-4" />}
            label={t("fact.why")}
            value={t(done ? "why.value" : "why.valueEstimate", { amount: f.money(story.less, story.statement.sentOut.currency) })}
            sub={
              <>
                {t("why.sub")}
                {linkBase && showStatementLink && (
                  <Link href={`${linkBase}/refunds/${refund.id}#statement`} className="ml-1 font-medium text-route-ink hover:underline">
                    {t("why.link")}
                  </Link>
                )}
              </>
            }
          />
        )}
      </div>

      <MoneyPath
        className="mt-3"
        compact
        state={refundPath(refund)}
        from={{ place: t("home"), sub: `${bank} ${refund.destination.maskedNumber}` }}
        to={{ place: "Hanbit University", sub: t("bursar") }}
      />
      {linkBase && (
        <Link href={`${linkBase}/refunds/${refund.id}`} className="mt-2 inline-flex items-center gap-1 px-1 text-sm font-medium text-route-ink hover:underline">
          {t("open")} <ArrowRight className="size-3.5" />
        </Link>
      )}
    </div>
  );
}

export function RefundCard({ data }: { data: Record<string, unknown> }) {
  // The live API sends the Refund itself; the mock sends a reference.
  const id = (data.refundId ?? data.id) as string | undefined;
  const q = useRefund(id);
  const { user } = usePersona();
  if (!q.data) return <Panel className="h-40 animate-pulse p-4" />;
  return (
    <div className="space-y-2.5">
      <OverdueRefund refund={q.data} />
      <Panel className="p-4">
        <RefundSummary refund={q.data} linkBase={user?.role === "parent" ? "/parent" : "/student"} />
      </Panel>
    </div>
  );
}

/** The two forms one consent signs, plus the letter attached as evidence. Previews are authenticated PDF projections. */
export function RefundForms({ refund, approval, className }: { refund?: Refund; approval?: Approval; className?: string }) {
  const t = useTranslations("refund.forms");
  const f = useFormat();
  const { client, user } = usePersona();
  const showError = useErrorToast();
  const forms = formsOf(refund, approval);
  const who = (id?: string) => (id === "usr_student_hao" || (!id && user?.familyId === "fam_wang") ? "Hao" : "Linh");
  const rows = [forms.withdrawal, forms.application].filter(Boolean) as NonNullable<typeof forms.withdrawal>[];
  return (
    <ul className={cn("divide-y", className)}>
      {rows.map((d) => (
        <li key={d.kind} className="flex items-start gap-3 py-2.5">
          <span className={cn("mt-0.5 grid size-8 shrink-0 place-items-center rounded-lg", d.status === "signed" ? "bg-verified-soft text-verified-ink" : "bg-subtle text-muted-foreground")}>
            {d.status === "signed" ? <FileCheck2 className="size-4" /> : <FileText className="size-4" />}
          </span>
          <div className="min-w-0 flex-1">
            <div className="text-sm font-medium">{t(`${d.kind}.title` as never)}</div>
            <div className="text-xs leading-relaxed text-pretty text-muted-foreground">{t(`${d.kind}.sub` as "admission_withdrawal.sub")}</div>
            <div className={cn("mt-0.5 text-xs", d.status === "signed" ? "text-verified-ink" : "text-muted-foreground")}>
              {d.status === "signed" && d.signedAt
                ? d.signerId === user?.id
                  ? t("signedYou", { date: f.date(d.signedAt) })
                  : t("signed", { who: who(d.signerId), date: f.date(d.signedAt) })
                : d.signerId === user?.id
                  ? t("waitingYou")
                  : t("waiting", { who: who(d.signerId) })}
            </div>
          </div>
          {approval && (
            <Button
              variant="outline"
              size="sm"
              className="h-8 shrink-0 rounded-lg"
              onClick={() => openPaperwork(() => client.approvals.paperwork(approval.id, d.kind as "admission_withdrawal" | "tuition_refund_application"), `${d.kind}.pdf`).catch(showError)}
            >
              {t("view")}
            </Button>
          )}
        </li>
      ))}
      {forms.denial && (
        <li className="flex items-start gap-3 py-2.5">
          <span className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-lg bg-subtle text-muted-foreground">
            <Paperclip className="size-4" />
          </span>
          <div className="min-w-0 flex-1">
            <div className="text-sm font-medium">{t("visa_denial_letter.title")}</div>
            <div className="text-xs text-muted-foreground">{t("visa_denial_letter.sub")}</div>
          </div>
          <MockBadge what="bursar" className="mt-1" />
        </li>
      )}
    </ul>
  );
}

// ---------------------------------------------------------------------------
// Info

/** A payment the agent just made or reported on (the live API sends the Payment itself as an info card). */
function PaymentSummaryCard({ id, initial }: { id: string; initial?: Payment }) {
  const t = useTranslations("cards.info");
  const tp = useTranslations("payment");
  const ta = useTranslations("cards.approval");
  const f = useFormat();
  const { client, persona, user } = usePersona();
  const pay = useQuery({ queryKey: ["payment", persona, id], queryFn: () => client.payments.get(id), initialData: initial });
  const p = pay.data;
  if (!p) return null;
  const rent = p.purpose === "rent";
  const payee = p.payee?.name?.replace(" (MOCK)", "") ?? "Hanbit University";
  return (
    <Panel className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-route-soft text-route-ink">
            {rent ? <Home className="size-5" /> : <Landmark className="size-5" />}
          </span>
          <div>
            <h3 className="font-semibold">{tp(rent ? "purpose.rent" : "purpose.tuition")}</h3>
            <p className="text-xs text-muted-foreground">{tp("to", { payee })}</p>
          </div>
        </div>
        <Pill tone={paymentTone(p)} dot>
          {tp(`status.${p.status}` as never)}
        </Pill>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
        <div className="rounded-xl bg-subtle p-3">
          <div className="text-xs text-muted-foreground">{ta("youPay")}</div>
          <div className="mt-0.5 font-semibold tnum">{f.money(p.send)}</div>
        </div>
        <div className="rounded-xl bg-subtle p-3">
          <div className="text-xs text-muted-foreground">{tp("received")}</div>
          <div className="mt-0.5 font-semibold tnum">{f.money(p.receive)}</div>
        </div>
      </div>
      {rent && user?.role === "parent" && <p className="mt-3 text-xs leading-relaxed text-pretty text-muted-foreground">{tp("autoExplain")}</p>}
      <Link href={`/${user?.role === "parent" ? "parent" : "student"}/payments/${p.id}`} className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-route-ink hover:underline">
        {t("openPayment")} <ArrowRight className="size-3.5" />
      </Link>
    </Panel>
  );
}

export function InfoCard({ data }: { data: Record<string, unknown> }) {
  const t = useTranslations("cards.info");
  const code = String(data.code);
  const { user } = usePersona();
  if (typeof data.id === "string" && data.id.startsWith("pay_") && data.send) return <PaymentSummaryCard id={data.id} initial={data as unknown as Payment} />;
  if (code === "PAYMENT_STATUS" && data.paymentId) return <PaymentSummaryCard id={String(data.paymentId)} />;
  if (code === "REFUND_CASE_STATUS" && data.approvalId) return <ApprovalRequiredCard data={{ approvalId: data.approvalId }} />;
  const icon =
    code === "FREEZE_HINT" ? <Snowflake className="size-4" /> : code === "NEED_INVOICE" ? <FileText className="size-4" /> : <ShieldCheck className="size-4" />;
  return (
    <div className="flex items-start gap-3 rounded-xl border border-dashed bg-subtle/60 px-3.5 py-3 text-sm">
      <span className="mt-0.5 text-muted-foreground">{icon}</span>
      <div className="text-pretty text-muted-foreground">
        {t.has(code as never) ? t(code as never) : t("generic")}
        {code === "FREEZE_HINT" && user?.role === "parent" && (
          <Link href="/parent/freeze" className="ml-1 font-medium text-foreground underline-offset-4 hover:underline">
            {t("openFreeze")}
          </Link>
        )}
      </div>
    </div>
  );
}

export function AgentCard({ kind, data, contextDocIds }: { kind: string; data: Record<string, unknown>; contextDocIds?: string[] }) {
  switch (kind) {
    case "quote":
      return <QuoteCard data={data} />;
    case "payee":
      return <PayeeCard data={data} />;
    case "pack":
      return <PackCard data={data} />;
    case "approval_required":
      return <ApprovalRequiredCard data={data} />;
    case "blocked":
      return <BlockedCard data={data} contextDocIds={contextDocIds} />;
    case "needs":
      return <NeedsCard data={data} />;
    case "refund":
      return <RefundCard data={data} />;
    case "payment": {
      // r5: explicit payment card (monthly rent). Accept the Payment itself or a reference to it.
      const p = (data.payment ?? data) as Partial<Payment> & { paymentId?: string };
      const pid = typeof p.id === "string" && p.id.startsWith("pay_") ? p.id : p.paymentId;
      return pid ? <PaymentSummaryCard id={pid} initial={p.send ? (p as Payment) : undefined} /> : <InfoCard data={data} />;
    }
    default:
      return <InfoCard data={data} />;
  }
}
