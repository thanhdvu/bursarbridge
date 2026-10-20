import type { Money, Reconciliation } from "@/lib/api/types";

/**
 * Mock backend only: the API's MOCK return wire (refund_policy.reconciliation): KRW to USD to home
 * currency at 2% of the principal, plus a fixed intermediary fee. The UI reads Refund.estimate /
 * Refund.reconciliation instead (API v1.16) and never computes these figures itself.
 */
const cents = (n: number) => Math.round(n * 100) / 100;
const money = (n: number, currency: string): Money => ({ amount: n.toFixed(2), currency });

/** MOCK return wire (API v1.13): KRW to USD to home currency at 2% of the principal, plus a fixed intermediary fee. */
const RETURN_LOSS = 0.02;
const INTERMEDIARY: Record<string, number> = { VND: 375_000, CNY: 100 };

export function estimateReturn(send: Money, fees: Money | undefined): Reconciliation {
  const cur = send.currency;
  const sent = Number(send.amount);
  const outboundFee = fees && fees.currency === cur ? Number(fees.amount) : 0;
  const loss = cents((sent - outboundFee) * RETURN_LOSS);
  const intermediary = INTERMEDIARY[cur] ?? 0;
  return {
    sentOut: send,
    receivedBack: money(cents(sent - outboundFee - loss - intermediary), cur),
    conversion: { route: ["KRW", "USD", cur], source: "MOCK return wire board", lossPct: "2.00" },
    lines: [
      { code: "OUTBOUND_BANK_FEE", amount: money(outboundFee, cur), clause: "Original outward bank fee is not refunded" },
      { code: "FX_MOVEMENT_MOCK", amount: money(loss, cur), clause: "MOCK KRW to USD to home-currency conversion loss" },
      { code: "INTERMEDIARY_BANK_FEE_MOCK", amount: money(intermediary, cur), clause: "MOCK intermediary bank wire fee" },
      { code: "RETENTION", amount: money(0, cur), clause: "No admission fee charged; tuition-only claim, no dormitory or insurance payment" },
    ],
  };
}

