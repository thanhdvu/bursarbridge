"use client";

import { useTranslations } from "next-intl";
import { AgentChat } from "@/components/bb/chat";
import { AppHeader, LocaleSwitcher, ThemeToggle } from "@/components/bb/shell";
import { NewChatButton } from "@/components/bb/new-chat";

export default function ParentChat() {
  const t = useTranslations("parent.chat");
  return (
    <div className="flex h-[calc(100dvh-64px)] flex-col md:h-[calc(100dvh-8rem)]">
      <AppHeader
        left={
          <div>
            <h1 className="text-[15px] font-semibold">{t("title")}</h1>
            <p className="text-xs text-muted-foreground">{t("sub")}</p>
          </div>
        }
        right={
          <>
            <NewChatButton />
            <LocaleSwitcher compact />
            <ThemeToggle />
          </>
        }
        className="border-b"
      />
      <AgentChat suggestions={[t("s1"), t("s2"), t("s3"), t("s4")]} />
    </div>
  );
}
