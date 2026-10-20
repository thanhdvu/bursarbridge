import type { Metadata } from "next";
import { FamilySurface } from "@/components/bb/family-surface";
import { ParentTabs } from "./tabs";

export const metadata: Metadata = { title: "Parent" };

export default function ParentLayout({ children }: { children: React.ReactNode }) {
  return (
    <FamilySurface role="parent">
      <div className="flex min-h-0 flex-1 flex-col">{children}</div>
      <ParentTabs />
    </FamilySurface>
  );
}
