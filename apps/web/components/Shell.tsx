"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useI18n } from "@/lib/i18n";

export default function Shell({ children }: { children: ReactNode }) {
  const { lang, setLang, t } = useI18n();
  const path = usePathname();
  const links = [["/", t("nav_review")], ["/assistant", t("nav_assistant")], ["/brief", t("nav_brief")], ["/governance", t("nav_governance")]] as const;
  return (
    <>
      <header>
        <span className="brand">{t("app")}</span>
        <span className="tag">{t("tagline")}</span>
        <nav>
          {links.map(([href, label]) => (
            <Link key={href} href={href} className={path === href ? "active" : ""}>{label}</Link>
          ))}
          <button className="lang" onClick={() => setLang(lang === "en" ? "ar" : "en")} aria-label="toggle language">{lang === "en" ? "العربية" : "English"}</button>
        </nav>
      </header>
      <main>
        <div className="banner">{t("synthetic")}</div>
        {children}
      </main>
    </>
  );
}
