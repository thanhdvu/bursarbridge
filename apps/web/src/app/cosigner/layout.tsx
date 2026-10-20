import type { Metadata } from "next";
import { FamilySurface } from "@/components/bb/family-surface";

export const metadata: Metadata = { title: "Co-signer" };

export default function CosignerLayout({ children }: { children: React.ReactNode }) {
  return (
    <FamilySurface role="cosigner">
      <div className="flex min-h-0 flex-1 flex-col">{children}</div>
    </FamilySurface>
  );
}
