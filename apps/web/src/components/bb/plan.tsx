"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarClock, ExternalLink, FileWarning, HeartPulse, Home, Mail, ShieldCheck } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { Approval, Refund, StudyPlan } from "@/lib/api/types";
import { useErrorToast } from "@/lib/errors";
import { plainName, useFormat } from "@/lib/format";
import { usePersona } from "@/lib/persona";
import { openPaperwork } from "@/lib/refund";
import { cn } from "@/lib/utils";
import { MockBadge, Pill } from "./badges";
import { PasskeySheet } from "./passkey";
import { Panel, SectionLabel } from "./primitives";

export function useStudyPlan() {
  const { client, persona } = usePersona();
  return useQuery({ queryKey: ["study-plan", persona], queryFn: () => client.studyPlan(), retry: false, staleTime: 15_000 });
}

/** A Korea-time deadline shown in Korea time ("17:00, 15 Jan"), because that is the clock the school uses. */
function seoulTime(iso: string, locale: string) {
  const tag = { vi: "vi-VN", ko: "ko-KR", zh: "zh-CN", en: "en-GB" }[locale] ?? "en-GB";
  return new Intl.DateTimeFormat(tag, { hour: "2-digit", minute: "2-digit", day: "numeric", month: "short", timeZone: "Asia/Seoul" }).format(new Date(iso));
}

/** "12–15 Jan 2027" in the app's language, from a window that opens and closes in Korea time. */
function useWindowText() {
  const f = useFormat();
  return (w: { opensAt: string; closesAt: string }) => `${f.date(w.opensAt, "short")} – ${f.date(w.closesAt)}`;
}

/**
 * Where the family stands in time: the demo's simulated today, Hanbit's registration (payment) window
 * and whether it is open now. Every countdown elsewhere is measured from this "today".
 */
export function PaymentWindowLine({ plan, className }: { plan?: StudyPlan; className?: string }) {
  const t = useTranslations("plan");
  const win = useWindowText();
  const f = useFormat();
  const w = plan?.currentPaymentWindow ?? plan?.registrationWindow;
  if (!plan || !w) return null;
  const status = plan.paymentWindowStatus ?? "legacy_unspecified";
  const tone = status === "open" ? "verified" : status === "settled" ? "neutral" : status === "closed" ? "blocked" : "attention";
  return (
    <div className={cn("flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground", className)}>
      <CalendarClock className="size-3.5 shrink-0" />
      <span>{t("window", { range: win(w) })}</span>
      <Pill tone={tone as "verified"} className="h-5 px-2 text-[11px]">
        {t.has(`status.${status}` as never) ? t(`status.${status}` as never) : status}
      </Pill>
      {plan.dueAt && status !== "settled" && <span className="tnum">{t("due", { date: seoulTime(plan.dueAt, f.locale) })}</span>}
    </div>
  );
}

/** Dorm and health insurance: real costs of the semester that BursarBridge does not pay, with who collects them and when. */
export function ObligationsCard({ plan }: { plan?: StudyPlan }) {
  const t = useTranslations("plan");
  const f = useFormat();
  const items = plan?.separateObligations?.filter((o) => o.applicable) ?? [];
  if (!items.length) return null;
  return (
    <section>
      <SectionLabel>{t("otherCosts")}</SectionLabel>
      <Panel className="divide-y px-4">
        {items.map((o) => (
          <div key={o.id} className="flex items-start gap-3 py-3">
            <span className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-lg bg-subtle text-muted-foreground">
              {o.id === "health_insurance" ? <HeartPulse className="size-4" /> : <Home className="size-4" />}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-sm font-medium">{o.label}</span>
                <span className="shrink-0 text-sm tnum">
                  {f.money(o.amount)}
                  {o.period === "monthly" ? t("perMonth") : ""}
                </span>
              </div>
              <div className="mt-0.5 text-xs leading-relaxed text-pretty text-muted-foreground">
                {t("collector", { who: o.id === "health_insurance" ? t("nhis") : o.id === "dorm" ? t("dormOffice") : plainName(o.collector) })} · {o.when}
              </div>
              {o.refundPolicy && <div className="mt-0.5 text-xs leading-relaxed text-pretty text-muted-foreground">{o.refundPolicy}</div>}
              <div className="mt-1 flex flex-wrap items-center gap-1.5 text-[11px] text-muted-foreground">
                <Pill tone="neutral" className="h-5 px-2 text-[11px]">
                  {t("notThroughUs")}
                </Pill>
                {o.source && <span className="text-pretty">{o.source}</span>}
                <MockBadge what="generic" />
              </div>
            </div>
          </div>
        ))}
      </Panel>
    </section>
  );
}

/**
 * A missed refund promise never goes quiet: the dated chaser the student approves (MOCK outbox only),
 * then, if that stalls too, the complaint pack for the official route. Nothing is sent automatically.
 */
