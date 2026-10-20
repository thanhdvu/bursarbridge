"use client";

import { useTranslations } from "next-intl";

type Values = Record<string, string | number>;

/**
 * Copy added in the Trust center / Judge console identity pass. The keys live in the i18n patch
 * (trust-judge-keys.json, all four locales); until it is merged into messages/*.json this falls back
 * to the English text given here, so the page never shows a raw key.
 */
export function useDraftCopy(ns: "trust" | "judge") {
  const t = useTranslations(ns) as unknown as { has: (k: string) => boolean; (k: string, v?: Values): string };
  return (key: string, en: string, values?: Values) => (t.has(key) ? t(key, values) : en.replace(/\{(\w+)\}/g, (_, k: string) => String(values?.[k] ?? `{${k}}`)));
}
