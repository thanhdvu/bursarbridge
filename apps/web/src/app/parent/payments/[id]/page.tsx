"use client";

import { useParams } from "next/navigation";
import { PaymentDetail } from "@/components/bb/payment-detail";

export default function Page() {
  const { id } = useParams<{ id: string }>();
  return <PaymentDetail id={id} back="/parent" />;
}