export function OverdueRefund({ refund }: { refund: Refund }) {
  const t = useTranslations("overdue");
  const f = useFormat();
  const { client, user } = usePersona();
  const showError = useErrorToast();
  const fu = refund.followUp;
  if (!fu?.overdue) return null;
  const esc = fu.escalation;
  const pack = fu.complaintPack;
  const student = user?.familyId === "fam_wang" ? "Hao" : "Linh";
  return (
    <Panel className="overflow-hidden border-attention/40">
      <div className="flex items-start gap-3 bg-attention-soft px-4 py-3 text-attention-ink">
        <FileWarning className="mt-0.5 size-5 shrink-0" />
        <div className="min-w-0">
          <div className="font-semibold text-pretty">{t("title", { n: fu.daysOverdue ?? 0 })}</div>
          {fu.promiseAt && <div className="text-xs opacity-90">{t("promised", { date: f.date(fu.promiseAt) })}</div>}
        </div>
      </div>
      <ol className="divide-y px-4">
        <li className="flex items-start gap-3 py-3">
          <Mail className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
          <div className="min-w-0 flex-1 text-sm">
            <div className="font-medium">{t("chaser")}</div>
            <div className="text-xs text-pretty text-muted-foreground">
              {!esc
                ? t("chaserPreparing")
                : esc.status === "pending_approval"
                  ? user?.role === "student"
                    ? t("chaserYou")
                    : t("chaserWaiting", { who: student })
                  : esc.status === "submitted_MOCK"
                    ? t("chaserSent", { date: f.date(esc.submittedAt ?? esc.preparedAt), to: plainName(esc.recipient) })
                    : t("chaserClosed")}
            </div>
          </div>
          {esc?.downloadUrl && (
            <Button variant="outline" size="sm" className="h-8 shrink-0 rounded-lg" onClick={() => openPaperwork(() => client.pdf(esc.downloadUrl!), "letter.pdf").catch(showError)}>
              {t("view")}
            </Button>
          )}
        </li>
        {pack && (
          <li className="flex items-start gap-3 py-3">
            <ShieldCheck className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
            <div className="min-w-0 flex-1 text-sm">
              <div className="font-medium">{t("pack")}</div>
              <div className="text-xs text-pretty text-muted-foreground">
                {t("packSub", { route: pack.route?.name ?? "" })}
                {pack.route?.url && (
                  <a href={pack.route.url} target="_blank" rel="noreferrer" className="ml-1 inline-flex items-center gap-0.5 font-medium text-route-ink hover:underline">
                    {t("official")} <ExternalLink className="size-3" />
                  </a>
                )}
              </div>
            </div>
            {pack.downloadUrl && (
              <Button variant="outline" size="sm" className="h-8 shrink-0 rounded-lg" onClick={() => openPaperwork(() => client.pdf(pack.downloadUrl!), "complaint-pack.pdf").catch(showError)}>
                {t("view")}
              </Button>
            )}
          </li>
        )}
      </ol>
      <p className="border-t px-4 py-2.5 text-[11px] text-pretty text-muted-foreground">
        {t("honest")} <MockBadge what="bursar" />
      </p>
    </Panel>
  );
}

/** The dated chaser letter: the student reads it and approves it with her passkey; parents see it read-only. */
export function EscalationLetterCard({ approval: a }: { approval: Approval }) {
  const t = useTranslations("overdue");
  const f = useFormat();
  const { client, user } = usePersona();
  const qc = useQueryClient();
  const showError = useErrorToast();
  const [sheet, setSheet] = useState(false);
  const c = a.correspondence;
  const mine = a.approverId ? a.approverId === user?.id : user?.role === "student";
  return (
    <Panel className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-attention-soft text-attention-ink">
            <Mail className="size-5" />
          </span>
          <div>
            <h3 className="leading-snug font-semibold">{t("letterTitle")}</h3>
            {c && <p className="text-xs text-muted-foreground">{t("letterTo", { to: plainName(c.recipient) })}</p>}
          </div>
        </div>
        <Pill tone={a.status === "approved" ? "verified" : a.status === "pending" ? "attention" : "neutral"} dot>
          {a.status === "approved" ? t("sentMock") : a.status === "pending" ? t("waiting") : t("closed")}
        </Pill>
      </div>
      {c && (
        <div className="mt-3 space-y-1 rounded-xl bg-subtle px-3 py-2.5 text-sm">
          <p className="text-pretty">{c.summary}</p>
          <p className="text-xs text-muted-foreground">{t("letterFacts", { date: f.date(c.promiseAt), prepared: f.date(c.preparedAt) })}</p>
        </div>
      )}
      <div className="mt-3 flex items-center gap-2">
        {c?.downloadUrl && (
          <Button variant="outline" size="sm" className="h-9 rounded-lg" onClick={() => openPaperwork(() => client.pdf(c.downloadUrl!), "letter.pdf").catch(showError)}>
            {t("view")}
          </Button>
        )}
        {a.status === "pending" && mine && (
          <Button size="sm" className="h-9 flex-1 rounded-lg" onClick={() => setSheet(true)}>
            {t("approve")}
          </Button>
        )}
      </div>
      {a.status === "pending" && !mine && <p className="mt-2 text-xs text-muted-foreground">{t("studentApproves")}</p>}
      <PasskeySheet
        open={sheet}
        onOpenChange={setSheet}
        purpose="approval"
        refId={a.id}
        hash={a.consentHash}
        title={t("approve")}
        lines={[
          { label: t("to"), value: c ? plainName(c.recipient) : "" },
          { label: t("promise"), value: c ? f.date(c.promiseAt) : "" },
          { label: t("channel"), value: t("channelMock") },
        ]}
        onSigned={async (assertion) => {
          try {
            await client.approvals.approve(a.id, assertion);
            qc.invalidateQueries();
          } catch (e) {
            showError(e);
            throw e;
          }
        }}
      />
    </Panel>
  );
}
