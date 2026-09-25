"use client";
import Link from "next/link";
import Logo from "@/components/Logo";
import Skyline from "@/components/Skyline";
import { useI18n } from "@/lib/i18n";

export default function Landing() {
  const { lang, setLang, t } = useI18n();
  return (
    <div className="landing">
      <div className="top">
        <Logo size={30} />
        <div className="langsw"><button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>EN</button><span>|</span><button className={lang === "ar" ? "on" : ""} onClick={() => setLang("ar")}>عربي</button></div>
      </div>
      <div className="copy">
        <span className="live" style={{ width: "fit-content" }}>{t("tagline")}</span>
        <h1><span>{t("hero_1")}</span><span>{t("hero_2")}</span><span className="accent">{t("hero_3")}</span></h1>
        <p>{t("hero_p")}</p>
        <Link href="/dashboard" className="cta"><span className="arrow">→</span>{t("get_started")}</Link>
      </div>
      <div className="visual">
        <Skyline />
        <div className="card" style={{ position: "absolute", bottom: "8vh", insetInlineStart: "-40px", width: 300 }}>
          <div className="row" style={{ justifyContent: "space-between" }}><h2 style={{ fontSize: 14 }}>{t("landing_preview")}</h2><span className="live">{t("live")}</span></div>
          <div className="list" style={{ marginTop: 6 }}>
            {[["Warehouse · Flood", "high"], ["Factory · Heat", "medium"], ["Cold store", "unknown"]].map(([n, l]) => (
              <div className="item" key={n}><span className="dot" style={{ background: `var(--${l})` }} /><span className="small">{n}</span><span className={`chip ${l}`} style={{ marginInlineStart: "auto" }}>{l}</span></div>
            ))}
          </div>
        </div>
      </div>
      <div className="foot note">{t("synthetic")}</div>
    </div>
  );
}
