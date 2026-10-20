"use client";

import { useQueryClient } from "@tanstack/react-query";
import { CalendarCheck, Clapperboard, FastForward, GraduationCap, Presentation, RotateCcw, Scale, UserRound, UserRoundCheck } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useMemo, useState, useSyncExternalStore } from "react";
import { toast } from "sonner";
import { apiBaseUrl, apiMode, createClient, serverApiMode, setApiMode } from "@/lib/api/client";
import { useFormat } from "@/lib/format";
import { setFamily, useFamily } from "@/lib/persona";
import { jumpToRefundPromise } from "@/lib/refund";
import { cn } from "@/lib/utils";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { MockBadge } from "./badges";
import { SimClockBadge, useInFrame } from "./shell";

function subscribeWide(cb: () => void) {
  const mq = window.matchMedia("(min-width: 768px)");
  mq.addEventListener("change", cb);
  return () => mq.removeEventListener("change", cb);
}

/** Persona switcher + demo controls. One person can play parent, student and judge. Hidden inside the demo stage frames. */
export function DemoDock({ className }: { className?: string }) {
  const t = useTranslations("demo");
  const inFrame = useInFrame();
  const family = useFamily();
  const qc = useQueryClient();
  const router = useRouter();
  const client = useMemo(() => createClient("judge"), []);
  const mode = useSyncExternalStore(() => () => {}, apiMode, serverApiMode);
  const [open, setOpen] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);
  const f = useFormat();
  const wide = useSyncExternalStore(subscribeWide, () => window.matchMedia("(min-width: 768px)").matches, () => true);
  if (inFrame) return null;

  const jumpPromise = async () => {
    try {
      const date = await jumpToRefundPromise(client, createClient(family === "wang" ? "parent_wang" : "parent_minh"));
      qc.invalidateQueries();
      if (date) toast(t("jumped", { date: f.date(date) }));
      else toast(t("noPromise"));
    } catch (e) {
      toast.error(String(e));
    }
  };

  const advance = async (days: number) => {
    try {
      await client.advanceClock({ days });
      qc.invalidateQueries();
      toast(t("advanced", { n: days }));
    } catch (e) {
      toast.error(String(e));
    }
  };

  const people = [
    { href: "/parent", icon: UserRound, label: family === "wang" ? "Wang" : "Minh", sub: t("parent") },
    { href: "/student", icon: GraduationCap, label: family === "wang" ? "Hao" : "Linh", sub: t("student") },
    { href: "/cosigner", icon: UserRoundCheck, label: "Lan", sub: t("cosigner") },
    { href: "/trust", icon: Scale, label: t("judge"), sub: t("judgeSub") },
    { href: "/demo", icon: Presentation, label: t("stage"), sub: t("stageSub") },
  ];

  const body = (
    <div className="space-y-4 p-4">
      {/* Mode and reset first: on a phone they must never sit below the fold. */}
      <div className="flex items-center justify-between gap-2 rounded-xl bg-muted p-1">
        {(["mock", "live"] as const).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => {
              if (m === mode) return;
              setApiMode(m);
              location.reload();
            }}
            title={m === "live" ? apiBaseUrl : t("mockTitle")}
            aria-pressed={mode === m}
            className={cn("flex-1 rounded-lg px-2 py-1.5 font-mono text-[11px] font-semibold", mode === m ? "bg-card shadow-sm" : "text-muted-foreground")}
          >
            API {m.toUpperCase()}
          </button>
        ))}
      </div>
      <div>
        <div className="mb-2 text-xs font-medium text-muted-foreground">{t("playAs")}</div>
        <div className="grid grid-cols-2 gap-2">
          {people.map((p) => (
            <Link key={p.href} href={p.href} onClick={() => setOpen(false)} className="flex items-center gap-2 rounded-xl border bg-card p-2.5 hover:bg-accent">
              <p.icon className="size-4 shrink-0 text-muted-foreground" />
              <span className="min-w-0">
                <span className="block truncate text-sm font-medium">{p.label}</span>
                <span className="block truncate text-[11px] text-muted-foreground">{p.sub}</span>
              </span>
            </Link>
          ))}
        </div>
      </div>
      <div>
        <div className="mb-2 text-xs font-medium text-muted-foreground">{t("family")}</div>
        <div className="grid grid-cols-2 gap-1 rounded-xl bg-muted p-1">
          {(["nguyen", "wang"] as const).map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => {
                setFamily(f);
                qc.invalidateQueries();
                router.refresh();
              }}
              className={cn("rounded-lg px-2 py-1.5 text-xs font-medium", family === f ? "bg-card shadow-sm" : "text-muted-foreground")}
            >
              {t(`families.${f}`)}
            </button>
          ))}
        </div>
      </div>
      <div>
        <div className="mb-2 flex items-center justify-between text-xs font-medium text-muted-foreground">
          {t("clock")}
          <SimClockBadge />
        </div>
        <div className="grid grid-cols-3 gap-2">
          {[1, 3, 14].map((d) => (
            <button key={d} type="button" onClick={() => advance(d)} className="inline-flex items-center justify-center gap-1 rounded-lg border bg-card px-2 py-1.5 text-xs font-medium hover:bg-accent">
              <FastForward className="size-3.5" />+{d}d
            </button>
          ))}
        </div>
        <button type="button" onClick={jumpPromise} className="mt-2 inline-flex w-full items-center justify-center gap-1.5 rounded-lg border bg-card px-2 py-1.5 text-xs font-medium hover:bg-accent">
          <CalendarCheck className="size-3.5" />
          {t("jumpPromise")}
        </button>
      </div>
      <div className="border-t pt-3">
        <button
          type="button"
          onClick={async () => {
            if (!confirmReset) {
              setConfirmReset(true);
              return;
            }
            await client.reset();
            try {
              Object.keys(localStorage)
                .filter((k) => k.startsWith("bb-thread-"))
                .forEach((k) => localStorage.removeItem(k));
            } catch {
              /* ignore */
            }
            qc.clear();
            toast.success(t("resetDone"));
            router.refresh();
            setTimeout(() => location.reload(), 200);
          }}
          className={cn(
            "inline-flex h-9 w-full items-center justify-center gap-1.5 rounded-lg text-xs font-medium",
            confirmReset ? "bg-blocked text-white" : "text-blocked hover:bg-blocked-soft",
          )}
        >
          <RotateCcw className="size-3.5" />
          {confirmReset ? t("resetAgain") : t("reset")}
        </button>
      </div>
    </div>
  );

  const header = (
    <div className="flex items-center justify-between border-b px-4 py-3">
      <div className="text-sm font-semibold">{t("title")}</div>
      <MockBadge what="generic" />
    </div>
  );

  const trigger = (
    <button
      type="button"
      onClick={wide ? undefined : () => setOpen(true)}
      className={cn(
        "fixed top-[38%] right-0 z-40 inline-flex h-11 w-6 items-center justify-center gap-2 rounded-l-lg border border-r-0 bg-popover opacity-70 hover:opacity-100 md:w-auto md:opacity-100 md:justify-start text-sm font-medium shadow-lift md:top-auto md:right-5 md:bottom-5 md:left-auto md:rounded-full md:border-r md:px-3.5",
        className,
      )}
      aria-label={t("open")}
    >
      <Clapperboard className="size-3.5 md:size-4" />
      <span className="hidden md:inline">{t("label")}</span>
    </button>
  );

  if (!wide)
    return (
      <>
        {trigger}
        <Sheet open={open} onOpenChange={(o) => { setOpen(o); if (!o) setConfirmReset(false); }}>
          <SheetContent side="bottom" className="mx-auto max-h-[85dvh] max-w-md gap-0 overflow-y-auto rounded-t-2xl pb-safe" onOpenAutoFocus={(e) => e.preventDefault()}>
            <SheetHeader className="border-b">
              <SheetTitle className="flex items-center gap-2">
                {t("title")} <MockBadge what="generic" />
              </SheetTitle>
              <SheetDescription className="sr-only">{t("open")}</SheetDescription>
            </SheetHeader>
            {body}
          </SheetContent>
        </Sheet>
      </>
    );

  return (
    <Popover open={open} onOpenChange={(o) => { setOpen(o); if (!o) setConfirmReset(false); }}>
      <PopoverTrigger asChild>{trigger}</PopoverTrigger>
      <PopoverContent
        side="top"
        align="end"
        collisionPadding={12}
        className="max-h-(--radix-popover-content-available-height) w-[min(92vw,340px)] gap-0 overflow-y-auto bg-popover p-0"
      >
        {header}
        {body}
      </PopoverContent>
    </Popover>
  );
}
