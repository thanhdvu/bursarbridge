"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, ChevronDown, Hourglass, PhoneCall, ShieldCheck, Snowflake, UserRoundCheck } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { MockBadge, Pill } from "@/components/bb/badges";
import { PasskeySheet } from "@/components/bb/passkey";
import { Initials, Panel, ReasonList, SectionLabel } from "@/components/bb/primitives";
import { useCoolingReviews, wasCosigned } from "@/components/bb/review";
import { AppHeader, LocaleSwitcher, ThemeToggle } from "@/components/bb/shell";
import { useErrorToast } from "@/lib/errors";
import { useFormat } from "@/lib/format";
import { usePersona } from "@/lib/persona";
import { cn } from "@/lib/utils";
import type { Approval } from "@/lib/api/types";

/**
 * Lan, the family's second signature. She lives in Vietnam, hears from the app only when
 * something looks like a scam, and gets one calm, unmistakable request when it does.
 */
export default function CosignerHome() {
  const t = useTranslations("cosigner");
  const { user, client, persona } = usePersona();
  const reviews = useCoolingReviews();
  const closed = useQuery({ queryKey: ["approvals", persona, "rejected"], queryFn: () => client.approvals.list("rejected") });
  const open = (reviews.data ?? []).filter((a) => !wasCosigned(a));
  const signed = (reviews.data ?? []).filter((a) => wasCosigned(a));
  const history = [...signed, ...(closed.data ?? []).filter((a) => a.rawAction?.purpose === "verify_scam_claim")];

  return (
    <>
      <AppHeader
        left={
          <div className="flex items-center gap-2.5">
            <Initials name={user?.name ?? " "} />
            <div className="min-w-0 leading-tight">
              <div className="truncate text-[15px] font-semibold">{user ? t("hello", { name: user.name }) : " "}</div>
              <div className="truncate text-xs text-muted-foreground">{t("role")}</div>
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
      <main className="flex-1 space-y-6 px-4 pt-2 pb-10">
        {reviews.isLoading ? (
          <div className="h-64 animate-pulse rounded-2xl bg-muted" />
        ) : open.length ? (
          open.map((a) => <Review key={a.id} a={a} />)
        ) : (
          <Quiet />
        )}

        {!!history.length && (
          <section>
            <SectionLabel>{t("history")}</SectionLabel>
            <Panel className="divide-y">
              {history.map((a) => (
                <HistoryRow key={a.id} a={a} />
              ))}
            </Panel>
          </section>
        )}
      </main>
    </>
  );
}

function Quiet() {
  const t = useTranslations("cosigner");
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <Panel className="flex flex-col items-center px-6 py-10 text-center">
        <span className="grid size-14 place-items-center rounded-2xl bg-verified-soft text-verified-ink">
          <ShieldCheck className="size-7" />
        </span>
        <h1 className="mt-4 text-xl font-semibold tracking-tight">{t("quietTitle")}</h1>
        <p className="mt-1.5 max-w-xs text-sm text-pretty text-muted-foreground">{t("quietBody")}</p>
      </Panel>
      <section>
        <SectionLabel>{t("roleTitle")}</SectionLabel>
        <Panel className="divide-y p-0 text-sm">
          {(["role1", "role2", "role3"] as const).map((k, i) => (
            <div key={k} className="flex items-start gap-3 px-4 py-3">
              <span className="mt-0.5 grid size-5 shrink-0 place-items-center rounded-full bg-secondary text-[11px] font-semibold">{i + 1}</span>
              <span className="text-pretty">{t(k)}</span>
            </div>
          ))}
        </Panel>
      </section>
    </motion.div>
  );
}

