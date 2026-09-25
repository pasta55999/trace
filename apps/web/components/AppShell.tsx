"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useI18n } from "@/lib/i18n";
import Chatbot from "./Chatbot";

const ICONS: Record<string, string> = { home: "⌂", portfolio: "▦", risk: "◔", agents: "✦", reports: "▤", settings: "⚙" };

export default function AppShell({ children, title, subtitle }: { children: ReactNode; title?: ReactNode; subtitle?: ReactNode }) {
  const { lang, setLang, t, prefs } = useI18n();
  const path = usePathname();
  const links = [
    ["/dashboard", "home", t("nav_home")], ["/portfolio", "portfolio", t("nav_portfolio")], ["/risk", "risk", t("nav_risk")],
    ["/agents", "agents", t("nav_agents")], ["/reports", "reports", t("nav_reports")], ["/settings", "settings", t("nav_settings")],
  ] as const;
  const initials = prefs.name.split(/\s+/).map((s) => s[0]).join("").slice(0, 2).toUpperCase() || "A";
  return (
    <div className="shell">
      <aside className="sidebar">
        <Link href="/" className="wordmark" style={{ padding: "4px 12px 18px", display: "block" }}>trace</Link>
        {links.map(([href, icon, label]) => (
          <Link key={href} href={href} className={path === href ? "active" : ""}><span className="icon">{ICONS[icon]}</span>{label}</Link>
        ))}
        <div className="user">
          <span className="avatar">{initials}</span>
          <div><div>{prefs.name}</div><div className="muted small">{t("bank_analyst")}</div></div>
        </div>
      </aside>
      <div className="content">
        <div className="topbar">
          <div>{title && <h1>{title}</h1>}{subtitle && <div className="sub">{subtitle}</div>}</div>
          <div className="right">
            <span className="num">{new Date().toLocaleDateString(lang === "ar" ? "ar-AE" : "en-GB", { day: "2-digit", month: "short", year: "numeric" })}</span>
            <button className="btn ghost sm" onClick={() => setLang(lang === "en" ? "ar" : "en")}>{lang === "en" ? "عربي" : "EN"}</button>
          </div>
        </div>
        <div className="banner">{t("synthetic")}</div>
        {children}
      </div>
      <Chatbot />
    </div>
  );
}
