"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import type { AdmissionDisposition, StudyPlan } from "@/lib/api/types";
import type { Client } from "@/lib/api/client";
import { usePersona } from "@/lib/persona";
import { useFormat } from "@/lib/format";
import { openPaperwork } from "@/lib/refund";
import { useErrorToast } from "@/lib/errors";
import { Button } from "@/components/ui/button";
import { MockBadge } from "./badges";
import { Panel } from "./primitives";

export function AdmissionNotice({ disposition }: { disposition?: AdmissionDisposition | null }) {
  const t = useTranslations("studyProgress");
  const { user } = usePersona();
  const f = useFormat();
  const d = disposition ?? user?.admissionDisposition;
  if (!d) return null;
  return <Panel className="space-y-2 p-4" role="status">
    <h2 className="font-semibold">{t("refusedTitle")}</h2>
    <p className="text-sm text-pretty">{t("moneySafe")}</p>
    <p className="text-sm text-pretty text-muted-foreground">{t("admissionNext")}</p>
    {d.parentNotice?.status === "available_in_family_app_MOCK" && <p className="text-xs text-pretty text-muted-foreground">{t("parentNotice", { date: f.date(d.parentNotice.at) })}</p>}
    <MockBadge what="generic" />
  </Panel>;
}

export function NeutralNeed({ code }: { code: string }) {
  const t = useTranslations("studyProgress");
  const chain = ["CHAIN_UNAVAILABLE", "CHAIN_REGISTRATION_PENDING"].includes(code);
  const admission = code === "ADMISSION_RECONFIRMATION_REQUIRED";
  return <Panel className="space-y-1 p-4" role="status">
    <h3 className="font-semibold">{t(chain ? "catchingUpTitle" : admission ? "newAdmissionTitle" : "windowTitle")}</h3>
    <p className="text-sm text-pretty text-muted-foreground">{t(chain ? "catchingUp" : admission ? "newAdmission" : "windowBody")}</p>
  </Panel>;
}

export function ChainCatchup() {
  const { client, persona } = usePersona();
  const t = useTranslations("studyProgress");
  const q = useQuery({ queryKey: ["chain-status", persona], queryFn: () => client.chain.status(), refetchInterval: query => query.state.data?.registrationStatus === "pending" || ["pending", "retrying"].includes(query.state.data?.anchorStatus ?? "") ? 5000 : false });
  const pending = q.data?.registrationStatus === "pending" || ["pending", "retrying"].includes(q.data?.anchorStatus ?? "");
  if (!pending) return null;
  return <div role="status" className="border-b bg-route-soft px-4 py-2 text-xs text-route-ink">{t("catchingUp")}</div>;
}

export function AcademicJourney({ plan, client: familyClient }: { plan?: StudyPlan; client?: Client }) {
  const t = useTranslations("studyProgress");
  const f = useFormat();
  const { client } = usePersona();
  const showError = useErrorToast();
  if (!plan?.academicTimeline) return null;
  const a = plan.academicTimeline;
  const certificate = plan.standardAdmissionCertificate;
  const reader = familyClient ?? client;
  const refused = plan.visaApplication?.status === "refusal_evidence_received_MOCK";
  return <Panel className="space-y-3 p-4">
    <h2 className="font-semibold">{t("journeyTitle")}</h2>
    <ol className="space-y-3 text-sm">
      {[[a.acceptedAt, "accepted"], [certificate?.issuedAt ?? a.certificateIssuedAt, "certificate"], [plan.visaApplication?.appliedAt ?? a.visaAppliedAt, "visaPending"], [plan.registrationWindow?.opensAt, "paymentWindow"]].map(([date, key]) => date && <li key={key} className="flex gap-3"><span className="w-24 shrink-0 text-xs text-muted-foreground">{f.date(date)}</span><span className="min-w-0 text-pretty">{t(key as "accepted")}</span></li>)}
    </ol>
    {refused && <p className="text-sm">{t("visaRefused")}</p>}
    <p className="text-xs text-pretty text-muted-foreground">{t("sequenceNote")}</p>
    {certificate?.status === "issued_MOCK" && certificate.downloadUrl && <Button variant="outline" size="sm" className="h-auto whitespace-normal py-2" onClick={() => openPaperwork(() => reader.pdf(certificate.downloadUrl!), "admission-certificate.pdf").catch(showError)}>{t("viewCertificate")}</Button>}
    <MockBadge what="generic" />
  </Panel>;
}
