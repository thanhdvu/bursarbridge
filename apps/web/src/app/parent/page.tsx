"use client";

import { ArrowRight, ChevronRight, Home, Landmark, Lock, ShieldCheck, Snowflake, Undo2 } from "lucide-react";
import { motion } from "motion/react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { MockBadge, Pill } from "@/components/bb/badges";
import { MoneyPath } from "@/components/bb/money-path";
import { Initials, Panel, SectionLabel } from "@/components/bb/primitives";
import { AppHeader, DemoToday, LocaleSwitcher, ThemeToggle } from "@/components/bb/shell";
import { NumberTicker } from "@/components/bb/ticker";
import { AdmissionNotice } from "@/components/bb/study-progress";
import { FrozenBanner } from "@/components/bb/frozen-banner";
import { MandateCard, PaymentRow } from "@/components/bb/rows";
import { CoolingCard, useCoolingReviews } from "@/components/bb/review";
import { useFormat } from "@/lib/format";
import { usePersona } from "@/lib/persona";
import { useApprovals, useMandates, usePayments, useRefunds } from "@/lib/queries";
import { paymentPath, paymentTone, refundPath } from "@/lib/status";
import type { Payment, Refund } from "@/lib/api/types";
import { useRefundStory } from "@/lib/refund";
import { isMine } from "@/lib/approval";
import { ObligationsCard, PaymentWindowLine, useStudyPlan } from "@/components/bb/plan";

