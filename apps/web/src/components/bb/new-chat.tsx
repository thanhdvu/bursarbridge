"use client";

import { SquarePen } from "lucide-react";
import { useTranslations } from "next-intl";

export function NewChatButton() {
  const t = useTranslations("chat");
  return (
    <button
      type="button"
      onClick={() => window.dispatchEvent(new Event("bb-new-thread"))}
      aria-label={t("newChat")}
      title={t("newChat")}
      className="grid size-9 place-items-center rounded-full text-muted-foreground hover:bg-accent hover:text-foreground"
    >
      <SquarePen className="size-4" />
    </button>
  );
}
