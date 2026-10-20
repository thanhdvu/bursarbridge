"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Check, Circle, Hourglass, ListChecks, PhoneCall, ShieldAlert, Snowflake } from "lucide-react";
import { motion } from "motion/react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useErrorToast } from "@/lib/errors";
import { useFormat } from "@/lib/format";
import { usePersona } from "@/lib/persona";
import { cn } from "@/lib/utils";
import type { Approval, Reason, User } from "@/lib/api/types";
import { AdmissionNotice, NeutralNeed } from "./study-progress";
import { Pill, RuleId } from "./badges";
import { Panel, ReasonList } from "./primitives";

// ---------------------------------------------------------------------------
// Who is who (actor ids from the API, mock ids are the same since round 2)

const STUDENTS = new Set(["usr_student_linh", "usr_student_hao"]);
const PARENTS = new Set(["usr_parent_minh", "usr_parent_wang"]);

function useWho() {
  const t = useTranslations("rel");
  const { user } = usePersona();
  return (actorId: string) => {
    if (actorId === user?.id) return null;
    if (PARENTS.has(actorId)) return user?.role === "student" ? t("parent") : actorId === "usr_parent_wang" ? "Wang" : "Minh";
    if (STUDENTS.has(actorId)) return actorId === "usr_student_hao" ? "Hao" : t("student");
    if (actorId === "usr_mother_lan") return "Lan";
    return actorId;
  };
}

// ---------------------------------------------------------------------------
// Needs: neutral, actionable prerequisites (API v1.4 `card.kind = "needs"`)

interface NeedsData {
  /** v1.13: e.g. STUDENT_REFUND_REQUEST_REQUIRED, PAYMENT_SETTLEMENT_REQUIRED, REFUSAL_DOCUMENT_REQUIRED. */
  code?: string;
  missing?: { kind: string; actorId: string; action: "upload" | "sign" | "upload_and_sign" | "wait" | "create_and_sign" }[];
  reasons?: Reason[];
  ruleIds?: string[];
}

