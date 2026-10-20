import type { Locale } from "@/lib/api/types";

export const locales: Locale[] = ["vi", "en", "ko", "zh"];
export type Surface = "parent" | "student" | "cosigner" | "site";

/** Minh reads Vietnamese; Linh's app defaults to English so judges can follow both phones; judges see English. */
export const surfaceDefaults: Record<Surface, Locale> = { parent: "vi", student: "en", cosigner: "vi", site: "en" };

export const localeCookie = (surface: Surface) => `bb-locale-${surface}`;

export function surfaceOf(pathname: string): Surface {
  if (pathname.startsWith("/parent")) return "parent";
  if (pathname.startsWith("/student")) return "student";
  if (pathname.startsWith("/cosigner")) return "cosigner";
  return "site";
}

export const localeNames: Record<Locale, { native: string; short: string }> = {
  vi: { native: "Tiếng Việt", short: "VI" },
  en: { native: "English", short: "EN" },
  ko: { native: "한국어", short: "KO" },
  zh: { native: "简体中文", short: "中文" },
};

export const intlTag: Record<Locale, string> = { vi: "vi-VN", en: "en-GB", ko: "ko-KR", zh: "zh-CN" };
