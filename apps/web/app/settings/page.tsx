"use client";
import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { API, api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export default function SettingsPage() {
  const { lang, setLang, t, prefs, setPrefs } = useI18n();
  const [name, setName] = useState(prefs.name);
  const [voice, setVoice] = useState(prefs.voice);
  const [llm, setLlm] = useState("…");
  useEffect(() => { setName(prefs.name); setVoice(prefs.voice); }, [prefs]);
  useEffect(() => { api.health().then((h) => setLlm(h.llm_provider)).catch(() => setLlm("offline")); }, []);
  return (
    <AppShell title={t("settings")}>
      <div className="card" style={{ maxWidth: 560 }}>
        <div className="stack">
          <label className="stack"><span className="muted small">{t("your_name")}</span><input value={name} onChange={(e) => setName(e.target.value)} /></label>
          <div><div className="muted small" style={{ marginBottom: 6 }}>{t("language")}</div><div className="tabs"><button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>English</button><button className={lang === "ar" ? "on" : ""} onClick={() => setLang("ar")}>العربية</button></div></div>
          <div><div className="muted small" style={{ marginBottom: 6 }}>{t("voice")}</div><div className="tabs"><button className={voice ? "on" : ""} onClick={() => setVoice(true)}>{t("voice_on")}</button><button className={!voice ? "on" : ""} onClick={() => setVoice(false)}>{t("voice_off")}</button></div></div>
          <div className="muted small">{t("api")}: <span className="num">{API}</span> · {t("llm")}: <span className="chip">{llm}</span></div>
          <button className="btn" style={{ width: "fit-content" }} onClick={() => setPrefs({ name: name || "Analyst", voice })}>{t("save")}</button>
        </div>
      </div>
    </AppShell>
  );
}