export default function ParentHome() {
  const t = useTranslations("parent.home");
  const { user } = usePersona();
  const f = useFormat();
  const approvals = useApprovals("pending");
  const mandates = useMandates();
  const payments = usePayments();
  const refunds = useRefunds();
  const plan = useStudyPlan();

  const pending = approvals.data?.find((a) => isMine(a, user) && a.action !== "refund_claim");
  const studentSigning = approvals.data?.find((a) => a.action === "refund_claim");
  const cooling = useCoolingReviews();
  const tc = useTranslations("cooling");
  const review = cooling.data?.[0];
  const tuitionMandate = mandates.data?.find((m) => m.purpose === "tuition" && (m.status === "active" || m.status === "suspended"));
  const otherMandates = mandates.data?.filter((m) => m.purpose !== "tuition" && m.status !== "revoked") ?? [];
  const refund = refunds.data?.[0];
  const latest = payments.data?.[0];
  const tuitionPay = payments.data?.find((p) => (p.purpose ?? "tuition") === "tuition" && p.status !== "cancelled");
  const account = user?.accounts[0];
  const isWang = user?.familyId === "fam_wang";
  // Until every source has answered, show placeholders: a wrong "nothing to do" for a second is worse than a shimmer.
  const loading = !user || approvals.isPending || mandates.isPending || payments.isPending || refunds.isPending || cooling.isPending;

  // The one sentence that answers "what do I need to do?"
  let headline: { text: string; tone: "act" | "calm" | "moving"; cta?: { href: string; label: string } };
  if (review && !user?.frozen) headline = { text: tc("parentHero"), tone: "act" };
  else if (user?.frozen) headline = { text: t("headline.frozen"), tone: "act", cta: { href: "/parent/freeze", label: t("cta.unfreeze") } };
  else if (pending)
    headline = {
      text: pending.action === "first_payment" ? t("headline.approve", { name: isWang ? "Hao" : "Linh" }) : t("headline.approveGeneric"),
      tone: "act",
      cta: { href: `/parent/approvals/${pending.id}`, label: t("cta.review") },
    };
  else if (!tuitionMandate && !isWang) headline = { text: t("headline.setLimit"), tone: "act", cta: { href: "/parent/mandate/new", label: t("cta.setLimit") } };
  else if (pending === undefined && !isWang && tuitionMandate && !tuitionPay && plan.data?.paymentWindowStatus === "not_open")
    headline = { text: t("headline.windowNotOpen", { date: f.date(plan.data.currentPaymentWindow?.opensAt ?? plan.data.registrationWindow?.opensAt ?? "") }), tone: "calm" };
  else if (studentSigning) headline = { text: t("headline.studentSigns", { name: isWang ? "Hao" : "Linh" }), tone: "moving" };
  else if (refund && refund.status !== "reconciled") headline = { text: t("headline.refund"), tone: "moving" };
  else if (latest && ["executing", "sent", "received_by_bursar"].includes(latest.status)) headline = { text: t("headline.moving"), tone: "moving" };
  else headline = { text: t("headline.nothing"), tone: "calm" };

  const where = (() => {
    if (refund && ["sent"].includes(refund.status)) return t("where.returning");
    if (refund && refund.status !== "received" && refund.status !== "reconciled") return t("where.atSchoolRefund");
    if (tuitionPay && ["received_by_bursar", "matched"].includes(tuitionPay.status) && !refund) return t("where.atSchool");
    if (tuitionPay && ["executing", "sent"].includes(tuitionPay.status)) return t("where.onTheWay");
    return t("where.home");
  })();

  return (
    <>
      <AppHeader
        left={
          <div className="flex items-center gap-2.5">
            <Initials name={user?.name ?? " "} />
            <div className="min-w-0 leading-tight">
              <div className="truncate text-[15px] font-semibold">{user ? t("hello", { name: isWang ? user.name : user.name.split(" ").slice(-1)[0] }) : <span className="inline-block h-4 w-28 animate-pulse rounded bg-muted align-middle" />}</div>
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                {account?.bank.replace(" (MOCK)", "")} {account?.maskedNumber}
                <MockBadge what="bank" />
              </div>
            </div>
          </div>
        }
        right={
          <>
            <LocaleSwitcher compact />
            <ThemeToggle />
          </>
        }
      />
      <main className="flex-1 space-y-6 px-4 pt-2 pb-8">
        <FrozenBanner />
        <AdmissionNotice />

        {/* At a glance */}
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}>
          <Panel className="overflow-hidden">
            <div className="p-5">
              <p className="text-[13px] font-medium text-muted-foreground">{t("glance")}</p>
              {loading ? (
                <div className="mt-2 h-14 animate-pulse rounded-lg bg-muted" />
              ) : (
                <h1 className="mt-1.5 font-display text-[27px] leading-[1.15] font-medium tracking-tight text-balance">{headline.text}</h1>
              )}
              <DemoToday className="mt-2 -ml-1" />
              {!isWang && <PaymentWindowLine plan={plan.data} className="mt-1.5" />}
              {!loading && headline.cta && (
                <Button asChild size="lg" className="mt-4 h-12 w-full rounded-xl text-[15px]">
                  <Link href={headline.cta.href}>
                    {headline.cta.label}
                    <ArrowRight className="size-4" />
                  </Link>
                </Button>
              )}
            </div>
            <dl className="divide-y border-t bg-subtle/50 text-sm">
              <div className="flex items-center gap-3 px-5 py-3">
                <Landmark className="size-4 shrink-0 text-muted-foreground" />
                <dt className="shrink-0 whitespace-nowrap text-muted-foreground">{t("whereLabel")}</dt>
                <dd className="ml-auto min-w-0 text-right font-medium text-pretty">{loading ? <span className="inline-block h-4 w-32 animate-pulse rounded bg-muted align-middle" /> : where}</dd>
              </div>
              <div className="flex items-center gap-3 px-5 py-3">
                <ShieldCheck className="size-4 shrink-0 text-verified" />
                <dt className="shrink-0 whitespace-nowrap text-muted-foreground">{t("safeLabel")}</dt>
                <dd className="ml-auto min-w-0 text-right font-medium text-pretty">{isWang ? t("safeRent") : t("safe")}</dd>
              </div>
              {account && (
                <div className="flex items-center gap-3 px-5 py-3">
                  <Lock className="size-4 shrink-0 text-muted-foreground" />
                  <dt className="shrink-0 whitespace-nowrap text-muted-foreground">{t("balance")}</dt>
                  <dd className="ml-auto font-medium tnum">
                    <NumberTicker value={Number(account.balance.amount)} format={(n) => f.money(n, account.currency)} />
                  </dd>
                </div>
              )}
            </dl>
          </Panel>
        </motion.div>

        {review && <CoolingCard approval={review} viewer={user} />}

        {/* Money in motion */}
        {refund ? (
          <MotionRefund refund={refund} />
        ) : latest && (latest.purpose ?? "tuition") === "tuition" ? (
          <MotionPayment p={latest} />
        ) : null}

        {/* Boundaries */}
        <section>
          <SectionLabel>{t("boundaries")}</SectionLabel>
          <div className="space-y-3">
            {tuitionMandate ? (
              <MandateCard m={tuitionMandate} />
            ) : !isWang ? (
              <Link href="/parent/mandate/new" className="block">
                <Panel className="flex items-center gap-3 border-dashed p-4 shadow-none transition-colors hover:bg-accent">
                  <span className="grid size-10 place-items-center rounded-xl bg-secondary">
                    <ShieldCheck className="size-5" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="font-medium">{t("noMandate")}</div>
                    <div className="text-xs text-muted-foreground">{t("noMandateSub")}</div>
                  </div>
                  <ChevronRight className="size-4 text-muted-foreground" />
                </Panel>
              </Link>
            ) : null}
            {otherMandates.map((m) => (
              <MandateCard key={m.id} m={m} />
            ))}
            {isWang && !otherMandates.some((m) => m.purpose === "rent" && m.status !== "expired") && (
              <Link href="/parent/mandate/new?purpose=rent" className="block">
                <Panel className="flex items-center gap-3 border-dashed p-4 shadow-none transition-colors hover:bg-accent">
                  <span className="grid size-10 place-items-center rounded-xl bg-secondary">
                    <Home className="size-5" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="font-medium">{t("noRentMandate")}</div>
                    <div className="text-xs text-pretty text-muted-foreground">{t("noRentMandateSub")}</div>
                  </div>
                  <ChevronRight className="size-4 text-muted-foreground" />
                </Panel>
              </Link>
            )}
          </div>
        </section>

        {!isWang && <ObligationsCard plan={plan.data} />}

        {/* Recent */}
        {!!payments.data?.length && (
          <section>
            <SectionLabel
              action={
                <Link href="/parent/activity" className="text-[13px] font-medium text-route-ink hover:underline">
                  {t("seeAll")}
                </Link>
              }
            >
              {t("recent")}
            </SectionLabel>
            <Panel className="divide-y">
              {payments.data.slice(0, 3).map((p) => (
                <PaymentRow key={p.id} p={p} />
              ))}
            </Panel>
          </section>
        )}

        <Link href="/parent/freeze" className="block">
          <Panel className="flex items-center gap-3 p-4 transition-colors hover:bg-accent">
            <span className="grid size-10 place-items-center rounded-xl bg-route-soft text-route-ink">
              <Snowflake className="size-5" />
            </span>
            <div className="min-w-0 flex-1">
              <div className="font-medium">{t("freeze")}</div>
              <div className="text-xs text-muted-foreground">{t("freezeSub")}</div>
            </div>
            <ChevronRight className="size-4 text-muted-foreground" />
          </Panel>
        </Link>
      </main>
    </>
  );
}

