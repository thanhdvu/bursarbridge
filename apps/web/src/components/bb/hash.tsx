"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { shortHash } from "@/lib/format";
import { cn } from "@/lib/utils";

export function HashChip({ value, n = 6, className, label }: { value: string; n?: number; className?: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={() => {
        navigator.clipboard?.writeText(value).catch(() => {});
        setCopied(true);
        setTimeout(() => setCopied(false), 1200);
      }}
      title={value}
      aria-label={label ? `${label}: ${value}` : value}
      className={cn(
        "group inline-flex shrink-0 items-center gap-1 rounded-md bg-muted/70 px-1.5 whitespace-nowrap py-0.5 font-mono text-[11px] text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
        className,
      )}
    >
      {shortHash(value, n)}
      {copied ? <Check className="size-3 text-verified" /> : <Copy className="size-3 opacity-0 transition-opacity group-hover:opacity-60" />}
    </button>
  );
}
