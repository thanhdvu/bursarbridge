"use client";

import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export type Tone = "verified" | "blocked" | "attention" | "route" | "neutral" | "mock";

const toneClass: Record<Tone, string> = {
  verified: "bg-verified-soft text-verified-ink",
  blocked: "bg-blocked-soft text-blocked-ink",
  attention: "bg-attention-soft text-attention-ink",
  route: "bg-route-soft text-route-ink",
  neutral: "bg-muted text-muted-foreground",
  mock: "bg-mock-soft text-mock",
};

const dotClass: Record<Tone, string> = {
  verified: "bg-verified",
  blocked: "bg-blocked",
  attention: "bg-attention",
  route: "bg-route",
  neutral: "bg-muted-foreground/60",
  mock: "bg-mock",
};

export function Pill({ tone = "neutral", children, className, dot, pulse }: { tone?: Tone; children: React.ReactNode; className?: string; dot?: boolean; pulse?: boolean }) {
  return (
    <span className={cn("inline-flex h-6 items-center gap-1.5 rounded-full px-2.5 text-xs font-medium whitespace-nowrap", toneClass[tone], className)}>
      {dot && (
        <span className="relative inline-flex size-1.5">
          {pulse && <span className={cn("absolute inset-0 rounded-full animate-pulse-ring", dotClass[tone])} />}
          <span className={cn("relative inline-flex size-1.5 rounded-full", dotClass[tone])} />
        </span>
      )}
      {children}
    </span>
  );
}

/** Honest, quiet label for anything simulated. */
export function MockBadge({ what = "generic", className }: { what?: "bank" | "clock" | "authenticator" | "chain" | "rate" | "bursar" | "generic" | "harness"; className?: string }) {
  const t = useTranslations("mock");
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          tabIndex={0}
          className={cn(
            "inline-flex h-[18px] cursor-help items-center rounded-[5px] border border-dashed border-mock/40 px-1.5 font-mono text-[10px] font-medium tracking-wider text-mock uppercase",
            className,
          )}
        >
          {t("label")}
        </span>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-64 text-pretty">
        {t(`why.${what}`)}
      </TooltipContent>
    </Tooltip>
  );
}

export function RuleId({ id, className }: { id: string; className?: string }) {
  return <span className={cn("rounded-[4px] bg-muted px-1 py-px font-mono text-[10.5px] text-muted-foreground", className)}>{id}</span>;
}
