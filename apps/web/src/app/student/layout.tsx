import type { Metadata } from "next";
import { FamilySurface } from "@/components/bb/family-surface";
import { StudentTabs } from "./tabs";

export const metadata: Metadata = { title: "Student" };

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <FamilySurface role="student">
      <div className="flex min-h-0 flex-1 flex-col">{children}</div>
      <StudentTabs />
    </FamilySurface>
  );
}
