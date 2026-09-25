"use client";
import Link from "next/link";
import Logo from "@/components/Logo";
import { useI18n } from "@/lib/i18n";

export default function Landing() {
  const { lang, setLang, t } = useI18n();
  return (
    <div className="landing">
      <div className="sky" />
      <div className="horizon" />
      <div className="contours" />
      <div className="orb o1" /><div className="orb o2" /><div className="orb o3" />
      <div className="top">
        <Logo size={44} glow />
        <div className="tabs"><button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>EN</button><button className={lang === "ar" ? "on" : ""} onClick={() => setLang("ar")}>عربي</button></div>
      </div>
      <div className="copy">
        <h1><span>{t("hero_1")}</span><span>{t("hero_2")}</span><span className="glow">{t("hero_3")}</span></h1>
        <p>{t("hero_p")}</p>
        <Link href="/dashboard" className="cta"><span className="arrow">→</span>{t("get_started")}</Link>
      </div>
      <div className="glance">
        <div className="glance-card">
          <div className="row" style={{ justifyContent: "space-between" }}><Logo size={18} /><span className="muted small num">9:41</span></div>
          <div className="glance-title">{t("landing_preview")}</div>
          <div className="map" style={{ height: 130 }}><div className="grid-lines" /><div className="flood" /><div className="heat" /><span className="tag">UAE</span></div>
          <div className="stack" style={{ marginTop: 10 }}>
            {[["Warehouse · Flood", "high"], ["Factory · Heat", "medium"], ["Cold store", "unknown"]].map(([n, l]) => (
              <div key={n} className="glance-row"><span>{n}</span><span className={`chip ${l}`}>{l}</span></div>
            ))}
          </div>
        </div>
      </div>
      <div className="foot muted small">{t("synthetic")}</div>
    </div>
  );
}
