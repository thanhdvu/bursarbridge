"use client";

import { ArrowRight, Bot, Check, FileSearch, Hand, KeyRound, Lock, OctagonX, Scale, ShieldCheck, Undo2 } from "lucide-react";
import { motion } from "motion/react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { MockBadge, Pill, RuleId } from "@/components/bb/badges";
import { MoneyPath } from "@/components/bb/money-path";
import { Panel } from "@/components/bb/primitives";
import { RealVsMocked } from "@/components/bb/real-vs-mocked";
import { SiteSurface } from "@/components/bb/site";
import { Logo } from "@/components/bb/logo";
import { useFormat } from "@/lib/format";
import { TUITION_KRW, vndFor } from "@/mock/fixtures";
import { cn } from "@/lib/utils";

const ease = [0.16, 1, 0.3, 1] as const;

export default function Landing() {
  return (
    <SiteSurface>
      <LandingBody />
    </SiteSurface>
  );
}

function LandingBody() {
  const t = useTranslations("landing");
  return (
    <main>
      {/* Hero: harbour night, the bridge carries the story */}
      <section className="stage-panel relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 opacity-[0.35] [background-image:radial-gradient(oklch(1_0_0/0.09)_1px,transparent_1px)] [background-size:22px_22px] [mask-image:radial-gradient(ellipse_at_30%_20%,black_20%,transparent_70%)]" aria-hidden />
        <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-4 pt-14 pb-20 sm:px-6 lg:grid-cols-[1.1fr_1fr] lg:pt-20 lg:pb-24">
          <motion.div className="stage-scope" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, ease }}>
            <p className="inline-flex items-center gap-2 rounded-full bg-white/[0.06] px-3 py-1 text-xs text-muted-foreground ring-1 ring-white/10">
              <span className="size-1.5 rounded-full bg-verified" />
              {t("eyebrow")}
            </p>
            <h1 className="mt-6 font-display text-[44px] leading-[1.02] font-medium tracking-[-0.025em] text-balance sm:text-[68px]">
              {t("h1")
                .split(/(?<=[.。])\s*/)
                .filter(Boolean)
                .map((part, i) => (
                  <span key={i} className={i === 1 ? "block italic text-[oklch(0.8_0.11_245)]" : "block"}>
                    {part}
                  </span>
                ))}
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-pretty text-muted-foreground">{t("lead")}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button asChild size="lg" className="h-12 rounded-xl bg-white px-6 text-[15px] text-[color:var(--stage)] hover:bg-white/90">
                <Link href="/demo">
                  {t("ctaDemo")} <ArrowRight className="size-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="h-12 rounded-xl border-white/20 bg-white/[0.04] px-5 text-[15px] text-white hover:bg-white/10 hover:text-white">
                <Link href="/parent">{t("ctaParent")}</Link>
              </Button>
              <Button asChild size="lg" variant="ghost" className="h-12 rounded-xl px-4 text-[15px] text-white/80 hover:bg-white/10 hover:text-white">
                <Link href="/trust">{t("ctaTrust")}</Link>
              </Button>
            </div>
            <p className="mt-6 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <MockBadge what="generic" /> {t("honest")}
            </p>
          </motion.div>
          <HeroVisual />
        </div>
      </section>

      {/* Problem */}
      <section className="border-y bg-card/50">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 py-14 sm:px-6 md:grid-cols-3">
          {(["s1", "s2", "s3"] as const).map((k, i) => (
            <motion.div key={k} initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.08, duration: 0.6, ease }}>
              <div className="font-display text-5xl font-medium tracking-tight tnum">{t(`stats.${k}.n`)}</div>
              <p className="mt-2 text-sm leading-relaxed text-pretty text-muted-foreground">{t(`stats.${k}.text`)}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Three moments */}
      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
        <SectionHead kicker={t("moments.kicker")} title={t("moments.title")} />
        <div className="mt-10 grid gap-5 md:grid-cols-3">
          <Moment icon={ShieldCheck} tone="verified" title={t("moments.pay.title")} body={t("moments.pay.body")}>
            <div className="space-y-1.5 text-xs">
              {(["c1", "c2", "c3"] as const).map((c) => (
                <div key={c} className="flex items-center gap-2">
                  <span className="grid size-4 place-items-center rounded-full bg-verified text-white">
                    <Check className="size-2.5" strokeWidth={3} />
                  </span>
                  {t(`moments.pay.${c}`)}
                </div>
              ))}
            </div>
          </Moment>
          <Moment icon={OctagonX} tone="blocked" title={t("moments.attack.title")} body={t("moments.attack.body")}>
            <div className="rounded-lg border border-blocked/30 bg-blocked-soft px-3 py-2 text-xs text-blocked-ink">
              <div className="font-semibold">{t("moments.attack.card")}</div>
              <div className="mt-1 flex flex-wrap gap-1">
                <RuleId id="PAY-02" />
                <RuleId id="TAINT-01" />
                <RuleId id="SCAM-02" />
              </div>
            </div>
          </Moment>
          <Moment icon={Undo2} tone="attention" title={t("moments.refund.title")} body={t("moments.refund.body")}>
            <MoneyPath compact state="returning" from={{ place: "Đà Nẵng" }} to={{ place: "Seoul" }} />
          </Moment>
        </div>
      </section>

      {/* Safe by construction */}
      <section className="border-y bg-card/50">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
          <SectionHead kicker={t("tiers.kicker")} title={t("tiers.title")} lead={t("tiers.lead")} />
          <div className="mt-10 grid gap-3 lg:grid-cols-5">
            {(
              [
                { k: "L0", icon: FileSearch, tone: "bg-muted text-muted-foreground" },
                { k: "L1", icon: Bot, tone: "bg-route-soft text-route-ink" },
                { k: "L2", icon: Scale, tone: "bg-verified-soft text-verified-ink" },
                { k: "L3", icon: KeyRound, tone: "bg-attention-soft text-attention-ink" },
                { k: "LX", icon: Hand, tone: "bg-blocked-soft text-blocked-ink" },
              ] as const
            ).map((tier, i) => (
              <motion.div key={tier.k} initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.06, duration: 0.5, ease }}>
                <Panel className="h-full p-4">
                  <div className="flex items-center gap-2">
                    <span className={cn("grid size-8 place-items-center rounded-lg", tier.tone)}>
                      <tier.icon className="size-4" />
                    </span>
                    <span className="font-mono text-sm font-semibold">{tier.k === "LX" ? "L-X" : tier.k}</span>
                  </div>
                  <div className="mt-3 font-semibold">{t(`tiers.${tier.k}.name`)}</div>
                  <p className="mt-1 text-sm leading-relaxed text-pretty text-muted-foreground">{t(`tiers.${tier.k}.body`)}</p>
                </Panel>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Proof */}
      <section className="mx-auto grid max-w-7xl items-center gap-10 px-4 py-20 sm:px-6 lg:grid-cols-2">
        <div>
          <SectionHead kicker={t("proof.kicker")} title={t("proof.title")} lead={t("proof.lead")} />
          <Button asChild variant="outline" className="mt-6 h-11 rounded-xl">
            <Link href="/trust">
              {t("proof.cta")} <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>
        <ChainVisual />
      </section>

      {/* Personas */}
      <section className="border-y bg-card/50">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
          <SectionHead kicker={t("people.kicker")} title={t("people.title")} />
          <div className="mt-10 grid gap-5 md:grid-cols-3">
            {(["minh", "linh", "judge"] as const).map((p) => (
              <Link key={p} href={p === "minh" ? "/parent" : p === "linh" ? "/student" : "/judge"} className="group">
                <Panel className="h-full p-5 transition-shadow group-hover:shadow-lift">
                  <div className="text-xs text-muted-foreground">{t(`people.${p}.role`)}</div>
                  <div className="mt-1 text-lg font-semibold">{t(`people.${p}.name`)}</div>
                  <p className="mt-2 text-sm leading-relaxed text-pretty text-muted-foreground">{t(`people.${p}.body`)}</p>
                  <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium">
                    {t(`people.${p}.cta`)} <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
                  </span>
                </Panel>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Honesty */}
      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
        <SectionHead kicker={t("rvm.kicker")} title={t("rvm.title")} lead={t("rvm.lead")} />
        <RealVsMocked className="mt-8" />
      </section>

      <footer className="border-t">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-4 px-4 py-8 text-xs text-muted-foreground sm:px-6">
          <Logo className="text-foreground" />
          <span>{t("footer.entry")}</span>
          <span className="ml-auto text-pretty">{t("footer.fictional")}</span>
        </div>
      </footer>
    </main>
  );
}

