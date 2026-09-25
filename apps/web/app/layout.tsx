import type { Metadata } from "next";
import { Manrope } from "next/font/google";
import type { ReactNode } from "react";
import { I18nProvider } from "@/lib/i18n";
import "./globals.css";

const sans = Manrope({ subsets: ["latin"], weight: ["400", "500", "600", "700"], variable: "--font-sans", display: "swap" });

export const metadata: Metadata = { title: "trace — climate risks, financial impact, a clearer picture", description: "UAE climate financial-risk intelligence with self-evolving agents. Synthetic demo." };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" dir="ltr" className={sans.variable}>
      <body><I18nProvider>{children}</I18nProvider></body>
    </html>
  );
}
