"use client";

import { Snowflake } from "lucide-react";
import { motion } from "motion/react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { usePersona } from "@/lib/persona";

export function FrozenBanner() {
  const { user } = usePersona();
  const t = useTranslations("freeze");
  if (!user?.frozen) return null;
  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      role="status"
      className="flex items-center gap-3 rounded-2xl border border-route/30 bg-route-soft px-4 py-3 text-route-ink"
    >
      <Snowflake className="size-5 shrink-0" />
      <div className="min-w-0 flex-1 text-sm">
        <div className="font-semibold">{t("bannerTitle")}</div>
        <div className="text-route-ink/80">{t("bannerBody")}</div>
      </div>
      {user.role === "parent" && (
        <Link href="/parent/freeze" className="shrink-0 text-sm font-semibold underline-offset-4 hover:underline">
          {t("manage")}
        </Link>
      )}
    </motion.div>
  );
}
