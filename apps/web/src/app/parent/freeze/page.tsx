"use client";

import { useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Ban, KeyRound, PauseCircle, Snowflake, Sun } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { PasskeySheet } from "@/components/bb/passkey";
import { Panel } from "@/components/bb/primitives";
import { AppHeader } from "@/components/bb/shell";
import { NumberTicker } from "@/components/bb/ticker";
import { usePersona } from "@/lib/persona";
import type { FreezeResult } from "@/lib/api/types";
import { useErrorToast } from "@/lib/errors";

export default function FreezePage() {
  const t = useTranslations("freeze");
  const { client, user } = usePersona();
  const qc = useQueryClient();
  const [result, setResult] = useState<FreezeResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [sheet, setSheet] = useState(false);
  const frozen = !!user?.frozen || !!result?.frozen;
  const showError = useErrorToast();

  const doFreeze = async () => {
    setBusy(true);
    try {
      const r = await client.freeze();
      setResult(r);
      qc.invalidateQueries();
    } catch (e) {
      showError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <AppHeader
        left={
          <Link href="/parent" aria-label={t("back")} className="-ml-2 grid size-9 place-items-center rounded-full hover:bg-accent">
            <ArrowLeft className="size-5" />
          </Link>
        }
      />
      <main className="flex flex-1 flex-col px-5 pb-8">
        <div className="flex flex-col items-center pt-4 text-center">
          <motion.div
            animate={frozen ? { rotate: [0, 60, 0], scale: [1, 1.08, 1] } : { rotate: 0 }}
            transition={{ duration: 0.9, ease: "easeInOut" }}
            className="relative grid size-24 place-items-center rounded-[28px] bg-route-soft text-route-ink"
          >
            {frozen && <span className="absolute inset-0 rounded-[28px] ring-2 ring-route/40" />}
            <Snowflake className="size-11" strokeWidth={1.6} />
          </motion.div>
          <h1 className="mt-5 text-2xl font-semibold tracking-tight">{frozen ? t("frozenTitle") : t("title")}</h1>
          <p className="mt-1.5 max-w-xs text-sm text-pretty text-muted-foreground">{frozen ? t("frozenBody") : t("lead")}</p>
        </div>

        <AnimatePresence>
          {result && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mt-6 grid grid-cols-3 gap-2">
              {[
                { v: result.pausedApprovals ?? 0, l: t("stats.paused") },
                { v: result.cancelledPayments ?? 0, l: t("stats.cancelled") },
                { v: result.suspendedMandates ?? 0, l: t("stats.suspended") },
              ].map((s) => (
                <Panel key={s.l} className="p-3 text-center">
                  <div className="text-2xl font-semibold tnum">
                    <NumberTicker value={s.v} format={(n) => String(n)} duration={0.6} />
                  </div>
                  <div className="mt-0.5 text-[11px] leading-tight text-muted-foreground">{s.l}</div>
                </Panel>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {!frozen && (
          <Panel className="mt-6 divide-y p-0 text-sm">
            {[
              { icon: KeyRound, text: t("what.revoke") },
              { icon: Ban, text: t("what.cancel") },
              { icon: PauseCircle, text: t("what.pause") },
            ].map((w) => (
              <div key={w.text} className="flex items-start gap-3 px-4 py-3">
                <w.icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                <span className="text-pretty">{w.text}</span>
              </div>
            ))}
          </Panel>
        )}

        <p className="mt-4 text-sm text-pretty text-muted-foreground">{t("incoming")}</p>
        <div className="mt-auto pt-8">
          {frozen ? (
            <>
              <Button size="lg" variant="outline" className="h-13 w-full rounded-2xl text-base" onClick={() => setSheet(true)}>
                <Sun className="size-5" />
                {t("unfreeze")}
              </Button>
              <p className="mt-2 text-center text-xs text-muted-foreground">{t("unfreezeHint")}</p>
            </>
          ) : (
            <>
              <Button size="lg" className="h-13 w-full rounded-2xl bg-route text-base text-white hover:bg-route/90" onClick={doFreeze} disabled={busy}>
                <Snowflake className="size-5" />
                {t("cta")}
              </Button>
              <p className="mt-2 text-center text-xs text-muted-foreground">{t("ctaHint")}</p>
            </>
          )}
        </div>
      </main>
      <PasskeySheet
        open={sheet}
        onOpenChange={setSheet}
        purpose="freeze"
        refId={user?.familyId ?? ""}
        title={t("unfreezeTitle")}
        lines={[{ label: t("unfreezeLine"), value: user?.name ?? "" }]}
        onSigned={async (assertion) => {
          try {
            await client.unfreeze(assertion);
          } catch (e) {
            showError(e);
            throw e;
          }
          setResult(null);
          qc.invalidateQueries();
        }}
      />
    </>
  );
}
