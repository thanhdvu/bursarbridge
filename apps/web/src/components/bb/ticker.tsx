"use client";

import { animate, useInView, useReducedMotion } from "motion/react";
import { useEffect, useRef } from "react";

/** Number ticker: counts to a value once visible; respects reduced motion. Inspired by Magic UI NumberTicker (MIT). */
export function NumberTicker({ value, format, className, duration = 1.1, animateOnMount = false }: { value: number; format: (n: number) => string; className?: string; duration?: number; animateOnMount?: boolean }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const reduce = useReducedMotion();
  // By default only changes animate (a balance should not count up from zero on every visit).
  const last = useRef<number | null>(animateOnMount ? 0 : null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (last.current === null) {
      el.textContent = format(value);
      last.current = value;
      return;
    }
    if (reduce || !inView) {
      el.textContent = format(value);
      if (inView) last.current = value;
      return;
    }
    const controls = animate(last.current, value, {
      duration,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (v) => (el.textContent = format(Math.round(v))),
    });
    last.current = value;
    return () => controls.stop();
  }, [value, inView, reduce, format, duration]);
  return (
    <span ref={ref} className={className}>
      {format(value)}
    </span>
  );
}
