"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { PersonaProvider } from "@/lib/persona";
import { cn } from "@/lib/utils";
import { DemoDock } from "./demo-dock";
import { Logo } from "./logo";
import { LocaleSwitcher, ThemeToggle } from "./shell";

export function SiteHeader({ className }: { className?: string }) {
  const t = useTranslations("site.nav");
  const pathname = usePathname();
  const links = [
    { href: "/demo", label: t("demo") },
    { href: "/trust", label: t("trust") },
    { href: "/judge", label: t("judge") },
  ];
  return (
    <header className={cn("sticky top-0 z-40 border-b bg-background/80 backdrop-blur supports-backdrop-filter:bg-background/65", className)}>
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-4 px-4 sm:px-6">
        <Link href="/" className="shrink-0" aria-label="BursarBridge">
          <Logo />
        </Link>
        <nav className="no-scrollbar ml-2 flex min-w-0 items-center gap-1 overflow-x-auto" aria-label="Site">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              aria-current={pathname.startsWith(l.href) ? "page" : undefined}
              className={cn(
                "rounded-full px-3 py-1.5 text-sm whitespace-nowrap transition-colors",
                pathname.startsWith(l.href) ? "bg-secondary font-medium text-foreground" : "text-muted-foreground hover:text-foreground",
              )}
            >
              {l.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-0.5">
          <LocaleSwitcher />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}

/** Desktop surfaces (landing, trust center, judge console, demo stage) act as the judge persona. */
export function SiteSurface({ children, header = true }: { children: React.ReactNode; header?: boolean }) {
  return (
    <PersonaProvider persona="judge">
      {header && <SiteHeader />}
      {children}
      <DemoDock />
    </PersonaProvider>
  );
}
