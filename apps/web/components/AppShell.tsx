"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useI18n } from "@/lib/i18n";
import Chatbot from "./Chatbot";
import Logo from "./Logo";
import Skyline from "./Skyline";

const ICONS: Record<string, string> = { home: "▦", portfolio: "◫", risk: "◔", agents: "✦", reports: "▤", settings: "⚙" };

export default function AppShell({ children, rail }: { children: ReactNode; rail?: ReactNode }) {
  const { lang, setLang, t, prefs } = useI18n();
  const path = usePathname();
  const links = [
    ["/dashboard", "home", t("nav_home")], ["/portfolio", "portfolio", t("nav_portfolio")], ["/risk", "risk", t("nav_risk")],
    ["/agents", "agents", t("nav_agents")], ["/reports", "reports", t("nav_reports")], ["/settings", "settings", t("nav_settings")],
  ] as const;
  const initials = prefs.name.split(/\s+/).map((s) => s[0]).join("").slice(0, 2).toUpperCase() || "A";
  return (
    <div className={`shell ${rail ? "" : "no-rail"}`}>
      <aside className="side">
        <Link href="/" className="brand"><Logo size={24} /></Link>
        <nav>
          {links.map(([href, icon, label]) => <Link key={href} href={href} className={path === href ? "active" : ""}><span className="ico">{ICONS[icon]}</span>{label}</Link>)}
        </nav>
        <div className="art">
          <Skyline />
          <div className="caption">{t("side_caption")}</div>
        </div>
      </aside>
      <div className="main">
        <div className="topbar">
          <span className="tag">{t("tagline")}</span>
          <label className="search"><span>⌕</span><input placeholder={t("search_ph")} /><span className="kbd">⌘K</span></label>
          <div className="langsw"><button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>EN</button><span>|</span><button className={lang === "ar" ? "on" : ""} onClick={() => setLang("ar")}>عربي</button></div>
          <Link href="/settings" className="avatar" title={prefs.name}>{initials}</Link>
        </div>
        {children}
      </div>
      {rail && <aside className="rail">{rail}</aside>}
      <Chatbot />
    </div>
  );
}
