"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowUp, Check, ChevronDown, FileText, Mail, Paperclip, Scale, Sparkles, Upload, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useLocale, useTranslations } from "next-intl";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import type { AgentEvent, AgentMessage, Locale } from "@/lib/api/types";
import { apiMode } from "@/lib/api/client";
import { usePersona } from "@/lib/persona";
import { cn } from "@/lib/utils";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { RuleId } from "./badges";
import { AgentCard, ApprovalAfterLine, ApprovalRequiredCard } from "./cards";
import { isMine } from "@/lib/approval";
import { useApprovals } from "@/lib/queries";
import { CheckIcon } from "./primitives";
import { samples, type SampleDoc } from "@/mock/fixtures";
import { CoolingCard, useCoolingReviews } from "./review";
import { useErrorToast } from "@/lib/errors";
import { detectLocale } from "@/mock/agent-copy";

type StepEv = Extract<AgentEvent, { type: "step" }>;

interface LiveMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  events: AgentEvent[];
  docs?: string[];
  docIds?: string[];
  streaming?: boolean;
  /** Client-known phase before the first server event arrives. */
  phase?: { kind: "uploading"; n: number } | { kind: "thinking" };
}

function fromStored(m: AgentMessage): LiveMessage {
  const events = m.events ?? [];
  // Older/other backends persist only `text`: render steps, then text, then cards.
  const hasText = events.some((e) => e.type === "token");
  const evs = hasText || !m.text ? events : [...events.filter((e) => e.type === "step"), { type: "token", text: m.text } as AgentEvent, ...events.filter((e) => e.type !== "step")];
  return { id: m.id, role: m.role, text: m.text, events: evs, docs: m.documentIds?.map(() => ""), docIds: m.documentIds };
}

// ---------------------------------------------------------------------------

function StepsBlock({ steps, streaming }: { steps: StepEv[]; streaming: boolean }) {
  const t = useTranslations("chat");
  const [open, setOpen] = useState(false);
  const byId = new Map<string, StepEv>();
  steps.forEach((s) => byId.set(s.id, s));
  const list = [...byId.values()];
  const running = list.some((s) => s.status === "running");
  const failed = list.filter((s) => s.status === "failed").length;
  const expanded = open || running || streaming;
  return (
    <div className="rounded-xl border bg-card/60 px-3 py-2">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 text-left text-xs text-muted-foreground"
        aria-expanded={expanded}
      >
        <Sparkles className="size-3.5" />
        <span className={cn("font-medium", running && "shimmer-text")}>
          {running ? t("working") : failed ? t("checkedFailed", { n: list.length, failed }) : t("checked", { n: list.length })}
        </span>
        {!running && !streaming && <ChevronDown className={cn("ml-auto size-3.5 transition-transform", open && "rotate-180")} />}
      </button>
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.ol initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="mt-1">
            {list.map((s) => (
              <motion.li key={s.id} initial={{ opacity: 0, x: -4 }} animate={{ opacity: 1, x: 0 }} className="flex min-w-0 items-center gap-2 py-1 text-[13px]">
                <CheckIcon state={s.status === "done" ? "ok" : s.status === "failed" ? "fail" : "running"} className="size-4 [&_svg]:size-2.5" />
                <span className={cn("min-w-0 truncate", s.status === "running" && "shimmer-text", s.status === "failed" && "text-blocked-ink")}>{s.label}</span>
                {s.tool && <span className="ml-auto hidden truncate font-mono text-[10px] text-muted-foreground/70 sm:inline">{s.tool}</span>}
              </motion.li>
            ))}
          </motion.ol>
        )}
      </AnimatePresence>
    </div>
  );
}

