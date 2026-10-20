"use client";

import { useTranslations } from "next-intl";
import { AcademicJourney, AdmissionNotice } from "@/components/bb/study-progress";
import { RefundCard } from "@/components/bb/cards";
import { Panel, SectionLabel } from "@/components/bb/primitives";
import { PaymentRow } from "@/components/bb/rows";
import { AppHeader, LocaleSwitcher, ThemeToggle } from "@/components/bb/shell";
import { Timeline } from "@/components/bb/timeline";
import { usePayments, useRefunds } from "@/lib/queries";
import { ObligationsCard, PaymentWindowLine, useStudyPlan } from "@/components/bb/plan";
import { DemoToday } from "@/components/bb/shell";

export default function StudentTimeline() {
  const t = useTranslations("student.timeline");
  const payments = usePayments();
  const refunds = useRefunds();
  const plan = useStudyPlan();
  const events = [...(payments.data ?? []).flatMap((p) => p.timeline), ...(refunds.data ?? []).flatMap((r) => r.timeline)];
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
        {plan.data && (
          <Panel className="space-y-1.5 p-4">
            <DemoToday className="-ml-1" />
            <PaymentWindowLine plan={plan.data} />
          </Panel>
        )}
        <AdmissionNotice />
        <AcademicJourney plan={plan.data} />
        {!events.length && !payments.isLoading && <p className="py-16 text-center text-sm text-pretty text-muted-foreground">{t("empty")}</p>}
        {refunds.data?.map((r) => <RefundCard key={r.id} data={{ refundId: r.id }} />)}
        {!!payments.data?.length && (
          <section>
            <SectionLabel>{t("payments")}</SectionLabel>
            <Panel className="divide-y">
              {payments.data.map((p) => (
                <PaymentRow key={p.id} p={p} base="/student" />
              ))}
            </Panel>
          </section>
        )}
        <ObligationsCard plan={plan.data} />
        {!!events.length && (
          <section>
            <SectionLabel>{t("everything")}</SectionLabel>
            <Panel className="p-4">
              <Timeline events={events} />
            </Panel>
          </section>
        )}
      </main>
    </>
  );
}
