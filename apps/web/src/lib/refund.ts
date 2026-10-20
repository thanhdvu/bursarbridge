"use client";

import { useQuery } from "@tanstack/react-query";
import type { Approval, Refund } from "@/lib/api/types";
import { usePersona } from "@/lib/persona";

/**
 * The refund story in the words a family uses: what comes back, when, to which account, and why
 * it is a little less than what went out. Every figure comes from the API: `estimate` (MOCK
 * projection) before the money lands, `reconciliation` (bank-recorded) after. The UI computes none.
 */

export type RefundPhase = "manual" | "waiting" | "wiring" | "back";

export function refundPhase(r: Refund): RefundPhase {
  if (r.status === "manual_review" || (!r.deadline && !r.reconciliation)) return "manual";
  if (r.status === "received" || r.status === "reconciled") return "back";
  if (r.status === "sent") return "wiring";
  return "waiting";
}

/** The signed forms (Refund.paperwork) or, before filing, the prepared ones (Approval.rawAction.paperwork). */
export function formsOf(r: Refund | undefined, a?: Approval) {
  const docs = r?.paperwork?.documents ?? (a?.rawAction as { paperwork?: Refund["paperwork"] } | undefined)?.paperwork?.documents ?? [];
  return {
    withdrawal: docs.find((d) => d.kind === "admission_withdrawal"),
    application: docs.find((d) => d.kind === "tuition_refund_application"),
    denial: docs.find((d) => d.kind === "visa_denial_letter"),
  };
}

export const promiseDays = (r: Pick<Refund, "policy" | "paperwork">) => r.policy?.paymentWithinDaysAfterClassesStart ?? r.paperwork?.policy?.paymentWithinDaysAfterClassesStart ?? 14;

/**
 * Everything the refund screens need. The payment gives "what went out" before the bank's
 * reconciliation exists; the approval gives the consent-bound form previews.
 */
export function useRefundStory(refund: Refund | undefined) {
  const { client, persona } = usePersona();
  const hash = refund?.paperwork?.documents?.find((d) => d.consentHash)?.consentHash;
  const approvals = useQuery({
    queryKey: ["approvals", persona, "all"],
    queryFn: () => client.approvals.list("all"),
    enabled: !!refund,
  });
  const approval = approvals.data?.find((a) => a.action === "refund_claim" && (hash ? a.consentHash === hash : (a.rawAction as { paymentId?: string }).paymentId === refund?.paymentId));
  const actual = refund?.reconciliation ?? null;
  const estimate = !actual && refund && refundPhase(refund) !== "manual" ? (refund.estimate ?? null) : null;
  const statement = actual ?? estimate;
  const less = statement ? Number(statement.sentOut.amount) - Number(statement.receivedBack.amount) : null;
  const backAt = refund?.timeline.find((x) => x.code === "refund_received")?.at;
  const requestedAt = refund?.timeline.find((x) => x.code === "refund_requested")?.at ?? refund?.paperwork?.requestedAt;
  return { approval, statement, actual, estimate, less, backAt, requestedAt };
}

/** Opens a consent-bound form (authenticated PDF) without putting a token in a URL. */
export async function openPaperwork(fetchPdf: () => Promise<Blob>, filename = "form.pdf") {
  // Open the tab inside the tap so phones do not block it, then point it at the PDF once fetched.
  const w = typeof window !== "undefined" ? window.open("", "_blank") : null;
  try {
    const blob = await fetchPdf();
    const url = URL.createObjectURL(blob);
    if (w) w.location.href = url;
    else {
      const a = document.createElement("a");
      a.href = url;
      // Popups blocked (some in-app browsers): save the file instead of losing the tap.
      a.download = filename;
      a.click();
    }
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  } catch (e) {
    w?.close();
    throw e;
  }
}

type ClockClient = { clock: () => Promise<{ now: string }>; advanceClock: (b: { hours: number }) => Promise<unknown> };
type RefundReader = { refunds: { list: () => Promise<Refund[]> } };

/** The public API caps one clock move at 31 days (744 h), the same bound Journey.advance_refund() keeps. */
const MAX_HOURS = 31 * 24;

/**
 * Moves the simulated clock to the school's promise date for the family's open refund, in steps the
 * public clock limit accepts. Returns the promise date, or null when no filed refund is waiting for one.
 */
export async function jumpToRefundPromise(judge: ClockClient, family: RefundReader) {
  const refunds = await family.refunds.list();
  const open = refunds.find((r) => r.deadline && r.status !== "received" && r.status !== "reconciled" && r.status !== "manual_review");
  if (!open?.deadline) return null;
  let hours = Math.ceil((Date.parse(open.deadline) - Date.parse((await judge.clock()).now)) / 3_600_000);
  while (hours > 0) {
    const chunk = Math.min(hours, MAX_HOURS);
    await judge.advanceClock({ hours: chunk });
    hours -= chunk;
  }
  return open.deadline;
}
