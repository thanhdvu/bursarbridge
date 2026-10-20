"use client";

import { FileCheck2, OctagonX, Undo2 } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Pill } from "@/components/bb/badges";
import { Panel, SectionLabel } from "@/components/bb/primitives";
import { PaymentRow } from "@/components/bb/rows";
import { AppHeader, LocaleSwitcher, ThemeToggle } from "@/components/bb/shell";
import { useFormat } from "@/lib/format";
import { useApprovals, useAudit, usePayments, useRefunds } from "@/lib/queries";

export default function ActivityPage() {
  const t = useTranslations("parent.activity");
  const tr = useTranslations("refund");
  const ta = useTranslations("cards.approval");
  const f = useFormat();
  const payments = usePayments();
  const refunds = useRefunds();
  const approvals = useApprovals("all");
  const audit = useAudit();
  const blocked = (audit.data?.entries ?? []).filter((e) => e.kind === "policy.disposition" && e.summary.startsWith("DENY")).reverse();
  const empty = !payments.data?.length && !refunds.data?.length && !approvals.data?.length && !blocked.length;

  return (
    <>
      <AppHeader
        left={<h1 className="text-lg font-semibold tracking-tight">{t("title")}</h1>}
        right={
          <>
            <LocaleSwitcher compact />
            <ThemeToggle />
          </>
        }
      />
      <main className="flex-1 space-y-6 px-4 pt-2 pb-8">
        {empty && !payments.isLoading && <p className="py-16 text-center text-sm text-muted-foreground">{t("empty")}</p>}

        {!!refunds.data?.length && (
          <section>
            <SectionLabel>{t("refunds")}</SectionLabel>
            <Panel className="divide-y">
              {refunds.data.map((r) => (
                <Link key={r.id} href={`/parent/refunds/${r.id}`} className="flex items-center gap-3 px-4 py-3 hover:bg-accent/50">
                  <span className="grid size-9 place-items-center rounded-full bg-attention-soft text-attention-ink">
                    <Undo2 className="size-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium">{tr("title")}</div>
                    <div className="text-xs text-muted-foreground">{(r.createdAt ?? r.timeline[0]?.at) ? f.date((r.createdAt ?? r.timeline[0]?.at)!, "short") : ""}</div>
                  </div>
                  <Pill tone={r.status === "reconciled" || r.status === "received" ? "verified" : "attention"}>{tr(`status.${r.status}`)}</Pill>
                </Link>
              ))}
            </Panel>
          </section>
        )}

        {!!payments.data?.length && (
          <section>
            <SectionLabel>{t("payments")}</SectionLabel>
            <Panel className="divide-y">
              {payments.data.map((p) => (
                <PaymentRow key={p.id} p={p} />
              ))}
            </Panel>
          </section>
        )}

        {!!approvals.data?.length && (
          <section>
            <SectionLabel>{t("approvals")}</SectionLabel>
            <Panel className="divide-y">
              {approvals.data.map((a) => (
                <Link key={a.id} href={a.action === "refund_claim" ? "#" : `/parent/approvals/${a.id}`} className="flex items-center gap-3 px-4 py-3 hover:bg-accent/50">
                  <span className="grid size-9 place-items-center rounded-full bg-secondary">
                    <FileCheck2 className="size-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium">{ta(`title.${a.action}`)}</div>
                    <div className="text-xs text-muted-foreground">{f.date(a.createdAt, "datetime")}</div>
                  </div>
                  <Pill tone={a.status === "approved" ? "verified" : a.status === "pending" ? "attention" : "neutral"}>{ta(`status.${a.status}`)}</Pill>
                </Link>
              ))}
            </Panel>
          </section>
        )}

        {!!blocked.length && (
          <section>
            <SectionLabel>{t("blocked")}</SectionLabel>
            <Panel className="divide-y">
              {blocked.map((e) => (
                <div key={e.seq} className="flex items-start gap-3 px-4 py-3">
                  <span className="grid size-9 shrink-0 place-items-center rounded-full bg-blocked-soft text-blocked-ink">
                    <OctagonX className="size-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium">{t(`blockedKind.${e.ruleIds.includes("LX-03") ? "redirect" : e.ruleIds.includes("PAY-02") ? "fakeInvoice" : "other"}`)}</div>
                    <div className="mt-0.5 text-xs text-muted-foreground">
                      {f.date(e.at, "datetime")} ·{" "}
                      <Link href={`/trust?seq=${e.seq}`} className="font-mono hover:underline">
                        #{e.seq}
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </Panel>
          </section>
        )}
      </main>
    </>
  );
}
