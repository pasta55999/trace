"use client";
import { useEffect, useState } from "react";
import { API, api, type Comparison, type Measure } from "@/lib/api";
import { fmt, useI18n } from "@/lib/i18n";

export default function BriefPage() {
  const { lang, t } = useI18n();
  const [measures, setMeasures] = useState<Measure[]>([]);
  const [measure, setMeasure] = useState("measure:raise_switchboards");
  const [cmp, setCmp] = useState<Comparison | null>(null);
  const [findings, setFindings] = useState<string[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => { api.measures().then(setMeasures).catch(() => setMeasures([])); }, []);

  const generate = async () => {
    setBusy(true); setErr(null);
    try {
      setCmp(await api.compare("A-001", measure));
      const r = await api.briefTree("A-001", measure);
      setFindings(r.findings);
    } catch (e) { setErr(String(e)); } finally { setBusy(false); }
  };
  const url = (l: string) => `${API}/report/brief?lang=${l}&asset_id=A-001&measure_id=${encodeURIComponent(measure)}`;

  return (
    <div className="stack">
      <div className="panel">
        <h2>{t("brief_title")}</h2>
        <div className="row">
          <label>{t("measure")}</label>
          <select value={measure} onChange={(e) => setMeasure(e.target.value)}>
            {measures.map((m) => <option key={m.id} value={m.id}>{lang === "ar" ? m.name_ar : m.name_en} — {fmt(m.capex_aed, lang)} AED</option>)}
          </select>
          <button className="primary" disabled={busy} onClick={generate}>{t("generate")}</button>
        </div>
        {err && <p className="bad">{err}</p>}
      </div>
      {cmp && (
        <div className="grid cols-2">
          <div className="panel">
            <h2>{lang === "ar" ? cmp.measure.name_ar : cmp.measure.name_en}</h2>
            <table>
              <tbody>
                <tr><th>{t("capex")}</th><td className="num">{fmt(cmp.capex_aed, lang)}</td></tr>
                <tr><th>{t("avoided")}</th><td className="num">{fmt(cmp.avoided_loss_event_aed, lang)}</td></tr>
                <tr><th>{t("residual")}</th><td className="num">{fmt(cmp.residual_damage_event_aed, lang)}</td></tr>
                {cmp.event_conditional_benefit_cost_ratio !== undefined && <tr><th>{t("bcr")}</th><td className="num">{cmp.event_conditional_benefit_cost_ratio}</td></tr>}
                <tr><th>{t("npv")}</th><td>{fmt(cmp.npv_aed, lang)}</td></tr>
              </tbody>
            </table>
            <p className="muted">{lang === "ar" ? cmp.disclaimer_ar : cmp.disclaimer_en}</p>
          </div>
          <div className="panel stack">
            {findings && findings.length > 0 ? (
              <p className="bad">{t("critic_blocked")} {findings.join("; ")}</p>
            ) : (
              <>
                <span className="chip ok">critic: pass · ar/en numeric parity</span>
                <div className="row">
                  <a className="lang" href={url("ar")} target="_blank" rel="noreferrer">{t("open_ar")}</a>
                  <a className="lang" href={url("en")} target="_blank" rel="noreferrer">{t("open_en")}</a>
                </div>
                <iframe title="brief" src={url(lang)} style={{ width: "100%", height: 520, border: "1px solid var(--line)", borderRadius: 8, background: "#fff" }} />
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
