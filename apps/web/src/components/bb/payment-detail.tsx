"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Bot } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { useSimClock } from "@/lib/clock";
import { plainName, useFormat } from "@/lib/format";
import { usePersona } from "@/lib/persona";
import { usePayment } from "@/lib/queries";
import { paymentPath, paymentTone } from "@/lib/status";
import { MockBadge, Pill } from "./badges";
import { PayeeChecks } from "./cards";
import { HashChip } from "./hash";
import { MoneyPath } from "./money-path";
import { CheckRow, Line, Panel, SectionLabel } from "./primitives";
import { AppHeader } from "./shell";
import { Timeline } from "./timeline";

export function PaymentDetail({ id, back }: { id: string; back: string }) {
  const t = useTranslations("payment");
  const f = useFormat();
  const q = usePayment(id);
  const { client, user } = usePersona();
  const qc = useQueryClient();
  const { nowMs } = useSimClock();
  const p = q.data;
  // The cancel window comes from the approval's disclosure when the payment itself does not carry it (live API).
  const approval = useQuery({
    queryKey: ["approval", user?.id, p?.approvalId],
    queryFn: () => client.approvals.get(p!.approvalId!),
    enabled: !!p?.approvalId && !p?.cancelUntil,
  });
  const cancelUntil = p?.cancelUntil ?? approval.data?.disclosure?.cancelUntil;
  const header = (
    <AppHeader
      left={
        <Link href={back} aria-label={t("back")} className="-ml-2 grid size-9 place-items-center rounded-full hover:bg-accent">
          <ArrowLeft className="size-5" />
        </Link>
      }
    />
  );
  if (!p)
    return (
      <>
        {header}
        <div className="m-4 h-60 animate-pulse rounded-2xl bg-muted" />
      </>
    );
  const total = Number(p.send.amount);
  const canCancel =
    user?.role === "parent" && cancelUntil && nowMs < Date.parse(cancelUntil) && !["cancelled", "failed"].includes(p.status);
  const steps = ["executing", "sent", "received_by_bursar", "matched"] as const;
  const idx = steps.indexOf(p.status as (typeof steps)[number]);
  const rent = p.purpose === "rent";
  return (
    <>
      {header}
      <main className="flex-1 space-y-5 px-4 pb-8">
        <section className="px-1">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">{t(`purpose.${p.purpose ?? "tuition"}`)}</span>
            <Pill tone={paymentTone(p)} dot pulse={["executing", "sent"].includes(p.status)}>
              {t(`status.${p.status}`)}
            </Pill>
          </div>
          <div className="mt-2 text-[30px] leading-none font-semibold tracking-tight tnum">{f.money(p.receive)}</div>
          <div className="mt-1 text-sm text-muted-foreground">
            {t("to", { payee: rent ? p.payee.name : plainName(p.payee.institution) })} · {t("paid", { amount: f.money(total, p.send.currency) })}
          </div>
          {p.autoExecuted && (
            <div className="mt-3 flex items-start gap-2 rounded-xl bg-route-soft px-3 py-2.5 text-sm text-route-ink">
              <Bot className="mt-0.5 size-4 shrink-0" />
              <span>{t("autoExplain")}</span>
            </div>
          )}
        </section>

        <Panel className="p-4">
          <MoneyPath
            state={paymentPath(p)}
            from={{ place: p.send.currency === "CNY" ? "Chengdu" : "Đà Nẵng", sub: "Lotus Home Bank" }}
            to={{ place: "Seoul", sub: rent ? p.payee.name : plainName(p.payee.institution) }}
          />
          {p.status !== "cancelled" ? (
            <div className="mt-4">
              {steps
                .filter((s) => !(rent && s === "received_by_bursar"))
                .map((s) => {
                  const i = steps.indexOf(s);
                  return <CheckRow key={s} state={idx >= i ? "ok" : idx + 1 === i ? "running" : "pending"} title={t(`step.${s}`)} className="py-1.5" />;
                })}
            </div>
          ) : (
            <p className="mt-3 text-sm text-muted-foreground">{t("cancelledBody")}</p>
          )}
          {canCancel && (
            <Button
              variant="outline"
              className="mt-3 h-11 w-full rounded-xl"
              onClick={async () => {
                if (!confirm(t("cancelConfirm"))) return;
                await client.payments.cancel(p.id);
                qc.invalidateQueries();
              }}
            >
              {t("cancel", { m: Math.ceil((Date.parse(cancelUntil!) - nowMs) / 60000) })}
            </Button>
          )}
        </Panel>

        <section>
          <SectionLabel>{t("amounts")}</SectionLabel>
          <Panel className="p-4">
            {p.fees && <Line label={t("debited")} value={f.money(Number(p.send.amount) - Number(p.fees.amount), p.send.currency)} muted />}
            {p.fees && <Line label={t("fees")} value={f.money(p.fees)} muted />}
            <Line label={t("total")} value={f.money(total, p.send.currency)} strong />
            <Line label={t("received")} value={f.money(p.receive)} strong />
            <Line label={t("reference")} value={<span className="font-mono text-xs">{p.invoiceRef}</span>} muted />
            {p.chainTx && (
              <Line
                label={
                  <span className="inline-flex items-center gap-1.5">
                    {t("evidence", { n: p.chainTx.blockNumber })} <MockBadge what="chain" />
                  </span>
                }
                value={<HashChip value={p.chainTx.txHash} />}
                muted
              />
            )}
          </Panel>
        </section>

        <section>
          <SectionLabel>{t("payee")}</SectionLabel>
          <Panel className="p-4">
            <PayeeChecks payee={p.payee} compact />
          </Panel>
        </section>

        <section>
          <SectionLabel>{t("history")}</SectionLabel>
          <Panel className="p-4">
            <Timeline events={p.timeline} />
          </Panel>
        </section>
      </main>
    </>
  );
}
