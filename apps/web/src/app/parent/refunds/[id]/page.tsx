"use client";

import { useParams } from "next/navigation";
import { RefundDetail } from "@/components/bb/refund-detail";

export default function Page() {
  const { id } = useParams<{ id: string }>();
  return <RefundDetail id={id} back="/parent" />;
}
