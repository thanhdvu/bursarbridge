"use client";

import { browserSupportsWebAuthn, startAuthentication, startRegistration } from "@simplewebauthn/browser";
import { Check, Fingerprint, ScanFace, ShieldCheck, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useTranslations } from "next-intl";
import { useCallback, useRef, useState } from "react";
import { Drawer, DrawerContent, DrawerDescription, DrawerTitle } from "@/components/ui/drawer";
import { Button } from "@/components/ui/button";
import { HashChip } from "@/components/bb/hash";
import { MockBadge } from "@/components/bb/badges";
import { ApiError } from "@/lib/api/client";
import { useClient } from "@/lib/persona";
import { cn } from "@/lib/utils";

export type Assertion = { demo: true } | Record<string, unknown>;

const REAL_KEY = "bb-passkey-real";
export function prefersRealPasskey() {
  try {
    return localStorage.getItem(REAL_KEY) === "1";
  } catch {
    return false;
  }
}
export function setPrefersRealPasskey(v: boolean) {
  try {
    localStorage.setItem(REAL_KEY, v ? "1" : "0");
  } catch {
    /* ignore */
  }
}

type Phase = "ready" | "scanning" | "done" | "error";

/**
 * Passkey signing sheet. Shows exactly what is being signed (dynamic linking: the challenge is the
 * consent hash). Uses the device's real passkey when the user opted in and WebAuthn is available,
 * otherwise a clearly labelled demo authenticator.
 */
type PasskeySheetProps = {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  purpose: "mandate" | "approval" | "freeze" | "cosign";
  refId: string;
  hash?: string;
  title: string;
  lines: { label: string; value: React.ReactNode }[];
  onSigned: (assertion: Assertion) => Promise<void> | void;
  tone?: "default" | "danger";
};

export function PasskeySheet(props: PasskeySheetProps) {
  return props.open ? <OpenPasskeySheet {...props} /> : null;
}

