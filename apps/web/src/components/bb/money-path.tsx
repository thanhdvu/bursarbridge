"use client";

import { motion, useAnimationFrame, useReducedMotion } from "motion/react";
import { useId, useMemo, useRef } from "react";
import { cn } from "@/lib/utils";

export type PathState = "idle" | "waiting" | "moving" | "arrived" | "returning" | "returned" | "blocked";

type P = [number, number];
function bez(p0: P, p1: P, p2: P, p3: P, t: number): P {
  const u = 1 - t;
  return [
    u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1],
  ];
}

/**
 * The bridge: BursarBridge's signature. A suspension arc from Đà Nẵng to Seoul; its hangers are the checks
 * that hold the payment up, and the packet's motion is the state: it waits at home, crosses, lands;
 * on refund it crosses back; on an attack it hits the guard mid-span and stops.
 */
export function MoneyPath({
  state,
  from,
  to,
  className,
  compact = false,
  hero = false,
}: {
  state: PathState;
  from: { place: string; sub?: string };
  to: { place: string; sub?: string };
  className?: string;
  compact?: boolean;
  /** Larger, display version for landing and approval. */
  hero?: boolean;
}) {
  const pathRef = useRef<SVGPathElement>(null);
  const dotRef = useRef<SVGGElement>(null);
  const tailRef = useRef<SVGPathElement>(null);
  const reduce = useReducedMotion();
  const uid = useId().replace(/:/g, "");
  const W = 320;
  const H = compact ? 86 : hero ? 132 : 118;
  const y = H - 22;
  const rise = compact ? 60 : hero ? 104 : 88;
  const d = `M 28 ${y} C 104 ${y - rise}, 216 ${y - rise}, 292 ${y}`;

  // Hangers: sample the arc at evenly spaced x and drop a line to the deck.
  const hangers = useMemo(() => {
    const A: P = [28, y];
    const B: P = [292, y];
    const c1: P = [104, y - rise];
    const c2: P = [216, y - rise];
    const n = compact ? 9 : 13;
    const pts: P[] = [];
    for (let i = 1; i <= n; i++) {
      const target = A[0] + (B[0] - A[0]) * (i / (n + 1));
      let lo = 0;
      let hi = 1;
      for (let k = 0; k < 18; k++) {
        const mid = (lo + hi) / 2;
        if (bez(A, c1, c2, B, mid)[0] < target) lo = mid;
        else hi = mid;
      }
      pts.push(bez(A, c1, c2, B, (lo + hi) / 2));
    }
    return pts;
  }, [compact, y, rise]);

  const travelling = state === "moving" || state === "returning";
  const reverse = state === "returning" || state === "returned";
  const built = state !== "idle";
  const homeLit = state === "returned";
  const awayLit = state === "arrived";

  useAnimationFrame((t) => {
    const p = pathRef.current;
    const dot = dotRef.current;
    if (!p || !dot) return;
    const len = p.getTotalLength();
    let k: number;
    if (state === "idle" || state === "waiting" || state === "returned") k = 0;
    else if (state === "arrived") k = 1;
    else if (state === "blocked") k = 0.5;
    else {
      // ease in and out of each crossing so the packet reads as travelling, not spinning
      const raw = reduce ? 0.5 : (t / 3200) % 1;
      const e = raw < 0.5 ? 2 * raw * raw : 1 - Math.pow(-2 * raw + 2, 2) / 2;
      k = state === "returning" ? 1 - e : e;
    }
    const pt = p.getPointAtLength(len * k);
    dot.setAttribute("transform", `translate(${pt.x} ${pt.y})`);
    const tail = tailRef.current;
    if (tail) {
      const seg = len * 0.2;
      const pos = len * k;
      // the comet tail trails behind the packet, in its direction of travel
      const start = state === "returning" ? pos : Math.max(0, pos - seg);
      const size = state === "returning" ? Math.min(seg, len - pos) : Math.min(seg, pos);
      tail.style.strokeDasharray = `${size} ${len * 2}`;
      tail.style.strokeDashoffset = `${-start}`;
    }
  });

  const tone =
    state === "blocked"
      ? "var(--blocked)"
      : state === "arrived" || state === "returned"
        ? "var(--verified)"
        : state === "idle"
          ? "var(--muted-foreground)"
          : "var(--brand)";
  const gy = y - rise * 0.75;

  return (
    <div className={cn("relative w-full select-none", className)}>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full overflow-visible" role="img" aria-label={`${from.place} → ${to.place}`}>
        <defs>
          <linearGradient id={`span-${uid}`} x1="0" x2="1">
            <stop offset="0%" stopColor={tone} stopOpacity={reverse ? 1 : 0.35} />
            <stop offset="100%" stopColor={tone} stopOpacity={reverse ? 0.35 : 1} />
          </linearGradient>
          <linearGradient id={`deck-${uid}`} x1="0" x2="1">
            <stop offset="0%" stopColor="var(--foreground)" stopOpacity="0.06" />
            <stop offset="50%" stopColor="var(--foreground)" stopOpacity="0.2" />
            <stop offset="100%" stopColor="var(--foreground)" stopOpacity="0.06" />
          </linearGradient>
          <radialGradient id={`glow-${uid}`}>
            <stop offset="0%" stopColor={tone} stopOpacity="0.5" />
            <stop offset="100%" stopColor={tone} stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* deck and water line */}
        <line x1={28} y1={y} x2={292} y2={y} stroke={`url(#deck-${uid})`} strokeWidth="1.5" />
        {!compact && (
          <line x1={58} y1={y + 8} x2={262} y2={y + 8} stroke="var(--foreground)" strokeOpacity="0.07" strokeWidth="1" strokeDasharray="1 6" strokeLinecap="round" />
        )}

        {/* hangers: the checks that hold the payment up */}
        {hangers.map(([hx, hy], i) => (
          <motion.line
            key={i}
            x1={hx}
            x2={hx}
            y1={y}
            y2={hy}
            stroke={built ? tone : "var(--border)"}
            strokeWidth="1"
            strokeLinecap="round"
            initial={false}
            animate={{
              pathLength: built ? 1 : 0.0001,
              opacity: built ? (state === "blocked" && Math.abs(i - (hangers.length - 1) / 2) < 1.5 ? 0.12 : 0.34) : 0.6,
            }}
            transition={{ duration: reduce ? 0 : 0.5, delay: reduce ? 0 : 0.15 + i * 0.045, ease: [0.16, 1, 0.3, 1] }}
          />
        ))}

        {/* the span: dashed while planned, drawn as it is built */}
        <path d={d} fill="none" stroke="var(--border)" strokeWidth="1.5" strokeDasharray="2 5" strokeLinecap="round" />
        <motion.path
          ref={pathRef}
          d={d}
          fill="none"
          stroke={`url(#span-${uid})`}
          strokeWidth={hero ? 3 : 2.5}
          strokeLinecap="round"
          initial={false}
          animate={{ pathLength: !built ? 0 : state === "blocked" ? 0.5 : 1, opacity: built ? 1 : 0 }}
          transition={{ duration: reduce ? 0 : 1.1, ease: [0.16, 1, 0.3, 1] }}
        />
        {travelling && !reduce && <path ref={tailRef} d={d} fill="none" stroke={tone} strokeOpacity="0.85" strokeWidth={hero ? 4 : 3.5} strokeLinecap="round" />}

        {state === "blocked" && (
          <motion.g
            initial={{ scale: 0.4, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: "spring", stiffness: 380, damping: 18, delay: reduce ? 0 : 0.6 }}
            style={{ transformOrigin: `160px ${gy}px` }}
          >
            <circle cx="160" cy={gy} r="14" fill="var(--blocked-soft)" stroke="var(--blocked)" strokeWidth="1.5" />
            <path d={`M 155.5 ${gy - 4.5} L 164.5 ${gy + 4.5} M 164.5 ${gy - 4.5} L 155.5 ${gy + 4.5}`} stroke="var(--blocked)" strokeWidth="2" strokeLinecap="round" />
          </motion.g>
        )}

        {/* pylons */}
        {[28, 292].map((x, i) => {
          const lit = (i === 1 && awayLit) || (i === 0 && homeLit);
          return (
            <g key={x} transform={`translate(${x} ${y})`}>
              {lit && !reduce && (
                <motion.circle r="10" fill="none" stroke="var(--verified)" strokeWidth="1.5" initial={{ scale: 0.8, opacity: 0.7 }} animate={{ scale: 2.1, opacity: 0 }} transition={{ duration: 1.6, repeat: 2, ease: "easeOut" }} />
              )}
              <circle r="10" fill="var(--card)" stroke={lit ? "var(--verified)" : "var(--border)"} strokeWidth="1.5" />
              {lit ? (
                <path d="M -4 0.2 L -1.2 3 L 4.2 -2.8" fill="none" stroke="var(--verified)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              ) : (
                <circle r="3.75" fill={i === 0 ? "var(--foreground)" : "var(--muted-foreground)"} />
              )}
            </g>
          );
        })}

        {state !== "idle" && state !== "blocked" && !homeLit && !awayLit ? (
          <g ref={dotRef}>
            {travelling && <circle r="15" fill={`url(#glow-${uid})`} />}
            <circle r={hero ? 6.5 : 5.5} fill={tone} stroke="var(--card)" strokeWidth="2" />
          </g>
        ) : (
          <g ref={dotRef} />
        )}
      </svg>
      <div className={cn("mt-1 flex items-start justify-between gap-4", hero ? "text-sm" : "text-xs")}>
        <div className="min-w-0">
          <div className="truncate font-medium text-foreground">{from.place}</div>
          {from.sub && <div className="truncate text-muted-foreground">{from.sub}</div>}
        </div>
        <div className="min-w-0 text-right">
          <div className="truncate font-medium text-foreground">{to.place}</div>
          {to.sub && <div className="truncate text-muted-foreground">{to.sub}</div>}
        </div>
      </div>
    </div>
  );
}
