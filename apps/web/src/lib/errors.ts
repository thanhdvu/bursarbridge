"use client";

import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { ApiError } from "@/lib/api/client";

/** Turn an API error into a short, localised sentence (stable codes from the contract). */
export function useErrorToast() {
  const t = useTranslations("errors");
  return (e: unknown) => {
    const code = e instanceof ApiError ? e.code : "";
    const msg = code && t.has(code as never) ? t(code as never) : t("generic");
    toast.error(msg, { description: e instanceof ApiError && e.ruleId ? e.ruleId : undefined });
  };
}
