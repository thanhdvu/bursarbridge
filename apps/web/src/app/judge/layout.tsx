import type { Metadata } from "next";

export const metadata: Metadata = { title: "Judge console" };

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
