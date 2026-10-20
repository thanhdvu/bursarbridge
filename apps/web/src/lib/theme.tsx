"use client";

import { createContext, useCallback, useContext, useEffect, useSyncExternalStore } from "react";
import { THEME_KEY as KEY } from "./theme-script";
export type ThemePref = "light" | "dark" | "system";
const CHANGE = "bb-theme-changed";
function preference(): ThemePref {
  try { const value = localStorage.getItem(KEY); return value === "dark" || value === "light" ? value : "system"; }
  catch { return "system"; }
}
function darkSystem() { return window.matchMedia("(prefers-color-scheme: dark)").matches; }
function subscribe(listener: () => void) {
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  mq.addEventListener("change", listener);
  window.addEventListener("storage", listener);
  window.addEventListener(CHANGE, listener);
  return () => { mq.removeEventListener("change", listener); window.removeEventListener("storage", listener); window.removeEventListener(CHANGE, listener); };
}
const Ctx = createContext<{ theme: ThemePref; resolvedTheme: "light" | "dark"; setTheme: (t: ThemePref) => void }>({ theme: "system", resolvedTheme: "light", setTheme: () => {} });
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useSyncExternalStore(subscribe, preference, (): ThemePref => "system");
  const systemDark = useSyncExternalStore(subscribe, darkSystem, () => false);
  const resolvedTheme = theme === "dark" || (theme === "system" && systemDark) ? "dark" : "light";
  useEffect(() => {
    document.documentElement.classList.toggle("dark", resolvedTheme === "dark");
    document.documentElement.style.colorScheme = resolvedTheme;
  }, [resolvedTheme]);
  const setTheme = useCallback((value: ThemePref) => {
    try { localStorage.setItem(KEY, value); } catch { /* unavailable storage */ }
    window.dispatchEvent(new Event(CHANGE));
  }, []);
  return <Ctx.Provider value={{ theme, resolvedTheme, setTheme }}>{children}</Ctx.Provider>;
}
export function useTheme() { return useContext(Ctx); }