function DispositionRow({ ev }: { ev: Extract<AgentEvent, { type: "disposition" }> }) {
  const t = useTranslations("chat.disposition");
  const tone = ev.result === "DENY" ? "text-blocked-ink bg-blocked-soft" : ev.result === "ESCALATE" ? "text-attention-ink bg-attention-soft" : "text-verified-ink bg-verified-soft";
  return (
    <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-muted-foreground">
      <Scale className="size-3.5" />
      <span>{t("engine")}</span>
      <span className={cn("rounded px-1.5 py-px font-medium", tone)}>{t(ev.result)}</span>
      <span className="flex flex-wrap gap-1">
        {ev.ruleIds.map((r) => (
          <RuleId key={r} id={r} />
        ))}
      </span>
    </div>
  );
}

/** Splits a finished reply into a short lead (what to do) and the rest, which folds away on a phone. */
function leadAndRest(text: string): [string, string] {
  const parts = text.trim().split(/(?<=[.!?])\s+|(?<=[。！？])/u).filter(Boolean);
  if (text.length <= 220 || parts.length < 3) return [text.trim(), ""];
  let lead = "";
  let n = 0;
  while (n < parts.length && (lead.length < 90 || n < 1) && lead.length + parts[n].length < 240) lead += (lead ? " " : "") + parts[n++];
  return n >= parts.length ? [text.trim(), ""] : [lead, parts.slice(n).join(" ")];
}

function FoldedReply({ text }: { text: string }) {
  const t = useTranslations("chat");
  const [open, setOpen] = useState(false);
  const [lead, more] = leadAndRest(text);
  return (
    <div>
      <p className="text-[15px] leading-relaxed whitespace-pre-wrap text-pretty">{lead}</p>
      {more && (
        <>
          <AnimatePresence initial={false}>
            {open && (
              <motion.p initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="mt-2 overflow-hidden text-[14px] leading-relaxed whitespace-pre-wrap text-pretty text-muted-foreground">
                {more}
              </motion.p>
            )}
          </AnimatePresence>
          <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} className="mt-1 inline-flex items-center gap-1 text-[13px] font-medium text-route-ink hover:underline">
            {open ? t("less") : t("more")}
            <ChevronDown className={cn("size-3.5 transition-transform", open && "rotate-180")} />
          </button>
        </>
      )}
    </div>
  );
}

function AssistantBody({ m, contextDocIds }: { m: LiveMessage; contextDocIds?: string[] }) {
  const steps = m.events.filter((e): e is StepEv => e.type === "step");
  const all = m.events.filter((e) => e.type !== "step" && e.type !== "envelope" && e.type !== "done");
  // A needs card already says what is missing (and carries the rule id); an amber ESCALATE line above it reads as alarm.
  const hasNeeds = all.some((e) => e.type === "card" && e.kind === "needs");
  // Finished replies lead with a short sentence above the cards; the longer explanation folds away below them.
  const reply = m.streaming ? "" : all.filter((e): e is Extract<AgentEvent, { type: "token" }> => e.type === "token").map((e) => e.text).join("").trim();
  const rest = reply ? all.filter((e) => e.type !== "token") : all;
  return (
    <div className="space-y-2.5">
      {steps.length > 0 && <StepsBlock steps={steps} streaming={!!m.streaming && all.length === 0} />}
      {reply && <FoldedReply text={reply} />}
      {rest.map((e, i) => {
        if (e.type === "token")
          return (
            <p key={i} className="text-[15px] leading-relaxed whitespace-pre-wrap text-pretty">
              {e.text.trim()}
              {m.streaming && i === rest.length - 1 && <span className="ml-0.5 inline-block h-4 w-1.5 translate-y-0.5 animate-pulse rounded-sm bg-foreground/60" />}
            </p>
          );
        if (e.type === "card") return <AgentCard key={i} kind={e.kind} data={e.data} contextDocIds={contextDocIds} />;
        if (e.type === "disposition") return hasNeeds ? null : <DispositionRow key={i} ev={e} />;
        if (e.type === "error") return <p key={i} className="text-sm text-blocked">{e.message}</p>;
        return null;
      })}
      {m.streaming && m.events.length === 0 && <WorkingLine phase={m.phase} />}
      {!m.streaming &&
        rest
          .filter((e): e is Extract<AgentEvent, { type: "card" }> => e.type === "card" && e.kind === "approval_required")
          .map((e, i) => {
            const id = (e.data.approvalId ?? e.data.id) as string | undefined;
            return id ? <ApprovalAfterLine key={`after-${i}`} approvalId={id} /> : null;
          })}
    </div>
  );
}

