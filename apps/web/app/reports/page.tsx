"use client";
import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { API, api, type Governance, type Measure } from "@/lib/api";
import { fmt, useI18n } from "@/lib/i18n";
import Scene from "@/components/Scene";

export default function ReportsPage() {
  const { lang, t } = useI18n();
  const [measures, setMeasures] = useState<Measure[]>([]);
  const [measure, setMeasure] = useState("measure:raise_switchboards");
  const [findings, setFindings] = useState<string[] | null>(null);
  const [g, setG] = useState<Governance | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { api.measures().then(setMeasures).catch(() => {}); api.governance().then(setG).catch(() => {}); }, []);
  const generate = async () => { setBusy(true); setErr(null); try { const r = await api.briefTree("A-001", measure); setFindings(r.findings); } catch (e) { setErr(String(e)); } finally { setBusy(false); } };
  const url = (l: string) => `${API}/report/brief?lang=${l}&asset_id=A-001&measure_id=${encodeURIComponent(measure)}`;

  return (
    <AppShell title={t("reports_title")}>
      <div className="grid cols-1-2">
        <div className="stack">
          <div className="card">
            <div className="tabs" style={{ marginBottom: 12 }}><button className="on">{t("latest")}</button></div>
            <div className="question row" style={{ justifyContent: "space-between" }}>
              <div className="row"><span className="ico" style={{ width: 34, height: 34, borderRadius: 10, display: "grid", placeItems: "center", background: "var(--accent-dim)", color: "var(--accent-2)" }}>▤</span><div><div>{t("brief_name")}</div><div className="muted small">{t("brief_desc")}</div></div></div>
            </div>
            <div className="row" style={{ marginTop: 12 }}>
              <select value={measure} onChange={(e) => setMeasure(e.target.value)} style={{ flex: 1 }}>{measures.map((m) => <option key={m.id} value={m.id}>{lang === "ar" ? m.name_ar : m.name_en} — AED {fmt(m.capex_aed, lang)}</option>)}</select>
              <button className="btn" disabled={busy} onClick={generate}>{busy ? "…" : t("generate")}</button>
            </div>
            {err && <div className="small" style={{ color: "var(--high)", marginTop: 8 }}>{err}</div>}
            {findings && findings.length > 0 && <div className="small" style={{ color: "var(--high)", marginTop: 8 }}>{t("critic_blocked")}: {findings.join("; ")}</div>}
            {findings && findings.length === 0 && (
              <div className="row" style={{ marginTop: 10 }}>
                <span className="chip low">critic: pass · ar/en parity</span>
                <a className="btn ghost sm" href={url("en")} target="_blank" rel="noreferrer">{t("open_en")}</a>
                <a className="btn ghost sm" href={url("ar")} target="_blank" rel="noreferrer">{t("open_ar")}</a>
              </div>
            )}
          </div>
          <div className="photo" style={{ minHeight: 170 }}>
            <Scene kind="cold" />
            <div className="t">{t("insight")}</div>
            <div className="s">{t("insight_p")}</div>
          </div>
          {g && (
            <div className="card">
              <h2>{t("governance")}</h2>
              <table><tbody>
                <tr><th>{t("engine")}</th><td className="num">{g.engine_version}</td></tr>
                {Object.entries(g.datasets).map(([k, v]) => <tr key={k}><th>{k}</th><td className="num">{v}</td></tr>)}
                {Object.entries(g.damage_functions).map(([k, v]) => <tr key={k}><th>{k}</th><td className="num">{v.version} <span className="chip">{v.validation_status}</span></td></tr>)}
                <tr><th>{t("reg")}</th><td>{g.regulatory_mapping.version} — <span className="muted">{g.regulatory_mapping.status}</span></td></tr>
              </tbody></table>
            </div>
          )}
        </div>
        <div className="card" style={{ padding: 0, overflow: "hidden", minHeight: 600 }}>
          {findings && findings.length === 0 ? <iframe title="brief" src={url(lang)} style={{ width: "100%", height: "100%", minHeight: 780, border: 0, background: "#fff" }} /> : <div className="empty muted">{t("generate")}</div>}
        </div>
      </div>
    </AppShell>
  );
}
