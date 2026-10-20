"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import type { AppEvent } from "@/lib/api/types";
import { PersonaProvider, personaFor, useFamily } from "@/lib/persona";
import { DemoDock } from "./demo-dock";
import { ChainCatchup } from "./study-progress";
import { MobileFrame } from "./shell";

/** Parent and student surfaces: persona follows the selected demo family; notifications become toasts. */
export function FamilySurface({ role, children }: { role: "parent" | "student" | "cosigner"; children: React.ReactNode }) {
  const family = useFamily();
  const persona = personaFor(role, family);
  const t = useTranslations("notify");
  const router = useRouter();
  const onEvent = (e: AppEvent) => {
    const d = e.data as Record<string, string | boolean>;
    switch (e.type) {
      case "approval_created":
        if (d.status === "cooling_off") {
          if (role === "cosigner") toast(t("cosignNeeded"), { description: t("cosignNeededBody"), duration: 15000 });
          else if (role === "parent") toast(t("scamPaused"), { description: t("scamPausedBody") });
          break;
        }
        if (role === "parent" && d.action !== "refund_claim")
          toast(t("approval"), {
            description: t("approvalBody"),
            action: { label: t("review"), onClick: () => router.push(`/parent/approvals/${d.approvalId}`) },
            duration: 10000,
          });
        if (role === "student" && d.action === "refund_claim") toast(t("claimReady"));
        break;
      case "payment_updated":
        if (d.cosigned && role === "parent") {
          toast.success(t("cosigned"));
          break;
        }
        if (d.status === "matched") toast.success(t(d.autoExecuted ? "rentPaid" : "paid"));
        else if (d.autoExecuted && d.status === "executing") toast(t("rentAuto"), { description: t("rentAutoBody") });
        else if (d.status === "cancelled") toast(t("cancelled"));
        break;
      case "refund_updated":
        if (d.status === "received") toast.success(t("refundHome"));
        else if (d.status === "approved") toast(t("refundApproved"));
        break;
      case "blocked":
        if (role === "student") break;
        toast.error(t("blocked"), { description: t("blockedBody") });
        break;
      case "freeze":
        if (d.reset) break;
        toast(d.frozen ? t("frozen") : t("unfrozen"));
        break;
    }
  };
  return (
    <PersonaProvider key={persona} persona={persona} onEvent={onEvent}>
      <MobileFrame><ChainCatchup />{children}</MobileFrame>
      <DemoDock />
    </PersonaProvider>
  );
}
