"use client";

import { Home, ListOrdered, MessageCircle } from "lucide-react";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { TabBar } from "@/components/bb/shell";
import { isMine } from "@/lib/approval";
import { usePersona } from "@/lib/persona";
import { useApprovals } from "@/lib/queries";

export function ParentTabs() {
  const t = useTranslations("parent.tabs");
  const pathname = usePathname();
  const pending = useApprovals("pending");
  const { user } = usePersona();
  // Full-screen flows hide the tab bar so the decision has the whole screen.
  if (/\/parent\/(approvals|mandate|freeze)/.test(pathname)) return null;
  return (
    <TabBar
      tabs={[
        { href: "/parent", label: t("home"), icon: Home, badge: pending.data?.filter((a) => isMine(a, user)).length },
        { href: "/parent/activity", label: t("activity"), icon: ListOrdered },
        { href: "/parent/chat", label: t("assistant"), icon: MessageCircle },
      ]}
    />
  );
}
