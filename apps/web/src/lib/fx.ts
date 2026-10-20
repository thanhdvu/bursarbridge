import type { Disclosure } from "@/lib/api/types";

/**
 * Rates can arrive as "receive per send" (live API: 0.0529 KRW per VND) or "send per receive" (18.73 VND per KRW).
 * People read "1 ₩ = 18.91 ₫", so always express the rate as send-currency per one receive unit.
 */
export function perReceiveUnit(rate: string | number) {
  const r = Number(rate);
  if (!r) return 0;
  return r < 1 ? 1 / r : r;
}

/** send is the total debit, fees included (API semantics). */
export function costVsMid(d: Pick<Disclosure, "send" | "receive" | "fx" | "fees">) {
  const total = Number(d.send.amount);
  const receive = Number(d.receive.amount);
  const mid = perReceiveUnit(d.fx.midRate);
  const atMid = receive * mid;
  const cost = total - atMid;
  return { total, receive, mid, rate: perReceiveUnit(d.fx.rate), fees: Number(d.fees.amount), converted: total - Number(d.fees.amount), cost, pct: atMid ? (cost / atMid) * 100 : 0 };
}