function SectionHead({ kicker, title, lead }: { kicker: string; title: string; lead?: string }) {
  return (
    <div className="max-w-2xl">
      <p className="text-sm font-medium text-brand-ink">{kicker}</p>
      <h2 className="mt-2 font-display text-4xl font-medium tracking-tight text-balance sm:text-5xl">{title}</h2>
      {lead && <p className="mt-3 leading-relaxed text-pretty text-muted-foreground">{lead}</p>}
    </div>
  );
}

function Moment({
  icon: Icon,
  tone,
  title,
  body,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  tone: "verified" | "blocked" | "attention";
  title: string;
  body: string;
  children: React.ReactNode;
}) {
  const toneCls = { verified: "bg-verified-soft text-verified-ink", blocked: "bg-blocked-soft text-blocked-ink", attention: "bg-attention-soft text-attention-ink" }[tone];
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6, ease }}>
      <Panel className="flex h-full flex-col p-5">
        <span className={cn("grid size-10 place-items-center rounded-xl", toneCls)}>
          <Icon className="size-5" />
        </span>
        <h3 className="mt-4 text-lg font-semibold">{title}</h3>
        <p className="mt-1.5 text-sm leading-relaxed text-pretty text-muted-foreground">{body}</p>
        <div className="mt-auto pt-5">{children}</div>
      </Panel>
    </motion.div>
  );
}

