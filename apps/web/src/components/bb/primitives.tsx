"use client";

import { AlertTriangle, Check, CircleDashed, Info, Loader2, X } from "lucide-react";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import type { Reason } from "@/lib/api/types";
import { RuleId } from "./badges";

export function Panel({ className, children, as: As = "section", ...rest }: { className?: string; children?: React.ReactNode; as?: "section" | "div" | "article" } & React.HTMLAttributes<HTMLElement>) {
  return (
    <As className={cn("surface rounded-2xl border bg-card text-card-foreground shadow-card", className)} {...rest}>
      {children}
    </As>
  );
}

export function SectionLabel({ children, className, action }: { children: React.ReactNode; className?: string; action?: React.ReactNode }) {
  return (
    <div className={cn("mb-2 flex items-center justify-between px-1", className)}>
      <h2 className="text-[13px] font-medium tracking-tight text-muted-foreground">{children}</h2>
      {action}
    </div>
  );
}

export type CheckState = "ok" | "fail" | "warn" | "running" | "pending" | "info";

export function CheckIcon({ state, className }: { state: CheckState; className?: string }) {
  const base = "grid size-5 shrink-0 place-items-center rounded-full";
  switch (state) {
    case "ok":
      return (
        <span className={cn(base, "bg-verified text-white", className)}>
          <Check className="size-3" strokeWidth={3} />
        </span>
      );
    case "fail":
      return (
        <span className={cn(base, "bg-blocked text-white", className)}>
          <X className="size-3" strokeWidth={3} />
        </span>
      );
    case "warn":
      return (
        <span className={cn(base, "bg-attention-soft text-attention-ink", className)}>
          <AlertTriangle className="size-3" strokeWidth={2.5} />
        </span>
      );
    case "running":
      return (
        <span className={cn(base, "text-route", className)}>
          <Loader2 className="size-4 animate-spin" />
        </span>
      );
    case "info":
      return (
        <span className={cn(base, "bg-route-soft text-route-ink", className)}>
          <Info className="size-3" strokeWidth={2.5} />
        </span>
      );
    default:
      return (
        <span className={cn(base, "text-muted-foreground/50", className)}>
          <CircleDashed className="size-4" />
        </span>
      );
  }
}

export function CheckRow({ state, title, detail, right, className }: { state: CheckState; title: React.ReactNode; detail?: React.ReactNode; right?: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex items-start gap-3 py-2", className)}>
      <CheckIcon state={state} className="mt-0.5" />
      <div className="min-w-0 flex-1">
        <div className="text-sm leading-snug font-medium">{title}</div>
        {detail && <div className="mt-0.5 text-xs leading-relaxed text-muted-foreground">{detail}</div>}
      </div>
      {right}
    </div>
  );
}

/** Line item row (Wise-style breakdown). */
export function Line({ label, value, strong, muted, hint, className }: { label: React.ReactNode; value: React.ReactNode; strong?: boolean; muted?: boolean; hint?: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex items-baseline justify-between gap-4 py-1.5", className)}>
      <div className={cn("text-sm", muted ? "text-muted-foreground" : "text-foreground/85")}>
        {label}
        {hint && <div className="text-xs text-muted-foreground">{hint}</div>}
      </div>
      <div className={cn("text-right text-sm tnum", strong && "text-base font-semibold")}>{value}</div>
    </div>
  );
}

/** Localised text for a policy Reason: text from code + params, rule ID as small print. */
export function ReasonText({ reason }: { reason: Reason }) {
  const t = useTranslations("reasons");
  const key = reason.code as Parameters<typeof t>[0];
  const has = t.has(key);
  return <>{has ? t(key, reason.params as Record<string, string>) : reason.code.replaceAll("_", " ").toLowerCase()}</>;
}

export function ReasonList({ reasons, className }: { reasons: Reason[]; className?: string }) {
  return (
    <ul className={cn("space-y-1", className)}>
      {reasons.map((r) => (
        <li key={r.ruleId + r.code}>
          <CheckRow
            state={r.severity === "block" ? "fail" : r.severity === "warn" ? "warn" : "ok"}
            title={<ReasonText reason={r} />}
            right={<RuleId id={r.ruleId} className="mt-0.5" />}
            className="py-1.5"
          />
        </li>
      ))}
    </ul>
  );
}

export function Initials({ name, className }: { name: string; className?: string }) {
  const parts = name.trim().split(/\s+/);
  const ini = /[一-鿿]/.test(name) ? name.slice(-1) : parts[parts.length - 1]?.[0] ?? "?";
  return (
    <span className={cn("grid size-9 place-items-center rounded-full bg-secondary text-sm font-semibold text-secondary-foreground", className)} aria-hidden>
      {ini}
    </span>
  );
}