function MotionPayment({ p }: { p: Payment }) {
  const t = useTranslations("parent.home");
  const tp = useTranslations("payment");
  return (
    <Link href={`/parent/payments/${p.id}`} className="block">
      <Panel className="p-4 transition-colors hover:bg-accent/40">
        <div className="mb-1 flex items-center justify-between">
          <h2 className="text-sm font-semibold">{t("tuition")}</h2>
          <Pill tone={paymentTone(p)} dot pulse={["executing", "sent"].includes(p.status)}>
            {tp(`status.${p.status}`)}
          </Pill>
        </div>
        <MoneyPath state={paymentPath(p)} from={{ place: "Đà Nẵng", sub: "Lotus Home Bank" }} to={{ place: "Seoul", sub: "Hanbit University" }} />
      </Panel>
    </Link>
  );
}

function MotionRefund({ refund }: { refund: Refund }) {
  const t = useTranslations("parent.home");
  const tr = useTranslations("refund");
  const f = useFormat();
  const done = refund.status === "received" || refund.status === "reconciled";
  const story = useRefundStory(refund);
  const back = story.statement?.receivedBack;
  return (
    <Link href={`/parent/refunds/${refund.id}`} className="block">
      <Panel className="p-4 transition-colors hover:bg-accent/40">
        <div className="mb-1 flex items-center justify-between">
          <h2 className="flex items-center gap-1.5 text-sm font-semibold">
            <Undo2 className="size-4" /> {t("refund")}
          </h2>
          <Pill tone={done ? "verified" : "attention"} dot pulse={!done}>
            {tr(`status.${refund.status}`)}
          </Pill>
        </div>
        <MoneyPath state={refundPath(refund)} from={{ place: "Đà Nẵng", sub: "Lotus Home Bank" }} to={{ place: "Seoul", sub: "Hanbit University" }} />
        {done && back ? (
          <p className="mt-2 font-display text-lg font-medium tnum">{tr("backAmount", { amount: f.money(back) })}</p>
        ) : back ? (
          <p className="mt-2 text-sm text-pretty text-muted-foreground tnum">
            {tr("hero.estimate", { amount: f.money(back) })}
            {refund.deadline && <> · {tr("when.promise", { date: f.date(refund.deadline) })}</>}
          </p>
        ) : refund.status === "manual_review" ? (
          <p className="mt-2 text-sm text-pretty text-muted-foreground">{tr("hero.manual")}</p>
        ) : null}
      </Panel>
    </Link>
  );
}

