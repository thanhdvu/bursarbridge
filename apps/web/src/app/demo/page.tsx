"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, FastForward, Laptop, Link2, RotateCcw, Send, Smartphone } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { MockBadge } from "@/components/bb/badges";
import { SimClockBadge } from "@/components/bb/shell";
import { AcademicJourney, ChainCatchup } from "@/components/bb/study-progress";
import { SiteSurface } from "@/components/bb/site";
import { createClient } from "@/lib/api/client";
import { useFormat } from "@/lib/format";
import { setFamily, useFamily, usePersona } from "@/lib/persona";
import { jumpToRefundPromise } from "@/lib/refund";
import { cn } from "@/lib/utils";

export default function DemoStage() {
  return (
    <SiteSurface>
      <Stage />
    </SiteSurface>
  );
}

type Cue = { kind: "cue"; id: string; persona: string; text?: string; sampleIds?: string[]; newThread?: boolean };

function cue(c: Omit<Cue, "kind" | "id">, navigate: (path: string) => void) {
  // Posted twice with one id: a phone that was re-rendering at that instant still gets it; the phone dedupes.
  const msg = { kind: "cue", id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`, ...c };
  if (window.matchMedia("(max-width: 1023px)").matches) {
    localStorage.setItem("bb-pending-cue", JSON.stringify(msg));
    navigate("/student");
    return;
  }
  if (typeof BroadcastChannel === "undefined") return;
  const ch = new BroadcastChannel("bb-stage");
  ch.postMessage(msg);
  setTimeout(() => {
    ch.postMessage(msg);
    ch.close();
  }, 450);
}

interface Scene {
  id: number;
  actions: { label: string; run: () => void | Promise<void>; icon?: "send" | "clock" | "open" | "link" }[];
}

function subscribeDesktop(listener: () => void) {
  const media = window.matchMedia("(min-width: 1024px)");
  media.addEventListener("change", listener);
  return () => media.removeEventListener("change", listener);
}

function Stage() {
  const t = useTranslations("stage");
  const router = useRouter();
  const sendCue = (c: Omit<Cue, "kind" | "id">) => cue(c, path => router.push(path));
  const { client } = usePersona();
  const f = useFormat();
  const qc = useQueryClient();
  const family = useFamily();
  const desktop = useSyncExternalStore(subscribeDesktop, () => window.matchMedia("(min-width: 1024px)").matches, () => false);
  const familyClient = useMemo(() => createClient(family === "wang" ? "student_hao" : "student_linh"), [family]);
  const plan = useQuery({ queryKey: ["study-plan", family, "stage"], queryFn: () => familyClient.studyPlan() });
  const [scene, setScene] = useState(1);
  const [parentSrc, setParentSrc] = useState("/parent");
  const [studentSrc, setStudentSrc] = useState("/student");
  const [nonce, setNonce] = useState(0);

  const advance = async (days: number) => {
    await client.advanceClock({ days });
    qc.invalidateQueries();
    toast(t("advanced", { n: days }));
  };
  const advanceHours = async (hours: number) => {
    await client.advanceClock({ hours });
    qc.invalidateQueries();
    toast(t("advancedHours", { n: hours }));
  };
  // Settlement follows the school's calendar (two weeks after classes start), not a fixed +N days.
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
  const openParent = (path: string) => { if (window.matchMedia("(max-width: 1023px)").matches) { router.push(path); return; } setParentSrc(path); setNonce(n => n + 1); };
  const openStudent = (path: string) => { if (window.matchMedia("(max-width: 1023px)").matches) { router.push(path); return; } setStudentSrc(path); setNonce(n => n + 1); };
  const reloadPhones = () => {
    if (!desktop) { router.push("/parent"); return; }
    setParentSrc("/parent");
    setStudentSrc("/student");
    setNonce(n => n + 1);
  };

  const linh = family === "wang" ? "student_hao" : "student_linh";
  const scenes: Scene[] = [
    { id: 1, actions: [{ label: t("a.openLimit"), icon: "open", run: () => openParent("/parent/mandate/new") }] },
    {
      id: 2,
      actions: [
        { label: t("a.cueVague"), icon: "send", run: () => sendCue({ persona: linh, text: "ba ơi chuyển tiền học kỳ 1 cho con nha" }) },
        { label: t("a.openTimeline"), icon: "open", run: () => openStudent("/student/timeline") },
        { label: t("a.openStudentChat"), icon: "open", run: () => openStudent("/student") },
        { label: t("a.cueInvoice"), icon: "send", run: () => sendCue({ persona: linh, text: "giấy tờ đây nè", sampleIds: ["admission", "invoice"] }) },
      ],
    },
    {
      id: 3,
      actions: [
        { label: t("a.openParent"), icon: "open", run: () => openParent("/parent") },
        { label: t("a.openFreeze"), icon: "open", run: () => openParent("/parent/freeze") },
        // The bank holds a new payment for 30 simulated minutes (cancel window); skip it to show PAID.
        { label: t("a.skipHold"), icon: "clock", run: () => advanceHours(1) },
      ],
    },
    {
      id: 4,
      actions: [
        { label: t("a.cueDiscount"), icon: "send", run: () => sendCue({ persona: linh, text: "trường gửi mail giảm 15% nè, chuyển luôn được không?", sampleIds: ["discount_email"] }) },
        { label: t("a.cuePolice"), icon: "send", run: () => sendCue({ persona: linh, text: "có người xưng công an bắt nộp tiền ký quỹ gấp, đừng nói với ai", sampleIds: ["police"] }) },
        { label: t("a.openLan"), icon: "open", run: () => openParent("/cosigner") },
        { label: t("a.backMinh"), icon: "open", run: () => openParent("/parent") },
      ],
    },
    {
      id: 5,
      actions: [
        { label: t("a.weekLater"), icon: "clock", run: () => advance(7) },
        { label: t("a.cueRefusal"), icon: "send", run: () => sendCue({ persona: linh, text: "visa bị từ chối rồi 😢 giờ sao", sampleIds: ["refusal"] }) },
        { label: t("a.plus3"), icon: "clock", run: () => advance(3) },
        { label: t("a.cueRedirect"), icon: "send", run: () => sendCue({ persona: linh, text: "có bên này nói lấy lại tiền nhanh trong 72h, đổi tài khoản nhận được không?", sampleIds: ["refund_agent_email"] }) },
        { label: t("a.jumpPromise"), icon: "clock", run: jumpPromise },
        { label: t("a.openParent"), icon: "open", run: () => openParent("/parent") },
      ],
    },
    { id: 6, actions: [{ label: t("a.openTrust"), icon: "link", run: () => void window.open("/trust", "_blank") }] },
    {
      id: 7,
      actions: [
        {
          label: t("a.wang"),
          icon: "open",
          run: () => {
            setFamily("wang");
            qc.invalidateQueries();
            reloadPhones();
          },
        },
        { label: t("a.openRent"), icon: "open", run: () => openParent("/parent/mandate/new?purpose=rent") },
        { label: t("a.cueRent"), icon: "send", run: () => sendCue({ persona: "student_hao", text: "爸爸，帮我付这个月的房租" }) },
        { label: t("a.cueLease"), icon: "send", run: () => sendCue({ persona: "student_hao", text: "这是我的租房合同", sampleIds: ["rental_agreement"] }) },
        { label: t("a.plus30"), icon: "clock", run: () => advance(30) },
      ],
    },
  ];

  return (
    <main className="mx-auto max-w-[1600px] px-4 pt-6 pb-16 sm:px-6">
      <ChainCatchup />
      <div className="lg:hidden">
        <div className="rounded-2xl border bg-card p-6 text-center">
          <Laptop className="mx-auto size-8 text-muted-foreground" />
          <h1 className="mt-3 text-xl font-semibold">{t("smallTitle")}</h1>
          <p className="mt-1 text-sm text-pretty text-muted-foreground">{t("smallBody")}</p>
          <div className="mt-4 grid gap-2">
            <Button asChild className="h-11 rounded-xl">
              <Link href="/parent">{t("openParent")}</Link>
            </Button>
            <Button asChild variant="outline" className="h-11 rounded-xl">
              <Link href="/student">{t("openStudent")}</Link>
            </Button>
          </div>
        </div>
        {/* On a phone the refund story is three steps; the clock jump is the one thing a phone cannot do by itself. */}
        <div className="mt-4 rounded-2xl border bg-card p-5">
          <h2 className="font-semibold">{t("phoneRefund.title")}</h2>
          <ol className="mt-3 space-y-3 text-sm">
            <li className="flex gap-3">
              <span className="grid size-6 shrink-0 place-items-center rounded-full bg-muted text-xs font-semibold">1</span>
              <span className="min-w-0 text-pretty">
                {t("phoneRefund.s1")}{" "}
                <Link href="/student" className="font-medium text-route-ink underline-offset-4 hover:underline">
                  {t("openStudent")}
                </Link>
              </span>
            </li>
            <li className="flex gap-3">
              <span className="grid size-6 shrink-0 place-items-center rounded-full bg-muted text-xs font-semibold">2</span>
              <span className="min-w-0 flex-1 text-pretty">
                {t("phoneRefund.s2")}
                <Button variant="outline" className="mt-2 h-10 w-full rounded-xl" onClick={jumpPromise}>
                  <FastForward className="size-4" /> {t("a.jumpPromise")}
                </Button>
              </span>
            </li>
            <li className="flex gap-3">
              <span className="grid size-6 shrink-0 place-items-center rounded-full bg-muted text-xs font-semibold">3</span>
              <span className="min-w-0 text-pretty">
                {t("phoneRefund.s3")}{" "}
                <Link href="/parent" className="font-medium text-route-ink underline-offset-4 hover:underline">
                  {t("openParent")}
                </Link>
              </span>
            </li>
          </ol>
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:mt-0 lg:grid lg:grid-cols-[300px_minmax(0,1fr)] lg:items-start 2xl:grid-cols-[320px_minmax(0,1fr)_300px]">
        {/* Script rail */}
        <aside className="no-scrollbar space-y-3 lg:sticky lg:top-20 lg:max-h-[calc(100dvh-6rem)] lg:overflow-y-auto">
          <div className="flex items-center justify-between">
            <h1 className="font-display text-2xl font-medium tracking-tight">{t("title")}</h1>
            <SimClockBadge />
          </div>
          <p className="text-sm text-pretty text-muted-foreground">{t("lead")}</p>
          <AcademicJourney plan={plan.data} client={familyClient} />
          <ol className="relative space-y-1.5 before:absolute before:top-4 before:bottom-4 before:left-[23px] before:w-px before:bg-border">
            {scenes.map((s) => (
              <li key={s.id} className="relative">
                <button
                  type="button"
                  onClick={() => setScene(s.id)}
                  className={cn("w-full rounded-xl border px-3 py-2.5 text-left transition-colors", scene === s.id ? "surface border-brand/25 bg-card shadow-card" : "border-transparent hover:bg-accent")}
                  aria-expanded={scene === s.id}
                >
                  <div className="flex items-center gap-2.5">
                    <span className={cn("relative grid size-6 shrink-0 place-items-center rounded-full text-xs font-semibold ring-4 ring-background transition-colors", scene === s.id ? "bg-brand text-white" : s.id < scene ? "bg-verified text-white" : "bg-muted text-muted-foreground")}>{s.id < scene ? "✓" : s.id}</span>
                    <span className="text-sm font-medium">{t(`scenes.${s.id}.title` as never)}</span>
                  </div>
                </button>
                <AnimatePresence initial={false}>
                  {scene === s.id && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                      <div className="space-y-2 pt-2 pr-3 pb-1 pl-11">
                        <p className="text-[13px] leading-relaxed text-pretty text-muted-foreground">{t(`scenes.${s.id}.cue` as never)}</p>
                        {s.id === 4 && <p className="text-[13px] leading-relaxed text-pretty text-muted-foreground">{t("scenes.4.cue2")}</p>}
                        <div className="flex flex-wrap gap-1.5">
                          {s.actions.map((a) => (
                            <button
                              key={a.label}
                              type="button"
                              onClick={() => a.run()}
                              className="inline-flex items-center gap-1.5 rounded-lg border border-brand/25 bg-brand-soft px-2.5 py-1.5 text-xs font-medium text-brand-ink transition-colors hover:bg-brand hover:text-white"
                            >
                              {a.icon === "send" ? <Send className="size-3.5" /> : a.icon === "clock" ? <FastForward className="size-3.5" /> : a.icon === "link" ? <ExternalLink className="size-3.5" /> : <Smartphone className="size-3.5" />}
                              {a.label}
                            </button>
                          ))}
                        </div>
                        <p className="text-[11px] text-muted-foreground/80">{t(`scenes.${s.id}.say` as never)}</p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </li>
            ))}
          </ol>
          <div className="flex items-center gap-2 border-t pt-3">
            <Button
              variant="ghost"
              size="sm"
              className="text-blocked hover:bg-blocked-soft hover:text-blocked"
              onClick={async () => {
                if (!confirm(t("resetConfirm"))) return;
                await client.reset();
                try {
                  Object.keys(localStorage)
                    .filter((k) => k.startsWith("bb-thread-"))
                    .forEach((k) => localStorage.removeItem(k));
                } catch {
                  /* ignore */
                }
                setFamily("nguyen");
                qc.clear();
                openParent("/parent");
                openStudent("/student");
                setNonce((n) => n + 1);
                setScene(1);
              }}
            >
              <RotateCcw className="size-4" /> {t("reset")}
            </Button>
            <MockBadge what="generic" className="ml-auto" />
          </div>
        </aside>

        {/* Phones */}
        {desktop && <section className="stage-panel stage-scope relative flex min-w-0 flex-wrap items-start justify-center gap-10 overflow-hidden rounded-[32px] px-6 pt-8 pb-6 shadow-lift lg:sticky lg:top-20">
          <div className="pointer-events-none absolute inset-0 opacity-30 [background-image:radial-gradient(oklch(1_0_0/0.08)_1px,transparent_1px)] [background-size:22px_22px] [mask-image:radial-gradient(ellipse_at_50%_0%,black_10%,transparent_65%)]" aria-hidden />
          <Phone key={`p-${nonce}`} src={parentSrc} label={parentSrc.startsWith("/cosigner") ? t("phoneLan") : family === "wang" ? t("phoneParentWang") : t("phoneParent")} />
          <Phone key={`s-${nonce}`} src={studentSrc} label={family === "wang" ? t("phoneStudentWang") : t("phoneStudent")} />
        </section>}

        {/* Live evidence */}
        <aside className="hidden 2xl:block">
          <LiveLog />
        </aside>
      </div>
    </main>
  );
}

function Phone({ src, label }: { src: string; label: string }) {
  const wrap = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(0.86);
  useEffect(() => {
    const fit = () => setScale(Math.max(0.6, Math.min(1, (window.innerHeight - 190) / 812)));
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);
  return (
    <figure className="flex flex-col items-center gap-2" ref={wrap}>
      <div style={{ width: 375 * scale, height: 812 * scale }} className="relative">
        <div
          style={{ transform: `scale(${scale})`, transformOrigin: "top left", width: 375, height: 812 }}
          className="absolute top-0 left-0 overflow-hidden rounded-[52px] border-[10px] border-neutral-950 bg-background shadow-[0_50px_90px_-30px_oklch(0_0_0/0.85),0_0_0_1px_oklch(1_0_0/0.14)]"
        >
          <div className="absolute top-2 left-1/2 z-10 h-6 w-28 -translate-x-1/2 rounded-full bg-neutral-900 dark:bg-neutral-800" aria-hidden />
          <iframe src={src} title={label} className="size-full border-0 pt-7" />
        </div>
      </div>
      <figcaption className="text-xs font-medium tracking-wide text-muted-foreground">{label}</figcaption>
    </figure>
  );
}

function LiveLog() {
  const t = useTranslations("stage");
  const f = useFormat();
  const { client } = usePersona();
  const audit = useQuery({ queryKey: ["audit"], queryFn: () => client.audit.all(), refetchInterval: 4000 });
  const entries = [...(audit.data?.entries ?? [])].reverse().slice(0, 14);
  return (
    <div className="sticky top-20">
      <div className="mb-2 flex items-center gap-2">
        <Link2 className="size-4 text-muted-foreground" />
        <h2 className="text-sm font-semibold">{t("log")}</h2>
        <Link href="/trust" className="ml-auto text-xs text-muted-foreground hover:text-foreground hover:underline">
          {t("openTrust")}
        </Link>
      </div>
      <ol className="space-y-1.5">
        <AnimatePresence initial={false}>
          {entries.map((e) => (
            <motion.li
              key={e.seq}
              layout
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn(
                "rounded-xl border bg-card px-3 py-2 text-xs",
                e.summary.startsWith("DENY") && "border-blocked/40 bg-blocked-soft",
                e.summary.startsWith("ESCALATE") && "border-attention/40",
                e.summary.startsWith("AUTO_EXECUTE") && "border-verified/40",
              )}
            >
              <div className="flex items-center gap-2 text-[10.5px] text-muted-foreground">
                <span className="font-mono">#{e.seq}</span>
                <span>{e.actor}</span>
                <span className="ml-auto tnum">{f.date(e.at, "time")}</span>
              </div>
              <p className="mt-0.5 line-clamp-2 leading-snug">{e.summary}</p>
            </motion.li>
          ))}
        </AnimatePresence>
      </ol>
    </div>
  );
}
