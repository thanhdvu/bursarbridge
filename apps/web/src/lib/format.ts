"use client";

import { useLocale } from "next-intl";
import { useMemo } from "react";
import type { Locale, Money } from "@/lib/api/types";
import { intlTag } from "@/i18n/config";

const DIGITS: Record<string, number> = { VND: 0, KRW: 0, JPY: 0, CNY: 2, USD: 2, AUD: 2 };

export function formatMoney(money: Money | number, locale: Locale, currency?: string, opts: { sign?: boolean; compact?: boolean; code?: boolean } = {}) {
  const amount = typeof money === "number" ? money : Number(money.amount);
  const cur = typeof money === "number" ? currency! : money.currency;
  const digits = DIGITS[cur] ?? 2;
  const nf = new Intl.NumberFormat(intlTag[locale], {
    style: "currency",
    currency: cur,
    currencyDisplay: opts.code ? "code" : "narrowSymbol",
    minimumFractionDigits: opts.compact ? 0 : digits,
    maximumFractionDigits: opts.compact ? 1 : digits,
    notation: opts.compact ? "compact" : "standard",
    signDisplay: opts.sign ? "exceptZero" : "auto",
  });
  return nf.format(amount);
}

/** Split for display: number part and currency symbol separately (hero amounts). */
export function moneyParts(money: Money, locale: Locale) {
  const amount = Number(money.amount);
  const digits = DIGITS[money.currency] ?? 2;
  const parts = new Intl.NumberFormat(intlTag[locale], {
    style: "currency",
    currency: money.currency,
    currencyDisplay: "narrowSymbol",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).formatToParts(amount);
  const symbol = parts.find((p) => p.type === "currency")?.value ?? money.currency;
  const symbolFirst = parts.findIndex((p) => p.type === "currency") < parts.findIndex((p) => p.type === "integer");
  const number = parts
    .filter((p) => p.type !== "currency" && p.type !== "literal")
    .map((p) => p.value)
    .join("");
  return { symbol, number, symbolFirst };
}

export function formatNumber(n: number, locale: Locale, digits = 0) {
  return new Intl.NumberFormat(intlTag[locale], { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(n);
}

export function formatDate(iso: string, locale: Locale, style: "date" | "datetime" | "time" | "short" = "date") {
  const d = new Date(iso);
  const tz = "Asia/Ho_Chi_Minh";
  const o: Intl.DateTimeFormatOptions =
    style === "date"
      ? { day: "numeric", month: "short", year: "numeric", timeZone: tz }
      : style === "short"
        ? { day: "numeric", month: "short", timeZone: tz }
        : style === "time"
          ? { hour: "2-digit", minute: "2-digit", timeZone: tz }
          : { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZone: tz };
  return new Intl.DateTimeFormat(intlTag[locale], o).format(d);
}

export function formatRelative(iso: string, nowMs: number, locale: Locale) {
  const diff = Date.parse(iso) - nowMs;
  const rtf = new Intl.RelativeTimeFormat(intlTag[locale], { numeric: "auto" });
  const abs = Math.abs(diff);
  if (abs < 60_000) return rtf.format(Math.round(diff / 1000), "second");
  if (abs < 3600_000) return rtf.format(Math.round(diff / 60_000), "minute");
  if (abs < 86400_000) return rtf.format(Math.round(diff / 3600_000), "hour");
  return rtf.format(Math.round(diff / 86400_000), "day");
}

export function useFormat() {
  const locale = useLocale() as Locale;
  return useMemo(
    () => ({
      locale,
      money: (m: Money | number, currency?: string, opts?: Parameters<typeof formatMoney>[3]) => formatMoney(m, locale, currency, opts),
      number: (n: number, digits?: number) => formatNumber(n, locale, digits),
      date: (iso: string, style?: Parameters<typeof formatDate>[2]) => formatDate(iso, locale, style),
      relative: (iso: string, nowMs: number) => formatRelative(iso, nowMs, locale),
      parts: (m: Money) => moneyParts(m, locale),
    }),
    [locale],
  );
}

export function plainName(name: string | undefined | null) {
  return (name ?? "").replace(/\s*\(MOCK\)\s*/g, "").trim();
}

export function shortHash(h: string | undefined | null, n = 6) {
  if (!h) return "";
  const s = h.startsWith("0x") ? h.slice(2) : h;
  return `${h.startsWith("0x") ? "0x" : ""}${s.slice(0, n)}…${s.slice(-4)}`;
}

// ---------------------------------------------------------------------------
// Until the API serves these localized (r5), translate the few English strings it returns for known seed values.
// Anything that does not match passes through unchanged, so localized API text wins automatically.

const SEASON: Record<string, Record<Locale, string>> = {
  Spring: { en: "Spring", vi: "Xuân", ko: "봄", zh: "春季" },
  Fall: { en: "Fall", vi: "Thu", ko: "가을", zh: "秋季" },
  Autumn: { en: "Autumn", vi: "Thu", ko: "가을", zh: "秋季" },
};

export function localTerm(term: string | undefined, locale: Locale) {
  if (!term) return "";
  const m = /^(Spring|Fall|Autumn) (\d{4})\s*[-–·]\s*semester (\d)$/i.exec(term.trim());
  if (!m || locale === "en") return term;
  const season = SEASON[m[1][0].toUpperCase() + m[1].slice(1).toLowerCase()]?.[locale] ?? m[1];
  const [y, n] = [m[2], m[3]];
  if (locale === "vi") return `Học kỳ ${n} · ${season} ${y}`;
  if (locale === "ko") return `${y}년 ${season} ${n}학기`;
  return `${y}年${season} 第${n}学期`;
}

const CLAUSES: Record<string, Record<Exclude<Locale, "en">, string>> = {
  "MOCK refund board rate": { vi: "Tỷ giá ngày hoàn tiền (MOCK)", ko: "환불일 환율 (MOCK)", zh: "退款日汇率（MOCK）" },
  "HBU-REF-01 fictional 1% charge": { vi: "HBU-REF-01 · phí hư cấu 1%", ko: "HBU-REF-01 · 가상 수수료 1%", zh: "HBU-REF-01 · 虚构手续费 1%" },
  "HBU-REF-01 fictional zero retention": { vi: "HBU-REF-01 · không giữ lại (hư cấu)", ko: "HBU-REF-01 · 유보금 없음(가상)", zh: "HBU-REF-01 · 无扣留（虚构）" },
};

export function localClause(clause: string | undefined, locale: Locale) {
  if (!clause || locale === "en") return clause;
  return CLAUSES[clause]?.[locale] ?? clause;
}
