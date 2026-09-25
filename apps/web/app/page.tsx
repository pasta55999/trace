"use client";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";

export default function Landing() {
  const { lang, setLang, t } = useI18n();
  return (
    <div className="landing">
      <div className="earth" />
      <div className="top">
        <span className="wordmark" style={{ fontSize: 34 }}>trace</span>
        <div className="tabs"><button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>EN</button><button className={lang === "ar" ? "on" : ""} onClick={() => setLang("ar")}>عربي</button></div>
      </div>
      <div className="copy">
        <h1>{t("hero_1")}<br />{t("hero_2")}<br />{t("hero_3")}</h1>
        <p>{t("hero_p")}</p>
        <Link href="/dashboard" className="cta"><span className="arrow">→</span>{t("get_started")}</Link>
        <p className="muted small" style={{ marginTop: 24 }}>{t("synthetic")}</p>
      </div>
      <div className="preview">
        <div className="card">
          <div className="row" style={{ justifyContent: "space-between" }}><span className="wordmark" style={{ fontSize: 18 }}>trace</span><span className="muted small num">9:41</span></div>
          <h2 style={{ marginTop: 10 }}>{t("landing_preview")}</h2>
          <div className="map" style={{ height: 150 }}><div className="grid-lines" /><div className="flood" /><div className="heat" /><span className="tag">UAE</span></div>
          <div className="stack" style={{ marginTop: 12 }}>
            {[["Warehouse — Flood", "high"], ["Factory — Heat", "medium"], ["Cold store — Storm", "unknown"]].map(([n, l]) => (
              <div key={n} className="row" style={{ justifyContent: "space-between", padding: "8px 10px", border: "1px solid var(--line)", borderRadius: 10 }}><span>{n}</span><span className={`chip ${l}`}>{l}</span></div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
