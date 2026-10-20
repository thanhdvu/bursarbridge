import { cn } from "@/lib/utils";

/** Mark: two shores joined by one suspension span. The span is the only route money can take; the hangers are the checks. */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" aria-hidden className={cn("size-7", className)}>
      <defs>
        <linearGradient id="bb-mark" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="var(--brand)" />
          <stop offset="1" stopColor="var(--primary)" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill="url(#bb-mark)" className="dark:hidden" />
      <rect width="32" height="32" rx="9" className="hidden fill-[color:var(--stage)] stroke-[color:var(--brand)]/40 dark:block" strokeWidth="1" />
      {[11, 14, 18, 21].map((x) => (
        <path key={x} d={`M${x} 21.5V${x === 11 || x === 21 ? 17.6 : 15.9}`} strokeWidth="1.1" strokeLinecap="round" stroke="white" strokeOpacity="0.5" />
      ))}
      <path d="M6.5 21.5C9 13.4 23 13.4 25.5 21.5" fill="none" strokeWidth="2.4" strokeLinecap="round" stroke="white" />
      <path d="M6 21.5h20" strokeWidth="1.5" strokeLinecap="round" stroke="white" strokeOpacity="0.55" />
      <circle cx="6.5" cy="21.5" r="2.2" fill="white" />
      <circle cx="25.5" cy="21.5" r="2.2" fill="var(--verified)" stroke="white" strokeWidth="0.8" />
    </svg>
  );
}

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <LogoMark />
      {!compact && <span className="font-display text-[1.2rem] font-semibold tracking-tight">BursarBridge</span>}
    </span>
  );
}
