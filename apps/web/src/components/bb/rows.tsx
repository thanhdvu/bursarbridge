"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Landmark, UserRoundCheck } from "lucide-react";
import { motion } from "motion/react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { useErrorToast } from "@/lib/errors";
import { usePersona } from "@/lib/persona";
import { Pill } from "./badges";
import { HashChip } from "./hash";
import { Panel } from "./primitives";
import { plainName, useFormat } from "@/lib/format";
import type { Mandate, Payment } from "@/lib/api/types";

export function MandateCard({ m }: { m: Mandate }) {
  const t = useTranslations("mandate");
  const f = useFormat();
  const { client, user } = usePersona();
  const qc = useQueryClient();
  const showError = useErrorToast();
  const [confirming, setConfirming] = useState(false);
  const monthly = m.period === "monthly";
  // The live API names a name-checked payee only in the catalog; resolve it so the rule never reads "only to ".
  const catalog = useQuery({ queryKey: ["catalog", user?.familyId], queryFn: () => client.catalog(), enabled: m.payeeRule.type === "name_checked" && !m.payeeLabel });
  const payeeName = plainName(m.payeeLabel ?? catalog.data?.bankPayees.find((p) => m.payeeRule.type === "name_checked" && p.id === m.payeeRule.payeeId)?.name ?? "");
  const cap = Number(m.cap.amount);
  const spent = Number(m.spent.amount);
  const k = cap > 0 ? Math.min(1, spent / cap) : 0;
  return (
    <Panel className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <h3 className="font-semibold whitespace-nowrap">{t(`purpose.${m.purpose}`)}</h3>
            <Pill tone={m.status === "active" ? "verified" : m.status === "suspended" ? "route" : "neutral"} dot>
              {t(`status.${m.status}`)}
            </Pill>
          </div>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {m.payeeRule.type === "credentialed" ? t("ruleCredentialed") : t("ruleNameChecked", { payee: payeeName })}
          </p>
        </div>
        <div className="shrink-0 text-right">
          <div className="text-xs text-muted-foreground">{m.period === "monthly" ? t("capMonthly") : t("cap")}</div>
          <div className="font-display text-lg leading-tight font-medium tnum">{f.money(m.cap)}</div>
        </div>
      </div>
      {monthly && (
        <div className="mt-3 space-y-1 rounded-xl bg-subtle px-3 py-2.5 text-xs text-muted-foreground">
          <div>{t("cycle")}</div>
          <div className="tnum">{t("until", { date: f.date(m.expiresAt) })}</div>
          <div>{t("landlordCheck")}</div>
        </div>
      )}
      {monthly && user?.role === "parent" && m.status === "active" && (
        <div className="mt-3 flex items-center gap-2">
          <Link href={`/parent/mandate/new?purpose=${m.purpose}`} className="inline-flex h-8 items-center rounded-lg border px-3 text-xs font-medium hover:bg-accent">
            {t("change")}
          </Link>
          <button
            type="button"
            className={confirming ? "inline-flex h-8 items-center rounded-lg bg-blocked px-3 text-xs font-medium text-white" : "inline-flex h-8 items-center rounded-lg px-3 text-xs font-medium text-blocked hover:bg-blocked-soft"}
            onClick={async () => {
              if (!confirming) {
                setConfirming(true);
                return;
              }
              try {
                await client.mandates.revoke(m.id);
                qc.invalidateQueries();
              } catch (e) {
                showError(e);
              } finally {
                setConfirming(false);
              }
            }}
          >
            {confirming ? t("cancelConfirm") : t("cancel")}
          </button>
        </div>
      )}
      {!monthly && (
        <div className="mt-3">
          <div className="h-1.5 overflow-hidden rounded-full bg-muted">
            <motion.div className="h-full rounded-full bg-verified" initial={{ width: 0 }} animate={{ width: `${k * 100}%` }} transition={{ duration: 0.8 }} />
          </div>
          <div className="mt-1.5 flex justify-between text-xs text-muted-foreground tnum">
            <span>{t("used", { amount: f.money(m.spent) })}</span>
            <span>{t("until", { date: f.date(m.expiresAt) })}</span>
          </div>
        </div>
      )}
      <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-muted-foreground">
        {m.cosignerId && (
          <span className="inline-flex items-center gap-1">
            <UserRoundCheck className="size-3.5" /> {t("cosigner")}
          </span>
        )}
        {m.chainTx && (
          <span className="inline-flex items-center gap-1.5">
            {t("onChain", { n: m.chainTx.blockNumber })}
            <HashChip value={m.chainTx.txHash} n={4} />
          </span>
        )}
      </div>
    </Panel>
  );
}

export function PaymentRow({ p, base = "/parent" }: { p: Payment; base?: string }) {
  const tp = useTranslations("payment");
  const f = useFormat();
  return (
    <Link href={`${base}/payments/${p.id}`} className="flex items-center gap-3 px-4 py-3 transition-colors first:rounded-t-2xl last:rounded-b-2xl hover:bg-accent/50">
      <span className="grid size-9 shrink-0 place-items-center rounded-full bg-secondary">
        <Landmark className="size-4" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-medium">{p.payee.institution === "Private landlord" || p.purpose === "rent" ? plainName(p.payee.name) : plainName(p.payee.institution)}</div>
        <div className="truncate text-xs text-muted-foreground">
          {tp(`purpose.${p.purpose ?? "tuition"}`)}
          {p.autoExecuted ? ` · ${tp("auto")}` : ""} · {p.createdAt || p.timeline[0]?.at ? f.date((p.createdAt || p.timeline[0]?.at)!, "short") : ""}
        </div>
      </div>
      <div className="text-right">
        <div className="text-sm font-medium tnum">−{f.money(p.send)}</div>
        <div className="text-xs text-muted-foreground">{tp(`status.${p.status}`)}</div>
      </div>
    </Link>
  );
}
