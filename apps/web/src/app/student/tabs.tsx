"use client";

import { FolderOpen, MessageCircle, Route } from "lucide-react";
import { useTranslations } from "next-intl";
import { TabBar } from "@/components/bb/shell";
import { useApprovals } from "@/lib/queries";
import { usePersona } from "@/lib/persona";
import { isMine } from "@/lib/approval";

export function StudentTabs() {
  const t = useTranslations("student.tabs");
  const { user } = usePersona();
  const pending = useApprovals("pending");
  const mine = pending.data?.filter((a) => isMine(a, user)).length;
  return (
    <TabBar
      tabs={[
        { href: "/student", label: t("assistant"), icon: MessageCircle, badge: mine },
        { href: "/student/documents", label: t("documents"), icon: FolderOpen },
        { href: "/student/timeline", label: t("timeline"), icon: Route, match: (p) => p.startsWith("/student/timeline") || p.startsWith("/student/payments") || p.startsWith("/student/refunds") },
      ]}
    />
  );
}
