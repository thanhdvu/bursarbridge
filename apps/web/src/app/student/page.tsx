"use client";

import { useTranslations } from "next-intl";
import { AgentChat } from "@/components/bb/chat";
import { FrozenBanner } from "@/components/bb/frozen-banner";
import { Pill } from "@/components/bb/badges";
import { AppHeader, LocaleSwitcher, ThemeToggle } from "@/components/bb/shell";
import { NewChatButton } from "@/components/bb/new-chat";
import { usePersona } from "@/lib/persona";
import { usePayments, useRefunds } from "@/lib/queries";

/** Linh's home is the conversation: she forwards things and the agent does the rest. */
export default function StudentHome() {
  const t = useTranslations("student.home");
  const tp = useTranslations("payment");
  const tr = useTranslations("refund");
  const { user } = usePersona();
  const payments = usePayments();
  const refunds = useRefunds();
  const refund = refunds.data?.[0];
  // Tuition first; a family that only pays rent (the Wangs) shows its latest rent payment.
  const pay =
    payments.data?.find((p) => (p.purpose ?? "tuition") === "tuition" && p.status !== "cancelled") ??
    payments.data?.find((p) => p.status !== "cancelled");
  const isWang = user?.familyId === "fam_wang";

  const loading = payments.isPending || refunds.isPending;
  const status = refund
    ? { tone: (refund.status === "received" || refund.status === "reconciled" ? "verified" : "attention") as "verified" | "attention", text: tr(`status.${refund.status}`) }
    : pay
      ? { tone: (pay.status === "matched" ? "verified" : "route") as "verified" | "route", text: tp(`status.${pay.status}`) }
      : { tone: "neutral" as const, text: t("noPayment") };

  return (
    <div className="flex h-[calc(100dvh-64px)] flex-col md:h-[calc(100dvh-8rem)]">
      <AppHeader
        className="border-b"
        left={
          <div className="min-w-0">
            <h1 className="truncate text-[15px] font-semibold">{isWang ? t("titleWang") : t("title")}</h1>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="truncate">{isWang ? t("subWang") : t("sub")}</span>
              {/* Never show a wrong state while loading: a quiet placeholder instead of "Nothing paid yet". */}
              {loading ? (
                <span className="h-5 w-24 shrink-0 animate-pulse rounded-full bg-muted" aria-label="…" />
              ) : (
                <Pill tone={status.tone} dot className="h-5 px-2 text-[11px]">
                  {status.text}
                </Pill>
              )}
            </div>
          </div>
        }
        right={
          <>
            <NewChatButton />
            <LocaleSwitcher compact />
            <ThemeToggle />
          </>
        }
      />
      <div className="px-4 pt-3 empty:hidden">
        <FrozenBanner />
      </div>
      <AgentChat suggestions={isWang ? [t("w1"), t("w2"), t("w3")] : [t("s1"), t("s2"), t("s3"), t("s4"), t("s5")]} />
    </div>
  );
}