export function NeedsCard({ data }: { data: Record<string, unknown> }) {
  const t = useTranslations("needs");
  const who = useWho();
  const { user, client, persona } = usePersona();
  const d = data as NeedsData;
  const missing = d.missing ?? [];
  const known = ["mandate", "rent_mandate", "admission", "invoice", "refusal", "refusal_and_refund_forms", "payment_settlement", "rental_agreement"];
  const rentCase = d.code === "RENT_PREREQUISITES_REQUIRED";
  const refundCase = d.code === "STUDENT_REFUND_REQUEST_REQUIRED" || missing.some((m) => m.kind === "refusal_and_refund_forms");
  // The card stays live: each step ticks off once it is done anywhere in the family.
  const mandates = useQuery({ queryKey: ["mandates", persona], queryFn: () => client.mandates.list() });
  const docs = useQuery({ queryKey: ["documents", persona], queryFn: () => client.documents.list() });
  const refunds = useQuery({ queryKey: ["refunds", persona], queryFn: () => client.refunds.list(), enabled: refundCase });
  const isDone = (m: { kind: string }) =>
    m.kind === "mandate" || m.kind === "rent_mandate"
      ? !!mandates.data?.some((x) => x.status === "active" && x.purpose === (m.kind === "mandate" ? "tuition" : "rent"))
      : m.kind === "refusal_and_refund_forms"
        ? !!refunds.data?.length
        : m.kind === "payment_settlement"
          ? !!payments.data?.some((x) => x.purpose !== "rent" && x.status === "matched")
          : !!docs.data?.some((x) => x.kind === m.kind);
  const pending = useQuery({ queryKey: ["approvals", persona, "pending"], queryFn: () => client.approvals.list("pending") });
  const payments = useQuery({ queryKey: ["payments", persona], queryFn: () => client.payments.list() });
  // Offer "continue" only while nothing has been prepared yet (older cards in the thread go quiet once it is).
  const rent = missing.every((m) => m.kind === "rent_mandate");
  const prepared = rent
    ? !!payments.data?.some((x) => x.purpose === "rent")
    : !!pending.data?.some((x) => (x.action === "payment" || x.action === "first_payment") && x.rawAction?.purpose !== "verify_scam_claim") || !!payments.data?.some((x) => x.purpose !== "rent");
  const everyDone = missing.length > 0 && missing.every(isDone);
  if (d.code === "VISA_REFUSED_BEFORE_PAYMENT") return <AdmissionNotice disposition={data.admissionDisposition as import("@/lib/api/types").AdmissionDisposition} />;
  if (["CHAIN_UNAVAILABLE", "CHAIN_REGISTRATION_PENDING", "DEMO_SEED_REFRESH_REQUIRED", "REGISTRATION_WINDOW_REQUIRED", "ADMISSION_RECONFIRMATION_REQUIRED", "PAYMENT_WINDOW_NOT_OPEN", "PAYMENT_WINDOW_CLOSED"].includes(d.code ?? "")) return <NeutralNeed code={d.code!} />;
  return (
    <motion.article initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="overflow-hidden rounded-2xl border bg-card shadow-card">
      <div className="flex items-start gap-3 px-4 pt-4">
        <span className={cn("grid size-9 shrink-0 place-items-center rounded-full transition-colors", everyDone ? "bg-verified text-white" : "bg-route-soft text-route-ink")}>
          {everyDone ? <Check className="size-[18px]" strokeWidth={3} /> : <ListChecks className="size-[18px]" />}
        </span>
        <div>
          <h3 className="font-semibold">{everyDone ? t("doneTitle") : refundCase ? t("refundTitle") : rentCase ? t("rentTitle") : t("title")}</h3>
          <p className="text-sm text-pretty text-muted-foreground">{everyDone ? (refundCase ? t("refundDone") : prepared ? t("doneBody") : t("doneBodyWaiting")) : refundCase ? t("refundBody") : t("body")}</p>
        </div>
      </div>
      <ol className="mt-3 divide-y border-t">
        {missing.map((m, i) => {
          const name = who(m.actorId);
          const kind = known.includes(m.kind) ? m.kind : "other";
          const mine = name === null;
          const done = isDone(m);
          const label = mine ? t(`you.${kind}` as never) : t(`other.${kind}` as "other.mandate", { who: name ?? "" });
          return (
            <li key={`${m.kind}-${i}`} className="flex items-center gap-3 px-4 py-3">
              {done ? (
                <span className="grid size-[18px] shrink-0 place-items-center rounded-full bg-verified text-white">
                  <Check className="size-3" strokeWidth={3} />
                </span>
              ) : (
                <Circle className={cn("size-[18px] shrink-0", mine ? "text-route" : "text-muted-foreground/50")} strokeWidth={2} />
              )}
              <span className={cn("min-w-0 flex-1 text-sm font-medium text-pretty", done && "text-muted-foreground")}>{label}</span>
              {done ? (
                <Pill tone="verified" className="shrink-0">
                  {t("done")}
                </Pill>
              ) : mine ? (
                (m.action === "sign" || m.action === "create_and_sign") && user?.role === "parent" ? (
                  <Button asChild size="sm" className="h-8 rounded-lg">
                    <Link href={m.kind === "rent_mandate" ? "/parent/mandate/new?purpose=rent" : "/parent/mandate/new"}>
                      {t("ctaSign")} <ArrowRight className="size-3.5" />
                    </Link>
                  </Button>
                ) : m.action === "upload" || m.action === "upload_and_sign" ? (
                  <Button
                    size="sm"
                    className="h-8 rounded-lg"
                    onClick={() =>
                      window.dispatchEvent(
                        new CustomEvent("bb-open-tray", {
                          detail: { kinds: missing.filter((x) => (x.action === "upload" || x.action === "upload_and_sign") && who(x.actorId) === null).map((x) => (x.kind === "refusal_and_refund_forms" ? "refusal" : x.kind)) },
                        }),
                      )
                    }
                  >
                    {t("ctaUpload")}
                  </Button>
                ) : null
              ) : (
                <Pill tone="neutral" className="shrink-0">
                  {t("asked")}
                </Pill>
              )}
            </li>
          );
        })}
      </ol>
      {!!(d.reasons?.length || d.ruleIds?.length) && (
        <div className="flex flex-wrap gap-1 border-t px-4 py-2.5">
          {(d.reasons?.map((r) => r.ruleId) ?? d.ruleIds ?? []).map((id) => (
            <RuleId key={id} id={id} />
          ))}
        </div>
      )}
    </motion.article>
  );
}

