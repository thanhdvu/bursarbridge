"use client";

import { useQuery } from "@tanstack/react-query";
import { BadgeCheck, FileText, Mail, MessageCircle, TriangleAlert } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Pill, RuleId } from "@/components/bb/badges";
import { HashChip } from "@/components/bb/hash";
import { Panel } from "@/components/bb/primitives";
import { ReasonText } from "@/components/bb/primitives";
import { AppHeader, LocaleSwitcher, ThemeToggle } from "@/components/bb/shell";
import { Button } from "@/components/ui/button";
import { useFormat } from "@/lib/format";
import { usePersona } from "@/lib/persona";
import type { DocumentRecord } from "@/lib/api/types";
import { cn } from "@/lib/utils";

export default function DocumentsPage() {
  const t = useTranslations("docs");
  const f = useFormat();
  const { client, persona, mode } = usePersona();
  // GET /documents is a proposed contract addition (see docs/status/frontend.md); live mode degrades to empty.
  const docs = useQuery({
    queryKey: ["documents", persona],
    queryFn: async () => {
      try {
        const res = await (client as unknown as { documents: { list?: () => Promise<DocumentRecord[]> } }).documents.list?.();
        return res ?? [];
      } catch {
        return [];
      }
    },
  });
  void mode;

  return (
    <>
      <AppHeader
        left={<h1 className="text-lg font-semibold tracking-tight">{t("title")}</h1>}
        right={
          <>
            <LocaleSwitcher compact />
            <ThemeToggle />
          </>
        }
      />
      <main className="flex-1 space-y-4 px-4 pt-2 pb-8">
        <p className="px-1 text-sm text-pretty text-muted-foreground">{t("lead")}</p>
        <div className="flex gap-2 px-1 text-xs">
          <Pill tone="verified">
            <BadgeCheck className="size-3.5" />
            {t("prov.verified_issuer")}
          </Pill>
          <Pill tone="neutral">{t("prov.untrusted_doc")}</Pill>
        </div>

        {docs.isPending && <Panel className="h-40 animate-pulse" />}
        {docs.data?.length === 0 && (
          <Panel className="flex flex-col items-center p-8 text-center">
            <FileText className="size-8 text-muted-foreground" />
            <p className="mt-3 text-sm text-muted-foreground">{t("empty")}</p>
            <Button asChild className="mt-4 rounded-xl">
              <Link href="/student">
                <MessageCircle className="size-4" /> {t("forward")}
              </Link>
            </Button>
          </Panel>
        )}

        {[...(docs.data ?? [])].reverse().map((d) => (
          <Panel key={d.id} className="p-4">
            <div className="flex items-start gap-3">
              <span className={cn("grid size-10 shrink-0 place-items-center rounded-xl", d.warnings.length ? "bg-blocked-soft text-blocked-ink" : "bg-secondary")}>
                {d.kind === "email" ? <Mail className="size-5" /> : <FileText className="size-5" />}
              </span>
              <div className="min-w-0 flex-1">
                <div className="truncate font-medium">{d.filename}</div>
                <div className="mt-0.5 flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
                  {t(`kind.${d.kind}`)}
                  {d.uploadedAt && <span>· {f.date(d.uploadedAt, "datetime")}</span>}
                  <HashChip value={d.sha256} n={6} />
                </div>
              </div>
            </div>
            {/* The raw extracted text is context, not a field: show it as a quiet excerpt. */}
            {d.fields
              .filter((fl) => fl.name === "text" && fl.value)
              .map((fl) => (
                <figure key="text" className="mt-3 rounded-xl bg-subtle px-3 py-2.5">
                  <figcaption className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">{t("readText")}</figcaption>
                  <p className="mt-1 line-clamp-3 text-xs leading-relaxed whitespace-pre-line text-muted-foreground">{String(fl.value).trim()}</p>
                </figure>
              ))}
            {d.fields.some((fl) => fl.name !== "text") && (
            <dl className="mt-3 divide-y rounded-xl border">
              {d.fields.filter((fl) => fl.name !== "text").map((fl) => (
                <div key={fl.name} className="flex items-center justify-between gap-3 px-3 py-2 text-sm">
                  <dt className="text-muted-foreground">{t.has(`field.${fl.name}` as never) ? t(`field.${fl.name}` as never) : fl.name}</dt>
                  <dd className="flex min-w-0 items-center gap-2 text-right">
                    <span className="truncate font-medium">{fl.value}</span>
                    {fl.provenance === "verified_issuer" ? (
                      <BadgeCheck className="size-4 shrink-0 text-verified" aria-label={t("prov.verified_issuer")} />
                    ) : (
                      <span className="size-2 shrink-0 rounded-full bg-muted-foreground/40" aria-label={t("prov.untrusted_doc")} />
                    )}
                  </dd>
                </div>
              ))}
            </dl>
            )}
            {d.warnings.length > 0 && (
              <ul className="mt-3 space-y-1.5">
                {d.warnings.map((w) => (
                  <li key={w.ruleId} className="flex items-start gap-2 text-xs text-blocked-ink">
                    <TriangleAlert className="mt-px size-3.5 shrink-0" />
                    <span className="flex-1">
                      <ReasonText reason={w} />
                    </span>
                    <RuleId id={w.ruleId} />
                  </li>
                ))}
              </ul>
            )}
          </Panel>
        ))}
      </main>
    </>
  );
}