function HeroVisual() {
  const t = useTranslations("landing.hero");
  const f = useFormat();
  return (
    <motion.div initial={{ opacity: 0, y: 16, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: 0.8, delay: 0.15, ease }} className="relative mx-auto w-full max-w-md">
      <motion.div
        initial={{ rotate: 0, x: 0, y: 0 }}
        animate={{ rotate: 4, x: 22, y: -16 }}
        transition={{ delay: 0.9, duration: 0.8, ease }}
        className="absolute inset-x-6 top-4 rounded-2xl border border-blocked/30 bg-card p-4 shadow-card"
        aria-hidden
      >
        <div className="flex items-center gap-2 text-sm font-semibold text-blocked-ink">
          <OctagonX className="size-4" /> {t("blocked")}
        </div>
        <div className="mt-1 text-xs text-muted-foreground">{t("blockedSub")}</div>
      </motion.div>
      <Panel className="relative mt-16 p-5 shadow-[0_40px_80px_-30px_oklch(0_0_0/0.7)]">
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">{t("label")}</span>
          <Pill tone="attention" dot pulse>
            {t("waiting")}
          </Pill>
        </div>
        <div className="mt-3 text-xs text-muted-foreground">{t("pay")}</div>
        <div className="font-display text-[34px] leading-tight font-medium tracking-tight tnum">{f.money(Math.round(vndFor(TUITION_KRW)), "VND")}</div>
        <div className="mt-2 text-xs text-muted-foreground">{t("receives")}</div>
        <div className="font-display text-2xl font-medium tnum">{f.money(TUITION_KRW, "KRW")}</div>
        <MoneyPath className="mt-3" compact state="moving" from={{ place: "Đà Nẵng", sub: "Lotus Home Bank" }} to={{ place: "Seoul", sub: "Hanbit University" }} />
        <div className="mt-3 space-y-1.5 border-t pt-3 text-sm">
          {(["c1", "c2", "c3"] as const).map((c, i) => (
            <motion.div key={c} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.5 + i * 0.15 }} className="flex items-center gap-2">
              <span className="grid size-5 place-items-center rounded-full bg-verified text-white">
                <Check className="size-3" strokeWidth={3} />
              </span>
              {t(c)}
            </motion.div>
          ))}
        </div>
        <div className="mt-4 flex h-11 items-center justify-center gap-2 rounded-xl bg-primary text-sm font-medium text-primary-foreground">
          <Lock className="size-4" /> {t("cta")}
        </div>
      </Panel>
    </motion.div>
  );
}

function ChainVisual() {
  const t = useTranslations("landing.proof");
  const blocks = [
    { seq: 41, text: t("b1"), tone: "", h: "3f9a" },
    { seq: 42, text: t("b2"), tone: "", h: "c21e" },
    { seq: 43, text: t("b3"), tone: "bad", h: "" },
    { seq: 44, text: t("b4"), tone: "after", h: "77b0" },
  ];
  return (
    <ol className="space-y-2">
      {blocks.map((b, i) => (
        <motion.li
          key={b.seq}
          initial={{ opacity: 0, x: 12 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ delay: i * 0.12, duration: 0.5, ease }}
          className={cn("flex items-center gap-3 rounded-xl border bg-card px-4 py-3 text-sm shadow-card", b.tone === "bad" && "border-blocked/40 bg-blocked-soft", b.tone === "after" && "opacity-50")}
        >
          <span className="font-mono text-xs text-muted-foreground">#{b.seq}</span>
          <span className={cn("flex-1", b.tone === "bad" && "font-medium text-blocked-ink")}>{b.text}</span>
          <span className={cn("font-mono text-[11px]", b.tone === "bad" ? "text-blocked-ink" : "text-muted-foreground")}>{b.tone === "bad" ? t("mismatch") : `✓ ${b.h}`}</span>
        </motion.li>
      ))}
    </ol>
  );
}
