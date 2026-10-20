import { getRequestConfig } from "next-intl/server";
import { cookies, headers } from "next/headers";
import type { Locale } from "@/lib/api/types";
import { localeCookie, locales, surfaceDefaults, type Surface } from "./config";

export default getRequestConfig(async () => {
  const h = await headers();
  const surface = (h.get("x-bb-surface") as Surface) || "site";
  const c = await cookies();
  const fromCookie = c.get(localeCookie(surface))?.value as Locale | undefined;
  const locale: Locale = fromCookie && locales.includes(fromCookie) ? fromCookie : surfaceDefaults[surface];
  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default,
    timeZone: "Asia/Ho_Chi_Minh",
  };
});