// ---------------------------------------------------------------------------
// Scam cooling-off review (API v1.2 `status = "cooling_off"`, co-signed by Lan)

/** API r5: `cosigned` is public and persisted, so every phone sees Lan's check. */
export function wasCosigned(a: Approval) {
  return !!a.cosigned;
}

export function useCoolingReviews() {
  const { client, persona } = usePersona();
  return useQuery({ queryKey: ["approvals", persona, "cooling_off"], queryFn: () => client.approvals.list("cooling_off") });
}

function RiskMeter({ score }: { score: number }) {
  const t = useTranslations("cooling");
  const k = Math.min(1, score / 16);
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-muted" aria-hidden>
        <motion.div className="h-full rounded-full bg-attention" initial={{ width: 0 }} animate={{ width: `${k * 100}%` }} transition={{ duration: 0.8 }} />
      </div>
      <span className="text-xs text-muted-foreground tnum">{t("score", { score })}</span>
    </div>
  );
}

/** Compact review card used inside the parent and student apps. */
export function CoolingCard({ approval, viewer }: { approval: Approval; viewer?: User }) {
  const t = useTranslations("cooling");
  const f = useFormat();
  const { client } = usePersona();
  const qc = useQueryClient();
  const showError = useErrorToast();
  const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const isParent = viewer?.role === "parent";
  const closed = approval.status === "rejected";
  const checked = wasCosigned(approval);
  return (
    <Panel className="overflow-hidden border-attention/40">
      <div className="flex items-start gap-3 bg-attention-soft px-4 py-3.5 text-attention-ink">
        <span className="grid size-9 shrink-0 place-items-center rounded-full bg-attention text-white">
          <Snowflake className="size-[18px]" />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold">{viewer?.role === "student" ? t("studentTitle") : t("parentTitle")}</h3>
          {approval.cooling && !closed && (
            <p className="mt-0.5 flex items-center gap-1.5 text-xs opacity-90">
              <Hourglass className="size-3.5" />
              {t("until", { time: f.date(approval.cooling.until, "datetime") })}
            </p>
          )}
        </div>
        {closed && (
          <Pill tone="neutral" className="shrink-0 bg-card/60">
            {t("closed").split(".")[0]}
          </Pill>
        )}
      </div>
      <div className="space-y-3 p-4">
        <p className="text-sm leading-relaxed text-pretty">{viewer?.role === "student" ? t("studentBody") : t("parentBody")}</p>
        <RiskMeter score={approval.risk.score} />
        {!closed && (
          <div className={cn("flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm", checked ? "bg-verified-soft text-verified-ink" : "bg-subtle text-muted-foreground")}>
            {checked ? <Check className="size-4" /> : <PhoneCall className="size-4" />}
            {viewer?.role === "student" ? (checked ? t("lanCheckedStudent") : t("waitingLanStudent")) : checked ? t("lanChecked") : t("waitingLan")}
          </div>
        )}
        {isParent && !closed && confirming && <p className="text-center text-sm text-pretty text-muted-foreground">{t("closeConfirm")}</p>}
        {isParent && !closed && (
          <Button
            variant={confirming ? "default" : "outline"}
            className="h-11 w-full rounded-xl"
            disabled={busy}
            onClick={async () => {
              // Two taps instead of a browser confirm(): calmer on a phone, and still deliberate.
              if (!confirming) {
                setConfirming(true);
                return;
              }
              setBusy(true);
              try {
                await client.approvals.reject(approval.id, "verified_scam");
                toast(t("closed"));
                qc.invalidateQueries();
              } catch (e) {
                showError(e);
              } finally {
                setBusy(false);
              }
            }}
          >
            {confirming ? t("closeYes") : t("close")}
          </Button>
        )}
      </div>
    </Panel>
  );
}

export function CoolingReasons({ features }: { features: Reason[] }) {
  return <ReasonList reasons={features.map((x) => ({ ...x, severity: "warn" as const }))} />;
}

export function ShieldIcon({ className }: { className?: string }) {
  return <ShieldAlert className={className} />;
}
