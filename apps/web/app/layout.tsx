import type { Metadata } from "next";
import type { ReactNode } from "react";
import Shell from "@/components/Shell";
import { I18nProvider } from "@/lib/i18n";
import "./globals.css";

export const metadata: Metadata = { title: "TRACE - climate financial risk (prototype)", description: "UAE climate financial-risk intelligence with self-evolving agents. Synthetic demo." };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" dir="ltr">
      <body>
        <I18nProvider>
          <Shell>{children}</Shell>
        </I18nProvider>
      </body>
    </html>
  );
}
