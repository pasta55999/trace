import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import type { ReactNode } from "react";
import { I18nProvider } from "@/lib/i18n";
import "./globals.css";

const outfit = Outfit({ subsets: ["latin"], weight: ["200", "300", "400", "500"], variable: "--font-outfit", display: "swap" });

export const metadata: Metadata = { title: "trace — climate risks, financial impact, a clearer picture", description: "UAE climate financial-risk intelligence with self-evolving agents. Synthetic demo." };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" dir="ltr" className={outfit.variable}>
      <body><I18nProvider>{children}</I18nProvider></body>
    </html>
  );
}