/** Loading the conversation: placeholders shaped like the thread, never an empty "Hi" screen that then jumps. */
function ThreadSkeleton() {
  return (
    <div className="mx-auto max-w-xl space-y-5" aria-busy="true">
      <div className="ml-auto h-9 w-2/3 animate-pulse rounded-2xl rounded-br-md bg-muted" />
      <div className="flex gap-2.5">
        <span className="size-7 shrink-0 animate-pulse rounded-full bg-muted" />
        <div className="flex-1 space-y-2">
          <div className="h-4 w-5/6 animate-pulse rounded bg-muted" />
          <div className="h-4 w-3/5 animate-pulse rounded bg-muted" />
          <div className="h-28 animate-pulse rounded-2xl bg-muted/70" />
        </div>
      </div>
    </div>
  );
}

/** Before the first step arrives: say what is actually happening, and admit it when it takes a while. */
function WorkingLine({ phase }: { phase?: LiveMessage["phase"] }) {
  const t = useTranslations("chat");
  const [slowFor, setSlowFor] = useState<LiveMessage["phase"]>();
  const slow = slowFor === phase;
  const kind = phase?.kind;
  useEffect(() => {
    if (kind !== "thinking") return;
    const id = setTimeout(() => setSlowFor(phase), 6000);
    return () => clearTimeout(id);
  }, [kind, phase]);
  const label = phase?.kind === "uploading" ? t("uploading", { n: phase.n }) : slow ? t("workingSlow") : t("reading");
  return (
    <div className="flex items-center gap-2 rounded-xl border bg-card/60 px-3 py-2 text-xs text-muted-foreground" role="status">
      <span className="flex gap-1" aria-hidden>
        {[0, 1, 2].map((i) => (
          <motion.span key={i} className="size-1.5 rounded-full bg-muted-foreground/60" animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1, repeat: Infinity, delay: i * 0.15 }} />
        ))}
      </span>
      <AnimatePresence mode="wait" initial={false}>
        <motion.span key={label} initial={{ opacity: 0, y: 2 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="shimmer-text font-medium">
          {label}
        </motion.span>
      </AnimatePresence>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Documents tray

/** Upload kind for a file (the API binds invoices, admissions and refusals to records; everything else is an email). */
export function kindOf(name: string): "invoice" | "admission" | "refusal" | "email" | "rental_agreement" {
  const s = samples.find((x) => x.filename === name || x.live === name);
  if (s) return s.uploadKind;
  const f = name.toLowerCase();
  if (/rental|lease|hop dong thue|임대|租约/.test(f)) return "rental_agreement";
  if (/refus|visa|decision|tu choi|거절|拒签/.test(f)) return "refusal";
  if (/admission|offer|nhap hoc|입학|录取/.test(f)) return "admission";
  if (/invoice|fee notice|hoa ?don|tuition|청구|学费|发票/.test(f) && !/discount|fake|giam/.test(f)) return "invoice";
  return "email";
}

async function sampleFile(s: SampleDoc): Promise<File> {
  // Live mode uploads the API's own synthetic fixtures so its parser and issuer records match.
  const live = apiMode() === "live";
  const name = live ? s.live : s.filename;
  try {
    const res = await fetch(`/samples/live/${s.live}`);
    if (res.ok) return new File([await res.blob()], name, { type: res.headers.get("content-type") ?? "application/octet-stream" });
  } catch {
    /* fall through */
  }
  return new File([`BursarBridge demo sample: ${s.id}`], name, { type: s.filename.endsWith(".eml") ? "message/rfc822" : "application/pdf" });
}

type DocTrayProps = { open: boolean; onOpenChange: (o: boolean) => void; onPick: (files: File[]) => void; preselect?: string[] };
export function DocTray(props: DocTrayProps) {
  return props.open ? <OpenDocTray {...props} /> : null;
}
function OpenDocTray({ open, onOpenChange, onPick, preselect }: DocTrayProps) {
  const t = useTranslations("docs");
  const input = useRef<HTMLInputElement>(null);
  const [picked, setPicked] = useState<string[]>(preselect ?? []);
  const group = (tone: SampleDoc["tone"][]) => samples.filter((s) => tone.includes(s.tone));
  // Forwarding often means several files at once (fee notice + admission letter): tap to select, then attach.
  const Item = ({ s }: { s: SampleDoc }) => {
    const on = picked.includes(s.id);
    return (
    <button
      type="button"
      aria-pressed={on}
      onClick={() => setPicked((p) => (on ? p.filter((x) => x !== s.id) : [...p, s.id]))}
      className={cn("flex w-full items-center gap-3 rounded-xl border bg-card p-3 text-left transition-colors hover:bg-accent", on && "border-foreground/40 bg-accent")}
    >
      <span className={cn("grid size-9 shrink-0 place-items-center rounded-lg", s.tone === "attack" ? "bg-blocked-soft text-blocked-ink" : "bg-secondary text-foreground")}>
        {s.kind === "email" ? <Mail className="size-4" /> : <FileText className="size-4" />}
      </span>
      <span className="min-w-0">
        <span className="block truncate text-sm font-medium">{t(`samples.${s.id}.title` as never)}</span>
        <span className="block truncate text-xs text-muted-foreground">{s.filename}</span>
      </span>
      <span className={cn("ml-auto grid size-5 shrink-0 place-items-center rounded-full border", on && "border-foreground bg-foreground text-background")} aria-hidden>
        {on && <Check className="size-3" strokeWidth={3} />}
      </span>
    </button>
    );
  };
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="bottom" className="mx-auto max-h-[85vh] max-w-md overflow-y-auto rounded-t-2xl">
        <SheetHeader>
          <SheetTitle>{t("trayTitle")}</SheetTitle>
          <SheetDescription>{t("trayHint")}</SheetDescription>
        </SheetHeader>
        <div className="space-y-4 px-4 pb-4">
          <button
            type="button"
            onClick={() => input.current?.click()}
            className="flex w-full items-center justify-center gap-2 rounded-xl border border-dashed p-4 text-sm font-medium hover:bg-accent"
          >
            <Upload className="size-4" /> {t("fromDevice")}
          </button>
          <input
            ref={input}
            type="file"
            multiple
            accept=".pdf,.eml,.txt,.png,.jpg,.jpeg"
            className="hidden"
            onChange={(e) => {
              const files = [...(e.target.files ?? [])];
              if (files.length) onPick(files);
              onOpenChange(false);
              e.target.value = "";
            }}
          />
          <div>
            <h3 className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">{t("fromSchool")}</h3>
            <div className="space-y-2">{group(["safe", "neutral"]).map((s) => <Item key={s.id} s={s} />)}</div>
          </div>
          <div>
            <h3 className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">{t("attacks")}</h3>
            <div className="space-y-2">{group(["attack"]).map((s) => <Item key={s.id} s={s} />)}</div>
          </div>
        </div>
        <div className="sticky bottom-0 border-t bg-popover/95 px-4 pt-3 pb-safe backdrop-blur">
          <button
            type="button"
            disabled={!picked.length}
            onClick={async () => {
              const files = await Promise.all(samples.filter((s) => picked.includes(s.id)).map(sampleFile));
              onPick(files);
              onOpenChange(false);
            }}
            className="h-12 w-full rounded-xl bg-primary text-[15px] font-medium text-primary-foreground transition-opacity disabled:opacity-30"
          >
            {t("attach", { n: picked.length })}
          </button>
        </div>
      </SheetContent>
    </Sheet>
  );
}

// ---------------------------------------------------------------------------

export function AgentChat({ suggestions, className, headerSlot }: { suggestions: string[]; className?: string; headerSlot?: React.ReactNode }) {
  const t = useTranslations("chat");
  const locale = useLocale() as Locale;
  const { client, persona, user } = usePersona();
  const qc = useQueryClient();
  const threadKey = `bb-thread-${apiMode()}-${persona}`;
  const thread = useQuery({
    queryKey: ["thread", persona],
    queryFn: async () => {
      let id: string | null = null;
      try {
        id = localStorage.getItem(threadKey);
      } catch {
        /* ignore */
      }
      if (id) {
        try {
          return await client.agent.thread(id);
        } catch {
          /* recreate */
        }
      }
      const created = await client.agent.createThread();
      try {
        localStorage.setItem(threadKey, created.threadId);
      } catch {
        /* ignore */
      }
      return client.agent.thread(created.threadId);
    },
  });
  const [live, setLive] = useState<LiveMessage[] | null>(null);
  const [text, setText] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [tray, setTray] = useState(false);
  const cooling = useCoolingReviews();
  // Anything waiting for this person's own signature stays reachable from a fresh conversation.
  const pendingAll = useApprovals("pending");
  const [trayPre, setTrayPre] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const sending = useRef(false);
  const seenCues = useRef(new Set<string>());
  const scroller = useRef<HTMLDivElement>(null);
  const stick = useRef(true);
  const ta = useRef<HTMLTextAreaElement>(null);
  const showError = useErrorToast();

  const stored = useMemo(() => thread.data?.messages.map(fromStored) ?? [], [thread.data?.messages]);
  const messages = busy && live ? live : stored;

  // grow the composer when text is set programmatically (demo cues, suggestions)
  useEffect(() => {
    const el = ta.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 140) + "px";
  }, [text]);

  // keep following the stream unless the user scrolled up
  useLayoutEffect(() => {
    const el = scroller.current;
    if (el && stick.current) el.scrollTop = el.scrollHeight;
  });

  const startNewThread = useCallback(async () => {
    const created = await client.agent.createThread();
    try {
      localStorage.setItem(threadKey, created.threadId);
    } catch {
      /* ignore */
    }
    setLive(null);
    await qc.invalidateQueries({ queryKey: ["thread", persona] });
  }, [client, persona, qc, threadKey]);

  useEffect(() => {
    // The needs card asks for specific documents: open the tray with those already selected.
    const open = (e: Event) => {
      const kinds = (e as CustomEvent<{ kinds?: string[] }>).detail?.kinds ?? [];
      setTrayPre(samples.filter((s) => kinds.includes(s.uploadKind)).map((s) => s.id));
      setTray(true);
    };
    window.addEventListener("bb-open-tray", open);
    return () => window.removeEventListener("bb-open-tray", open);
  }, []);

  useEffect(() => {
    const onNew = () => void startNewThread();
    window.addEventListener("bb-new-thread", onNew);
    return () => window.removeEventListener("bb-new-thread", onNew);
  }, [startNewThread]);

  // Demo stage cues: the presenter can pre-fill this composer from /demo.
  useEffect(() => {
    if (typeof BroadcastChannel === "undefined") return;
    const ch = new BroadcastChannel("bb-stage");
    const receive = async (msg: { data: unknown }) => {
      const cue = msg.data as { kind: string; id?: string; persona?: string; text?: string; sampleIds?: string[]; newThread?: boolean };
      if (cue.kind !== "cue" || (cue.persona && cue.persona !== persona)) return;
      if (cue.id) {
        if (seenCues.current.has(cue.id)) return;
        seenCues.current.add(cue.id);
      }
      if (cue.newThread) await startNewThread();
      if (cue.text !== undefined) setText(cue.text);
      if (cue.sampleIds?.length) {
        const picked = await Promise.all(samples.filter((s) => cue.sampleIds!.includes(s.id)).map(sampleFile));
        setFiles(picked);
      }
      ta.current?.focus();
    };
    ch.onmessage = receive;
    const pending = localStorage.getItem("bb-pending-cue");
    if (pending) {
      const queued = JSON.parse(pending);
      if (!queued.persona || queued.persona === persona) {
        localStorage.removeItem("bb-pending-cue");
        void receive({ data: queued });
      }
    }
    return () => ch.close();
  }, [persona, startNewThread]);

  const send = useCallback(
    async (overrideText?: string) => {
      const body = (overrideText ?? text).trim();
      // A ref, not just state: a quick double tap lands before React re-renders with busy=true.
      if ((!body && files.length === 0) || busy || sending.current || !thread.data) return;
      sending.current = true;
      setBusy(true);
      stick.current = true;
      const pending = files;
      setText("");
      setFiles([]);
      const userMsg: LiveMessage = { id: "u-" + Date.now(), role: "user", text: body, events: [], docs: pending.map((f) => f.name) };
      const asst: LiveMessage = {
        id: "a-" + Date.now(),
        role: "assistant",
        text: "",
        events: [],
        streaming: true,
        phase: pending.length ? { kind: "uploading", n: pending.length } : { kind: "thinking" },
      };
      setLive([...stored, userMsg, asst]);
      try {
        const docs = await Promise.all(pending.map((f) => client.documents.upload(f, kindOf(f.name))));
        userMsg.docIds = docs.map((x) => x.id);
        asst.phase = { kind: "thinking" };
        setLive([...stored, userMsg, { ...asst }]);
        const evs: AgentEvent[] = [];
        for await (const ev of client.agent.send(thread.data.threadId, { text: body, documentIds: docs.map((d) => d.id), locale: detectLocale(body, locale) })) {
          if (ev.type === "token") {
            const last = evs[evs.length - 1];
            if (last?.type === "token") evs[evs.length - 1] = { type: "token", text: last.text + ev.text };
            else evs.push(ev);
          } else if (ev.type !== "done") evs.push(ev);
          if (ev.type === "card" && (ev.kind === "approval_required" || ev.kind === "refund")) qc.invalidateQueries();
          setLive([...stored, userMsg, { ...asst, events: [...evs] }]);
        }
      } catch (e) {
        showError(e);
        // Nothing was answered: give the words and files back instead of letting them vanish.
        setText((cur) => cur || body);
        setFiles((cur) => (cur.length ? cur : pending));
      } finally {
        await qc.invalidateQueries({ queryKey: ["thread", persona] });
        await thread.refetch();
        sending.current = false;
        setBusy(false);
        setLive(null);
      }
    },
    [busy, client, files, locale, persona, qc, stored, text, thread, showError],
  );


  const firstName = user?.name.split(" ").slice(-1)[0] ?? "";

  return (
    <div className={cn("flex min-h-0 flex-1 flex-col", className)}>
      {headerSlot}
      <div
        ref={scroller}
        onScroll={(e) => {
          const el = e.currentTarget;
          stick.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
        }}
        className="min-h-0 flex-1 overflow-y-auto px-4 pt-4 pb-6"
        aria-live="polite"
      >
        {thread.isPending && <ThreadSkeleton />}
        {messages.length === 0 && thread.isSuccess && (
          <div className="mx-auto max-w-sm py-8 text-center">
            <div className="mx-auto mb-4 grid size-12 place-items-center rounded-2xl bg-primary text-primary-foreground">
              <Sparkles className="size-5" />
            </div>
            <h2 className="text-lg font-semibold tracking-tight">{t("emptyTitle", { name: firstName })}</h2>
            <p className="mt-1 text-sm text-pretty text-muted-foreground">{t(user?.role === "parent" ? "emptyBodyParent" : user?.familyId === "fam_wang" ? "emptyBodyRent" : "emptyBody")}</p>
            {/* A paused scam review must be visible even in a fresh conversation. */}
            {cooling.data?.map((a) => (
              <div key={a.id} className="mt-6 text-left">
                <CoolingCard approval={a} viewer={user ?? undefined} />
              </div>
            ))}
            {pendingAll.data
              ?.filter((a) => a.status === "pending" && isMine(a, user ?? undefined))
              .map((a) => (
                <div key={a.id} className="mt-6 text-left">
                  <ApprovalRequiredCard data={{ approvalId: a.id }} />
                </div>
              ))}
          </div>
        )}
        <div className="mx-auto max-w-xl space-y-5">
          {messages.map((m, idx) =>
            m.role === "user" ? (
              <motion.div key={m.id} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col items-end gap-1.5">
                {m.docs?.map((d, i) => (
                  <span key={`${d}-${i}`} className="inline-flex max-w-[80%] items-center gap-1.5 rounded-lg border bg-card px-2.5 py-1.5 text-xs">
                    <FileText className="size-3.5 text-muted-foreground" />
                    <span className="truncate">{d || t("document")}</span>
                  </span>
                ))}
                {m.text && <p className="max-w-[85%] rounded-2xl rounded-br-md bg-primary px-3.5 py-2 text-[15px] text-primary-foreground">{m.text}</p>}
              </motion.div>
            ) : (
              <motion.div key={m.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-2.5">
                <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-full bg-secondary">
                  <Sparkles className="size-3.5" />
                </span>
                <div className="min-w-0 flex-1">
                  <AssistantBody m={m} contextDocIds={messages[idx - 1]?.role === "user" ? messages[idx - 1].docIds : undefined} />
                </div>
              </motion.div>
            ),
          )}
        </div>
      </div>

      <div className="border-t bg-background/85 px-3 pt-2 pb-safe backdrop-blur supports-backdrop-filter:bg-background/70">
        {messages.length === 0 && thread.isSuccess && (
          <div className="no-scrollbar -mx-3 mb-2 flex gap-2 overflow-x-auto px-3">
            {suggestions.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => send(s)}
                className="shrink-0 rounded-full border bg-card px-3 py-1.5 text-[13px] whitespace-nowrap transition-colors hover:bg-accent"
              >
                {s}
              </button>
            ))}
          </div>
        )}
        {files.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-1.5">
            {files.map((f, i) => (
              <span key={f.name + i} className="inline-flex items-center gap-1.5 rounded-lg border bg-card py-1 pr-1 pl-2.5 text-xs">
                <FileText className="size-3.5 text-muted-foreground" />
                <span className="max-w-[200px] truncate">{f.name}</span>
                <button type="button" aria-label={t("remove")} onClick={() => setFiles(files.filter((_, j) => j !== i))} className="rounded p-0.5 hover:bg-accent">
                  <X className="size-3.5" />
                </button>
              </span>
            ))}
          </div>
        )}
        <form
          className="mx-auto flex max-w-xl items-end gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
        >
          <button type="button" onClick={() => { setTrayPre([]); setTray(true); }} aria-label={t("attach")} className="grid size-11 shrink-0 place-items-center rounded-full border bg-card text-muted-foreground hover:text-foreground">
            <Paperclip className="size-[18px]" />
          </button>
          <label className="sr-only" htmlFor="chat-input">
            {t("placeholder")}
          </label>
          <textarea
            id="chat-input"
            ref={ta}
            rows={1}
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              e.target.style.height = "auto";
              e.target.style.height = Math.min(e.target.scrollHeight, 140) + "px";
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                e.preventDefault();
                send();
              }
            }}
            placeholder={t("placeholder")}
            className="min-h-11 flex-1 resize-none rounded-[22px] border bg-card px-4 py-2.5 text-[15px] leading-[22px] outline-none [scrollbar-width:none] placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring/40"
          />
          <button
            type="submit"
            disabled={busy || !thread.data || (!text.trim() && files.length === 0)}
            aria-label={t("send")}
            className="grid size-11 shrink-0 place-items-center rounded-full bg-primary text-primary-foreground transition-opacity disabled:opacity-30"
          >
            <ArrowUp className="size-5" />
          </button>
        </form>
        <p className="mx-auto mt-1.5 max-w-xl text-center text-[10.5px] text-muted-foreground/80">{t("aiLabel")}</p>
      </div>
      <DocTray open={tray} onOpenChange={setTray} preselect={trayPre} onPick={(f) => setFiles((x) => [...x, ...f])} />
    </div>
  );
}
