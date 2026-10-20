"use client";

import { useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Building2, CalendarDays, Check, Lock, ShieldCheck, UserRoundCheck } from "lucide-react";
import { motion } from "motion/react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useState, useSyncExternalStore } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { HashChip } from "@/components/bb/hash";
import { PasskeySheet } from "@/components/bb/passkey";
import { Panel } from "@/components/bb/primitives";
import { AppHeader } from "@/components/bb/shell";
import { useFormat } from "@/lib/format";
import { usePersona } from "@/lib/persona";
import { cn } from "@/lib/utils";
import type { Mandate } from "@/lib/api/types";
import { TUITION_KRW } from "@/mock/fixtures";
import { useErrorToast } from "@/lib/errors";

export default function NewMandatePage() {
  const t = useTranslations("mandateNew");
  const f = useFormat();
  const { client, persona } = usePersona();
  const catalog = useQuery({ queryKey: ["catalog", persona], queryFn: () => client.catalog() });
  const purpose = useSyncExternalStore<"tuition" | "rent">(() => () => {}, () => new URLSearchParams(window.location.search).get("purpose") === "rent" ? "rent" : "tuition", () => "tuition");
  const rentPayee = catalog.data?.bankPayees[0];
  // v1.17: the verified-landlord setup (masked account, lease status, template expiry).
  const rent = useQuery({ queryKey: ["rent", persona], queryFn: () => client.rent(), enabled: purpose === "rent", retry: false });
  const qc = useQueryClient();
  const router = useRouter();
  const [capEdit, setCap] = useState<number>();
  const [untilEdit, setUntil] = useState<string>();
  const cap = capEdit ?? (purpose === "rent" ? Number(rentPayee?.amount ?? 0) : TUITION_KRW);
  const until = untilEdit ?? (purpose === "rent" ? rent.data?.mandateTemplate.expiresAt.slice(0, 10) ?? "2027-06-01" : "2027-03-31");
  // Lan is the Nguyễn family's co-signer; the Wang family has none in the seed.
  const hasCosigner = persona === "parent_minh";
  const [cosign, setCosign] = useState(true);
  const [draft, setDraft] = useState<Mandate | null>(null);
  const [signed, setSigned] = useState<Mandate | null>(null);
  const [busy, setBusy] = useState(false);
  const [sheet, setSheet] = useState(false);
  const showError = useErrorToast();

  const presets = purpose === "rent" ? (rentPayee ? [Number(rentPayee.amount)] : []) : [TUITION_KRW, 10_000_000];

  const prepare = async () => {
    setBusy(true);
    try {
      const m = await client.mandates.create({
        purpose,
        payeeRule:
          purpose === "rent" && rentPayee
            ? { type: "name_checked", payeeId: rentPayee.id }
            : { type: "credentialed", issuer: catalog.data?.issuer ?? (await client.catalog()).issuer },
        cap: { amount: cap.toFixed(2), currency: "KRW" },
        period: purpose === "rent" ? "monthly" : "once",
        expiresAt: new Date(`${until}T23:59:00+07:00`).toISOString(),
        cosignerId: cosign && hasCosigner ? "usr_mother_lan" : undefined,
      });
      setDraft(m);
      setSheet(true);
    } catch (e) {
      showError(e);
    } finally {
      setBusy(false);
    }
  };

  if (signed) {
    return (
      <>
        <AppHeader left={<span />} />
        <main className="flex flex-1 flex-col px-5 pb-10">
          <div className="flex flex-col items-center pt-8 text-center">
            <motion.span initial={{ scale: 0.5 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 300, damping: 14 }} className="grid size-16 place-items-center rounded-full bg-verified text-white">
              <Check className="size-8" strokeWidth={2.5} />
            </motion.span>
            <h1 className="mt-4 text-2xl font-semibold tracking-tight">{t("done.title")}</h1>
            <p className="mt-1 max-w-xs text-sm text-pretty text-muted-foreground">{t("done.body")}</p>
          </div>
          <Panel className="mt-6 space-y-2 p-4 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted-foreground">{t("done.hash")}</span>
              <HashChip value={signed.hash} n={8} />
            </div>
            {signed.chainTx && (
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-foreground">{t("done.chain", { n: signed.chainTx.blockNumber })}</span>
                <HashChip value={signed.chainTx.txHash} n={8} />
              </div>
            )}
          </Panel>
          <Button asChild size="lg" className="mt-auto h-12 w-full rounded-xl">
            <Link href="/parent">{t("done.home")}</Link>
          </Button>
        </main>
      </>
    );
  }

  return (
    <>
      <AppHeader
        left={
          <button type="button" onClick={() => router.back()} aria-label={t("back")} className="-ml-2 grid size-9 place-items-center rounded-full hover:bg-accent">
            <ArrowLeft className="size-5" />
          </button>
        }
      />
      <main className="flex-1 space-y-5 px-4 pb-6">
        <div className="px-1">
          <h1 className="text-2xl font-semibold tracking-tight">{purpose === "rent" ? t("titleRent") : t("title")}</h1>
          <p className="mt-1 text-sm text-pretty text-muted-foreground">{purpose === "rent" ? t("leadRent") : t("lead")}</p>
        </div>

        <Panel className="divide-y p-0">
          {/* Who can be paid: fixed by design */}
          <div className="flex gap-3 p-4">
            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-verified-soft text-verified-ink">
              <Building2 className="size-5" />
            </span>
            <div className="min-w-0 flex-1">
              <div className="text-xs text-muted-foreground">{t("who")}</div>
              <div className="font-medium">{purpose === "rent" ? t("whoRent", { payee: rentPayee?.name ?? "" }) : t("whoValue")}</div>
              <p className="mt-1 text-xs text-pretty text-muted-foreground">{purpose === "rent" ? t("whoRentHint") : t("whoHint")}</p>
              {purpose === "rent" && rent.data && (
                <div className="mt-2 space-y-0.5 text-xs">
                  <div className="text-muted-foreground">{t("account", { masked: rent.data.landlord.account.masked })}</div>
                  <div className={rent.data.landlord.verification?.agreementStatus === "required" ? "text-attention-ink" : "text-verified-ink"}>
                    {rent.data.landlord.verification?.agreementStatus === "required" ? t("leaseRequired") : t("leaseVerified")}
                  </div>
                </div>
              )}
            </div>
            <Lock className="mt-1 size-4 shrink-0 text-muted-foreground" aria-label={t("locked")} />
          </div>

          {/* Cap */}
          <div className="p-4">
            <label htmlFor="cap" className="text-xs text-muted-foreground">
              {t("cap")}
            </label>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-lg font-semibold text-muted-foreground">₩</span>
              <input
                id="cap"
                inputMode="numeric"
                value={f.number(cap)}
                onChange={(e) => setCap(Number(e.target.value.replace(/\D/g, "")) || 0)}
                className="w-full bg-transparent text-2xl font-semibold tracking-tight tnum outline-none"
              />
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              {presets.map((p, i) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setCap(p)}
                  className={cn("rounded-full border px-3 py-1 text-xs font-medium", cap === p ? "border-foreground bg-foreground text-background" : "hover:bg-accent")}
                >
                  {i === 0 ? t(purpose === "rent" ? "presetRent" : "presetInvoice", { amount: f.money(p, "KRW") }) : f.money(p, "KRW")}
                </button>
              ))}
            </div>
            <p className="mt-2 text-xs text-muted-foreground">{purpose === "rent" ? t("capHintRent") : t("capHint")}</p>
          </div>

          {/* Until */}
          <div className="flex items-center gap-3 p-4">
            <CalendarDays className="size-5 text-muted-foreground" />
            <label htmlFor="until" className="flex-1 text-sm">
              {t("until")}
            </label>
            {/* The native date field follows the browser locale (03/31/2027 for a Vietnamese parent); show the date in the app language and keep the native picker underneath. */}
            <span className="relative inline-flex items-center rounded-lg border bg-card px-2.5 py-1 text-sm font-medium tnum">
              {f.date(until + "T12:00:00Z", "date")}
              <input
                id="until"
                type="date"
                value={until}
                min="2026-10-16"
                onChange={(e) => e.target.value && setUntil(e.target.value)}
                onClick={(e) => e.currentTarget.showPicker?.()}
                className="absolute inset-0 cursor-pointer opacity-0"
              />
            </span>
          </div>

          {/* Co-signer */}
          {hasCosigner && (
          <div className="flex items-center gap-3 p-4">
            <UserRoundCheck className="size-5 text-muted-foreground" />
            <div className="flex-1">
              <label htmlFor="cosign" className="block text-sm">
                {t("cosign")}
              </label>
              <p className="text-xs text-muted-foreground">{t("cosignHint")}</p>
            </div>
            <Switch id="cosign" checked={cosign} onCheckedChange={setCosign} />
          </div>
          )}
        </Panel>

        <div className="rounded-2xl bg-subtle px-4 py-3.5 text-sm leading-relaxed text-pretty">
          <ShieldCheck className="mr-1.5 inline size-4 -translate-y-px text-verified" />
          {purpose === "rent"
            ? t("summaryRent", { cap: f.money(cap, "KRW"), payee: rentPayee?.name ?? "", date: f.date(new Date(`${until}T12:00:00Z`).toISOString()) })
            : t("summary", { cap: f.money(cap, "KRW"), date: f.date(new Date(`${until}T12:00:00Z`).toISOString()) })}
          {cosign && hasCosigner ? ` ${t("summaryCosign")}` : ""}
        </div>
        <p className="px-1 text-xs text-muted-foreground">{t("never")}</p>
      </main>
      <div className="sticky bottom-0 z-30 border-t bg-background/92 px-4 pt-3 pb-safe backdrop-blur">
        <Button size="lg" className="h-13 w-full rounded-2xl text-base" onClick={prepare} disabled={busy || cap <= 0}>
          <ShieldCheck className="size-5" />
          {t("sign")}
        </Button>
      </div>
      {draft && (
        <PasskeySheet
          open={sheet}
          onOpenChange={setSheet}
          purpose="mandate"
          refId={draft.id}
          hash={draft.hash}
          title={purpose === "rent" ? t("sheetTitleRent") : t("sheetTitle")}
          lines={[
            { label: t("who"), value: purpose === "rent" ? `${rentPayee?.name ?? ""} ✓` : "Hanbit University ✓" },
            { label: t("cap"), value: f.money(draft.cap) },
            { label: t("until"), value: f.date(draft.expiresAt) },
          ]}
          onSigned={async (assertion) => {
            const m = await client.mandates.sign(draft.id, assertion);
            qc.invalidateQueries();
            setTimeout(() => setSigned(m), 700);
          }}
        />
      )}
    </>
  );
}
