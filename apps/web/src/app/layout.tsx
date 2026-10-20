import type { Metadata, Viewport } from "next";
import { Be_Vietnam_Pro, JetBrains_Mono, Newsreader } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getLocale } from "next-intl/server";
import { AppProviders } from "@/components/providers/app-providers";
import { InlineScript } from "@/components/inline-script";
import { themeScript } from "@/lib/theme-script";
import "./globals.css";

const ui = Be_Vietnam_Pro({
  variable: "--font-ui",
  subsets: ["latin", "latin-ext", "vietnamese"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const serif = Newsreader({
  variable: "--font-serif",
  subsets: ["latin", "latin-ext", "vietnamese"],
  weight: ["400", "500", "600"],
  style: ["normal", "italic"],
  display: "swap",
});

const code = JetBrains_Mono({
  variable: "--font-code",
  subsets: ["latin"],
  weight: ["400", "500"],
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: { default: "BursarBridge — tuition, paid safely", template: "%s · BursarBridge" },
  description:
    "An AI agent that pays an international student's tuition from the family's home bank, pays only payees the university has cryptographically vouched for, and gets the money back if the visa is refused.",
  applicationName: "BursarBridge",
  openGraph: {
    title: "BursarBridge",
    description: "Tuition, paid safely. Refunded if the visa says no.",
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f9f8f5" },
    { media: "(prefers-color-scheme: dark)", color: "#121722" },
  ],
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const locale = await getLocale();
  return (
    <html lang={locale} className={`${ui.variable} ${serif.variable} ${code.variable} h-full`} suppressHydrationWarning>
      <head>
        <InlineScript html={themeScript} />
      </head>
      <body className="min-h-full">
        <NextIntlClientProvider>
          <AppProviders>{children}</AppProviders>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
