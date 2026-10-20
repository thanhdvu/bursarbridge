import type { Payment, Refund } from "@/lib/api/types";
import type { PathState } from "@/components/bb/money-path";
import type { Tone } from "@/components/bb/badges";

export function paymentPath(p: Payment): PathState {
  switch (p.status) {
    case "awaiting_approval":
      return "waiting";
    case "executing":
    case "sent":
      return "moving";
    case "received_by_bursar":
    case "matched":
      return "arrived";
    case "cancelled":
      return "returned";
    case "failed":
      return "blocked";
  }
}

export function paymentTone(p: Payment): Tone {
  if (p.status === "matched" || p.status === "received_by_bursar") return "verified";
  if (p.status === "cancelled" || p.status === "failed") return "neutral";
  return "route";
}

export const paymentSteps: Payment["status"][] = ["executing", "sent", "received_by_bursar", "matched"];

export function refundPath(r: Refund): PathState {
  if (r.status === "sent") return "returning";
  if (r.status === "received" || r.status === "reconciled") return "returned";
  return "arrived";
}

export function refundTone(r: Refund): Tone {
  if (r.status === "received" || r.status === "reconciled") return "verified";
  if (r.status === "manual_review") return "neutral";
  return "attention";
}

/** API v1.13: the refund exists from the student's signature (requested); received and reconciled land together at the promise. */
export const refundSteps: Refund["status"][] = ["requested", "acknowledged", "approved", "sent", "received"];