function OpenPasskeySheet({
  open,
  onOpenChange,
  purpose,
  refId,
  hash,
  title,
  lines,
  onSigned,
  tone = "default",
}: PasskeySheetProps) {
  const t = useTranslations("passkey");
  const te = useTranslations("errors");
  const client = useClient();
  const [phase, setPhase] = useState<Phase>("ready");
  const [error, setError] = useState<string | null>(null);
  const [real, setReal] = useState(() => prefersRealPasskey() && browserSupportsWebAuthn());
  const busy = useRef(false);

  const sign = useCallback(async () => {
    if (busy.current) return;
    busy.current = true;
    setError(null);
    setPhase("scanning");
    try {
      let assertion: Assertion;
      if (real) {
        // Ask the server, not localStorage, whether this person has a device passkey: a judge reset or another
        // persona on the same browser would otherwise leave a stale "registered" flag and a dead end.
        let opts = await client.webauthn.assertOptions(purpose, refId);
        if (!(opts.allowCredentials as unknown[] | undefined)?.length) {
          const regOpts = await client.webauthn.registerOptions();
          const reg = await startRegistration({ optionsJSON: regOpts as never });
          await client.webauthn.registerVerify(reg);
          opts = await client.webauthn.assertOptions(purpose, refId);
        }
        const cred = await startAuthentication({ optionsJSON: opts as never });
        const receipt = await client.webauthn.assertVerify(refId, cred);
        // Preferred flow: the API returns a short-lived receipt bound to this reference and consent hash.
        assertion = receipt.assertionHash ? { assertionHash: receipt.assertionHash } : (cred as unknown as Record<string, unknown>);
      } else {
        // Each attempt asks for fresh options first (the server consumes a challenge on verify), and an
        // options refusal (not this person's signature, expired, frozen) is shown, never swallowed.
        await Promise.all([new Promise((r) => setTimeout(r, 1100)), client.webauthn.assertOptions(purpose, refId)]);
        const receipt = await client.webauthn.assertVerify(refId, { demo: true });
        assertion = receipt.assertionHash ? { assertionHash: receipt.assertionHash } : { demo: true };
      }
      await onSigned(assertion);
      setPhase("done");
      setTimeout(() => onOpenChange(false), 900);
    } catch (e) {
      setPhase("error");
      const code = e instanceof ApiError ? e.code : "";
      setError(code && te.has(code as never) ? te(code as never) : e instanceof DOMException ? t("cancelled") : te("generic"));
    } finally {
      busy.current = false;
    }
  }, [client, onOpenChange, onSigned, purpose, real, refId, t, te]);

  return (
    <Drawer open={open} onOpenChange={(o) => phase !== "scanning" && onOpenChange(o)}>
      <DrawerContent className="mx-auto max-w-md">
        <div className="px-5 pt-2 pb-6">
          <div className="flex items-center justify-between">
            <DrawerTitle className="text-base font-semibold">{title}</DrawerTitle>
            {!real && <MockBadge what="authenticator" />}
          </div>
          <DrawerDescription className="mt-1 text-sm text-muted-foreground">{t("exactly")}</DrawerDescription>

          <dl className="mt-4 divide-y divide-hairline rounded-xl border bg-subtle/60">
            {lines.map((l) => (
              <div key={l.label} className="flex items-baseline justify-between gap-4 px-3.5 py-2.5 text-sm">
                <dt className="text-muted-foreground">{l.label}</dt>
                <dd className="text-right font-medium tnum">{l.value}</dd>
              </div>
            ))}
            {hash && (
              <div className="flex items-center justify-between gap-4 px-3.5 py-2.5 text-sm">
                <dt className="text-muted-foreground">{t("hash")}</dt>
                <dd>
                  <HashChip value={hash} label={t("hash")} />
                </dd>
              </div>
            )}
          </dl>

          <div className="mt-6 flex flex-col items-center">
            <div className="relative grid size-20 place-items-center">
              <AnimatePresence mode="wait">
                {phase === "done" ? (
                  <motion.span
                    key="done"
                    initial={{ scale: 0.6, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="grid size-16 place-items-center rounded-full bg-verified text-white"
                  >
                    <Check className="size-8" strokeWidth={2.5} />
                  </motion.span>
                ) : phase === "error" ? (
                  <motion.span key="err" initial={{ scale: 0.8 }} animate={{ scale: 1 }} className="grid size-16 place-items-center rounded-full bg-blocked-soft text-blocked">
                    <X className="size-8" />
                  </motion.span>
                ) : (
                  <motion.span key="scan" className="relative grid size-16 place-items-center rounded-2xl border bg-card text-foreground">
                    {phase === "scanning" && (
                      <motion.span
                        className="absolute inset-x-2 h-0.5 rounded-full bg-route"
                        initial={{ top: 8 }}
                        animate={{ top: [8, 54, 8] }}
                        transition={{ duration: 1.1, repeat: Infinity, ease: "easeInOut" }}
                      />
                    )}
                    {real ? <Fingerprint className="size-8" /> : <ScanFace className="size-8" />}
                  </motion.span>
                )}
              </AnimatePresence>
            </div>
            <p className={cn("mt-2 h-5 text-sm", phase === "error" ? "text-blocked" : "text-muted-foreground")} aria-live="polite">
              {phase === "scanning" ? t("scanning") : phase === "done" ? t("signed") : phase === "error" ? t("failed") : real ? t("deviceHint") : t("demoHint")}
            </p>
            {error && <p className="mt-1 max-w-xs text-center text-xs text-muted-foreground">{error}</p>}
          </div>

          <Button
            size="lg"
            className={cn("mt-5 h-12 w-full rounded-xl text-[15px]", tone === "danger" && "bg-blocked text-white hover:bg-blocked/90")}
            onClick={sign}
            disabled={phase === "scanning" || phase === "done"}
          >
            <ShieldCheck className="size-5" />
            {phase === "error" ? t("retry") : t("cta")}
          </Button>
          {browserSupportsWebAuthn() && (
            <button
              type="button"
              className="mx-auto mt-3 block text-xs text-muted-foreground underline-offset-4 hover:underline"
              onClick={() => {
                setPrefersRealPasskey(!real);
                setReal(!real);
              }}
            >
              {real ? t("useDemo") : t("useDevice")}
            </button>
          )}
        </div>
      </DrawerContent>
    </Drawer>
  );
}
