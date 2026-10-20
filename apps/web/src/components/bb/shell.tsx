"use client";

import { Check, Languages, Monitor, Moon, Sun } from "lucide-react";
import { motion } from "motion/react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useTheme } from "@/lib/theme";
import { useTransition, useSyncExternalStore } from "react";
import type { Locale } from "@/lib/api/types";
import { localeCookie, localeNames, locales, surfaceOf } from "@/i18n/config";
import { cn } from "@/lib/utils";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { useSimClock } from "@/lib/clock";
import { useFormat } from "@/lib/format";
import { MockBadge } from "./badges";

const subscribeHydration = () => () => {};
export function useInFrame() {
  return useSyncExternalStore(subscribeHydration, () => window.self !== window.top, () => false);
}

export function setLocaleCookie(pathname: string, l: Locale) {
  document.cookie = `${localeCookie(surfaceOf(pathname))}=${l}; path=/; max-age=31536000; samesite=lax`;
}

export function LocaleSwitcher({ className, compact }: { className?: string; compact?: boolean }) {
  const locale = useLocale() as Locale;
  const pathname = usePathname();
  const router = useRouter();
  const [pending, start] = useTransition();
  const t = useTranslations("common");
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        aria-label={t("language")}
        className={cn(
          "inline-flex h-9 items-center gap-1.5 rounded-full px-2.5 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground",
          pending && "opacity-60",
          className,
        )}
      >
        <Languages className="size-4" />
        {!compact && <span className="font-medium">{localeNames[locale].short}</span>}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-40">
        <DropdownMenuLabel className="text-xs text-muted-foreground">{t("language")}</DropdownMenuLabel>
        {locales.map((l) => (
          <DropdownMenuItem
            key={l}
            lang={l}
            onSelect={() => {
              setLocaleCookie(pathname, l);
              start(() => router.refresh());
            }}
            className="justify-between"
          >
            {localeNames[l].native}
            {l === locale && <Check className="size-4" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();
  const t = useTranslations("common");
  const mounted = useSyncExternalStore(subscribeHydration, () => true, () => false);
  const items = [
    { v: "light", icon: Sun, label: t("light") },
    { v: "dark", icon: Moon, label: t("dark") },
    { v: "system", icon: Monitor, label: t("system") },
  ];
  const Current = !mounted ? Monitor : theme === "dark" ? Moon : theme === "light" ? Sun : Monitor;
  return (
    <DropdownMenu>
      <DropdownMenuTrigger aria-label={t("theme")} className={cn("grid size-9 place-items-center rounded-full text-muted-foreground hover:bg-accent hover:text-foreground", className)}>
        <Current className="size-4" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {items.map((i) => (
          <DropdownMenuItem key={i.v} onSelect={() => setTheme(i.v as "light" | "dark" | "system")} className="gap-2">
            <i.icon className="size-4" />
            {i.label}
            {mounted && theme === i.v && <Check className="ml-auto size-4" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function SimClockBadge({ className }: { className?: string }) {
  const { nowMs, ready } = useSimClock(15_000);
  const f = useFormat();
  const t = useTranslations("common");
  if (!ready) return null;
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-xs text-muted-foreground", className)} title={t("simClock")}>
      <span className="tnum">{f.date(new Date(nowMs).toISOString(), "datetime")}</span>
      <MockBadge what="clock" />
    </span>
  );
}

/**
 * "Today in the demo": the simulated date every countdown and deadline is measured from. A jump of the
 * demo clock shows here (and pulses), so a "144 days" never floats without its reference point.
 */
export function DemoToday({ className }: { className?: string }) {
  const { nowMs, ready } = useSimClock(15_000);
  const f = useFormat();
  const t = useTranslations("common");
  if (!ready) return null;
  const day = f.date(new Date(nowMs).toISOString());
  return (
    <motion.span
      key={day}
      initial={{ backgroundColor: "var(--attention-soft)" }}
      animate={{ backgroundColor: "rgba(0,0,0,0)" }}
      transition={{ duration: 2.4 }}
      className={cn("inline-flex items-center gap-1.5 rounded-md px-1 text-xs text-muted-foreground", className)}
      title={t("simClock")}
    >
      <span className="tnum">{t("today", { date: day })}</span>
      <MockBadge what="clock" />
    </motion.span>
  );
}

export interface Tab {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
  match?: (p: string) => boolean;
}

export function TabBar({ tabs }: { tabs: Tab[] }) {
  const pathname = usePathname();
  return (
    <nav className="sticky bottom-0 z-30 border-t bg-background/90 pb-safe backdrop-blur supports-backdrop-filter:bg-background/75" aria-label="Main">
      <ul className="mx-auto flex max-w-md">
        {tabs.map((tab) => {
          const active = tab.match ? tab.match(pathname) : pathname === tab.href;
          return (
            <li key={tab.href} className="flex-1">
              <Link
                href={tab.href}
                aria-current={active ? "page" : undefined}
                className={cn("relative flex flex-col items-center gap-0.5 pt-2.5 pb-1 text-[11px] font-medium transition-colors", active ? "text-foreground" : "text-muted-foreground hover:text-foreground")}
              >
                <span className="relative">
                  <tab.icon className="size-[22px]" />
                  {!!tab.badge && (
                    <motion.span
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="absolute -top-1 -right-2 grid min-w-4 place-items-center rounded-full bg-blocked px-1 text-[10px] leading-4 font-semibold text-white"
                    >
                      {tab.badge}
                    </motion.span>
                  )}
                </span>
                {tab.label}
                {active && <motion.span layoutId="tab-dot" className="absolute top-0 h-0.5 w-8 rounded-full bg-foreground" />}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

/** Phone-first column. On desktop it sits centred on a quiet grid so it reads as "the phone app". */
export function MobileFrame({ children, className }: { children: React.ReactNode; className?: string }) {
  const inFrame = useInFrame();
  return (
    <div className={cn("min-h-dvh", !inFrame && "md:hairline-grid md:py-8")}>
      <div
        className={cn(
          "relative mx-auto flex min-h-dvh w-full max-w-md flex-col bg-background",
          !inFrame && "md:min-h-[calc(100dvh-4rem)] md:overflow-hidden md:rounded-[28px] md:border md:shadow-lift",
          className,
        )}
      >
        {children}
      </div>
    </div>
  );
}

export function AppHeader({ left, right, className }: { left: React.ReactNode; right?: React.ReactNode; className?: string }) {
  return (
    <header className={cn("sticky top-0 z-30 flex h-14 items-center gap-2 bg-background/85 px-4 backdrop-blur supports-backdrop-filter:bg-background/70", className)}>
      <div className="min-w-0 flex-1">{left}</div>
      <div className="flex items-center gap-0.5">{right}</div>
    </header>
  );
}

export function DropdownSep() {
  return <DropdownMenuSeparator />;
}
