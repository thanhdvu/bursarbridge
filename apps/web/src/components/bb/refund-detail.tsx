"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useFormat } from "@/lib/format";
import { refundPhase, useRefundStory } from "@/lib/refund";
import { refundSteps } from "@/lib/status";
import type { Refund } from "@/lib/api/types";
import { MockBadge } from "./badges";
import { OverdueRefund } from "./plan";
import { RefundForms, RefundSummary, useRefund } from "./cards";
import { CheckRow, Line, Panel, SectionLabel } from "./primitives";
import { AppHeader } from "./shell";
import { Timeline } from "./timeline";

const DAY = 86_400_000;

/** When each step happens, from the API's simulated bursar: ack +1d, approve +3d, wire 2 days before the promise, back by the promise. */
function stepDate(r: Refund, step: Refund["status"], requestedAt?: string) {
  const done = r.timeline.find((x) => x.code === `refund_${step}`)?.at;
  if (done) return { at: done, planned: false };
  if (!requestedAt || !r.deadline) return null;
  const t0 = Date.parse(requestedAt);
  const promise = Date.parse(r.deadline);
  const at = step === "acknowledged" ? t0 + DAY : step === "approved" ? t0 + 3 * DAY : step === "sent" ? promise - 2 * DAY : step === "received" ? promise : null;
  return at ? { at: new Date(at).toISOString(), planned: true } : null;
}

export function RefundDetail({ id, back }: { id: string; back: string }) {
  const t = useTranslations("refund");
  const f = useFormat();
  const q = useRefund(id);
  const r = q.data;
  const story = useRefundStory(r);
  const header = (
    <AppHeader
      left={
        <Link href={back} aria-label={t("back")} className="-ml-2 grid size-9 place-items-center rounded-full hover:bg-accent">
          <ArrowLeft className="size-5" />
        </Link>
      }
    />
  );
  if (!r)
    return (
      <>
        {header}
        <div className="m-4 h-60 animate-pulse rounded-2xl bg-muted" />
      </>
    );
  const phase = refundPhase(r);
  const rec = story.statement;
  const idx = r.status === "reconciled" ? refundSteps.length - 1 : refundSteps.indexOf(r.status);
  const pct = rec && story.less !== null ? (story.less / Number(rec.sentOut.amount)) * 100 : 0;
  return (
    <>
      {header}
      <main className="flex-1 space-y-5 px-4 pb-8">
        <OverdueRefund refund={r} />
        <Panel className="p-4">
          <RefundSummary refund={r} showStatementLink={false} />
        </Panel>

        {rec && (
          <section id="statement" className="scroll-mt-20">
            <SectionLabel action={!story.actual ? <MockBadge what="bank" /> : undefined}>{t("statement")}</SectionLabel>
            <Panel className="p-4">
              <Line label={t("sentOut")} value={f.money(rec.sentOut)} />
              <div className="my-1 border-l-2 border-dashed pl-3">
                {rec.lines.map((l) => (
                  <Line
                    key={l.code}
                    label={t.has(`lines.${l.code}` as never) ? t(`lines.${l.code}` as never) : l.code.replaceAll("_", " ").toLowerCase()}
                    hint={t.has(`hints.${l.code}` as never) ? t(`hints.${l.code}` as "hints.FX_MOVEMENT_MOCK", { pct: rec.conversion?.lossPct ? f.number(Number(rec.conversion.lossPct), 0) : "2" }) : (l.clause ?? undefined)}
                    value={
                      Number(l.amount.amount) === 0 ? (
                        <span className="text-verified-ink">{f.money(0, l.amount.currency)}</span>
                      ) : (
                        <span className="text-blocked-ink">{f.money(-Math.abs(Number(l.amount.amount)), l.amount.currency, { sign: true })}</span>
                      )
                    }
                    muted
                  />
                ))}
              </div>
              <Line label={story.actual ? t("receivedBack") : t("expectedBack")} value={f.money(rec.receivedBack)} strong className="border-t pt-2" />
              <p className="mt-2 rounded-lg bg-subtle px-3 py-2 text-xs leading-relaxed text-pretty text-muted-foreground">
                {t(story.actual ? "lossNote" : "lossNoteEstimate", { pct: f.number(pct, 1) })}
              </p>
              <p className="mt-2 px-1 text-xs leading-relaxed text-pretty text-muted-foreground">{t("separateNote")}</p>
            </Panel>
          </section>
        )}

        {(r.paperwork || story.approval) && (
          <section>
            <SectionLabel>{t("paperwork")}</SectionLabel>
            <Panel className="px-4 py-1.5">
              <RefundForms refund={r} approval={story.approval} />
            </Panel>
            <p className="mt-1.5 px-1 text-[11px] text-muted-foreground">{t("forms.note")}</p>
          </section>
        )}

        {phase !== "manual" && (
          <section>
            <SectionLabel>{t("progress")}</SectionLabel>
            <Panel className="p-4">
              {refundSteps.map((s, i) => {
                const when = stepDate(r, s, story.requestedAt);
                return (
                  <CheckRow
                    key={s}
                    state={idx >= i ? "ok" : idx + 1 === i ? "running" : "pending"}
                    title={t(`steps.${s}` as never)}
                    right={when ? <span className="shrink-0 text-xs text-muted-foreground tnum">{when.planned ? t("eta", { date: f.date(when.at, "short") }) : f.date(when.at, "short")}</span> : undefined}
                    className="py-1.5"
                  />
                );
              })}
            </Panel>
          </section>
        )}

        <section>
          <SectionLabel>{t("history")}</SectionLabel>
          <Panel className="p-4">
            <Timeline events={r.timeline} />
          </Panel>
        </section>
      </main>
    </>
  );
}