function Review({ a }: { a: Approval }) {
  const t = useTranslations("cosigner");
  const tc = useTranslations("cooling");
  const f = useFormat();
  const { client } = usePersona();
  const qc = useQueryClient();
  const showError = useErrorToast();
  const [sheet, setSheet] = useState(false);
  const [cantReach, setCantReach] = useState(false);
  const [done, setDone] = useState(false);
  const { user } = usePersona();
  const score = a.risk.score;

  if (done) {
    return (
      <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }}>
        <Panel className="flex flex-col items-center px-6 py-10 text-center">
          <motion.span initial={{ scale: 0.5 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 300, damping: 14 }} className="grid size-16 place-items-center rounded-full bg-verified text-white">
            <Check className="size-8" strokeWidth={2.5} />
          </motion.span>
          <h1 className="mt-4 text-xl font-semibold tracking-tight">{t("signedTitle", { name: user?.name ?? "" })}</h1>
          <p className="mt-1.5 max-w-xs text-sm text-pretty text-muted-foreground">{t("signedBody")}</p>
        </Panel>
      </motion.div>
    );
  }

  return (
    <motion.article initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      <div className="px-1">
        <Pill tone="attention" dot pulse>
          {t("kicker")}
        </Pill>
        <h1 className="mt-3 text-[24px] leading-tight font-semibold tracking-tight text-balance">{t("title")}</h1>
        <p className="mt-2 text-[15px] leading-relaxed text-pretty text-muted-foreground">{t("body")}</p>
        {a.cooling && (
          <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-route-soft px-3 py-1 font-medium text-route-ink">
              <Snowflake className="size-4" />
              {tc("until", { time: f.date(a.cooling.until, "datetime") })}
            </span>
            <MockBadge what="clock" />
          </div>
        )}
      </div>

      <section>
        <SectionLabel>{t("doTitle")}</SectionLabel>
        <Panel className="divide-y p-0">
          {(["do1", "do2", "do3"] as const).map((k, i) => (
            <div key={k} className="flex items-start gap-3 px-4 py-3.5">
              <span className={cn("mt-0.5 grid size-6 shrink-0 place-items-center rounded-full text-xs font-semibold", i === 0 ? "bg-foreground text-background" : "bg-secondary")}>{i + 1}</span>
              <span className={cn("text-[15px] text-pretty", i === 0 && "font-medium")}>{t(k)}</span>
            </div>
          ))}
        </Panel>
      </section>

      <section>
        <SectionLabel action={<span className="rounded-full bg-attention-soft px-2 py-0.5 text-[11px] font-medium text-attention-ink tnum">{tc("score", { score })}</span>}>{t("whyTitle")}</SectionLabel>
        <Panel className="p-4">
          <ReasonList reasons={a.risk.features.map((x) => ({ ...x, severity: "warn" as const }))} />
        </Panel>
      </section>

      <Told />

      <div className="sticky bottom-0 -mx-4 space-y-2 border-t bg-background/92 px-4 pt-3 pb-safe backdrop-blur">
        <Button size="lg" className="h-13 w-full rounded-2xl text-base" onClick={() => setSheet(true)}>
          <UserRoundCheck className="size-5" />
          {t("sign")}
        </Button>
        <p className="text-center text-[11.5px] leading-snug text-pretty text-muted-foreground">{t("signHint")}</p>
        <button type="button" onClick={() => setCantReach(!cantReach)} className="mx-auto flex items-center gap-1.5 py-1 text-sm font-medium text-muted-foreground hover:text-foreground" aria-expanded={cantReach}>
          <PhoneCall className="size-4" />
          {t("cantReach")}
        </button>
        <AnimatePresence initial={false}>
          {cantReach && (
            <motion.p initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden rounded-xl bg-subtle px-3 py-2.5 text-sm text-pretty">
              {t("cantReachBody")}
            </motion.p>
          )}
        </AnimatePresence>
      </div>

      <PasskeySheet
        open={sheet}
        onOpenChange={setSheet}
        purpose="cosign"
        refId={a.id}
        hash={a.consentHash}
        title={t("sheetTitle")}
        lines={[{ label: t("sheetWhat"), value: t("sheetWhatValue") }]}
        onSigned={async (assertion) => {
          try {
            await client.approvals.cosign(a.id, assertion);
            qc.invalidateQueries();
            setTimeout(() => setDone(true), 700);
          } catch (e) {
            showError(e);
            throw e;
          }
        }}
      />
    </motion.article>
  );
}

function Told() {
  const t = useTranslations("cosigner");
  const [open, setOpen] = useState(false);
  return (
    <section>
      <button type="button" onClick={() => setOpen(!open)} className="flex w-full items-center justify-between px-1 pb-2 text-[13px] font-medium text-muted-foreground" aria-expanded={open}>
        {t("toldTitle")}
        <ChevronDown className={cn("size-4 transition-transform", open && "rotate-180")} />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
            <Panel className="space-y-2 p-4 text-sm">
              {(["told1", "told2", "told3"] as const).map((k) => (
                <p key={k} className="flex gap-2 text-pretty">
                  <Hourglass className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                  {t(k)}
                </p>
              ))}
            </Panel>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}

function HistoryRow({ a }: { a: Approval }) {
  const t = useTranslations("cosigner");
  const f = useFormat();
  const closed = a.status === "rejected";
  return (
    <div className="flex items-center gap-3 px-4 py-3">
      <span className={cn("grid size-9 shrink-0 place-items-center rounded-full", closed ? "bg-secondary" : "bg-verified-soft text-verified-ink")}>
        {closed ? <ShieldCheck className="size-4" /> : <Check className="size-4" />}
      </span>
      <div className="min-w-0 flex-1">
        <div className="text-sm font-medium">{closed ? t("historyClosed") : t("historySigned")}</div>
        <div className="text-xs text-muted-foreground">{f.date(a.createdAt, "datetime")}</div>
      </div>
    </div>
  );
}
