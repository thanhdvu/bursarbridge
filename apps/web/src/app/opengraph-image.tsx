import { ImageResponse } from "next/og";

export const alt = "BursarBridge — tuition, paid safely. Refunded if the visa says no.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OG() {
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between", padding: 72, background: "#121722", color: "#f3f1ec", fontFamily: "sans-serif" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 18, fontSize: 34, fontWeight: 600 }}>
          <div style={{ width: 56, height: 56, borderRadius: 16, background: "#f3f1ec", display: "flex", alignItems: "flex-end", justifyContent: "space-between", padding: "0 12px 14px" }}>
            <div style={{ width: 10, height: 10, borderRadius: 10, background: "#121722" }} />
            <div style={{ width: 10, height: 10, borderRadius: 10, background: "#3fbf8f" }} />
          </div>
          BursarBridge
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div style={{ fontSize: 72, fontWeight: 700, lineHeight: 1.05, letterSpacing: -2 }}>Tuition, paid safely.</div>
          <div style={{ fontSize: 72, fontWeight: 700, lineHeight: 1.05, letterSpacing: -2, color: "#9fb4d9" }}>Refunded if the visa says no.</div>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 24, color: "#a7adbb" }}>
          <span>Verified payees only · Passkey-signed approvals · Tamper-evident evidence</span>
          <span>Fintechathon 2026</span>
        </div>
      </div>
    ),
    size,
  );
}
