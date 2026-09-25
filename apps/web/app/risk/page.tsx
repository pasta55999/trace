"use client";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import { BarChart, BarLabels, LineCompare } from "@/components/Charts";
import { api, type Comparison, type Measure } from "@/lib/api";
import { fmt, useI18n } from "@/lib/i18n";
import { mid } from "@/lib/risk";
import { useStatus } from "@/lib/useStatus";

function RiskInner() {
  const { lang, t } = useI18n();
  const sp = useSearchParams();
  const { status: s } = useStatus();
  const [tab, setTab] = useState<"scenarios" | "measures" | "comparisons">((sp.get("measure") ? "comparisons" : "scenarios"));
  const [asset, setAsset] = useState(sp.get("asset") ?? "A-001");
  const [measure, setMeasure] = useState(sp.get("measure") ?? "measure:raise_switchboards");
  const [measures, setMeasures] = useState<Measure[]>([]);
  const [cmp, setCmp] = useState<Comparison | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => { api.measures().then(setMeasures).catch(() => {}); }, []);
  useEffect(() => { if (tab === "comparisons") { setBusy(true); api.compare(asset, measure).then(setCmp).catch(() => setCmp(null)).finally(() => setBusy(false)); } }, [tab, asset, measure]);

  const run = s?.run; const c = run?.aggregation.concentration; const assets = run?.assets ?? [];
  const bars = assets.map((a) => ({ label: a.asset_id, value: mid(a.outstanding_allocated_aed), color: c?.assets_in_footprint.includes(a.asset_id) ? "#ff6b6b" : "#2b3a4b" }));
  const bd = cmp ? mid(cmp.baseline.physical_damage_total_aed) : null, pd = cmp ? mid(cmp.protected.physical_damage_total_aed) : null;
  const bb = cmp ? mid(cmp.baseline.interruption_cost_aed) : null, pb = cmp ? mid(cmp.protected.interruption_cost_aed) : null;

  return (
    <AppShell title={t("nav_risk")}>
      <div className="tabs" style={{ marginBottom: 14 }}>
        {(["scenarios", "measures", "comparisons"] as const).map((k) => <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{t(k)}</button>)}
      </div>

      {tab === "scenarios" && run && (
        <div className="grid cols-2-1">
          <div className="card">
            <h2>{lang === "ar" ? run.scenario.label_ar : run.scenario.label_en}</h2>
            <div className="grid cols-3" style={{ marginBottom: 14 }}>
              <div className="card" style={{ padding: 12 }}><div className="muted small">{t("in_footprint")}</div><div className="num" style={{ fontSize: 22 }}>{c?.assets_in_footprint.length} / {assets.length}</div><div className="muted small">{c?.sectors.length} sectors</div></div>
              <div className="card" style={{ padding: 12 }}><div className="muted small">{t("outstanding")}</div><div className="num" style={{ fontSize: 22 }}>AED {fmt(c?.outstanding_in_footprint_aed, lang, true)}</div><div className="muted small num">{((c?.share_of_portfolio_outstanding ?? 0) * 100).toFixed(1)}% {t("share")}</div></div>
              <div className="card" style={{ padding: 12 }}><div className="muted small">{t("damage")}</div><div className="num" style={{ fontSize: 18 }}>AED {fmt(c?.physical_damage_total_aed, lang, true)}</div><div className="muted small">{t("insured")}: {fmt(c?.insured_loss_total_aed, lang, true)}</div></div>
            </div>
            <h2>{t("outstanding")} — {t("concentration").toLowerCase()}</h2>
            <BarChart rows={bars} /><BarLabels rows={bars} />
            <div className="muted small" style={{ marginTop: 8 }}>{lang === "ar" ? run.aggregation.diversification_warning_ar : run.aggregation.diversification_warning_en}</div>
          </div>
          <div className="card">
            <h2>{t("changes")}</h2>
            {!s?.diff || s.diff.changes.length === 0 ? <div className="muted small">{t("no_changes")}</div> : (
              <>
                <div className="muted small" style={{ marginBottom: 8 }}>{lang === "ar" ? s.diff.summary_ar : s.diff.summary_en}</div>
                <table><tbody>{s.diff.changes.slice(0, 10).map((ch, i) => <tr key={i}><td>{ch.asset_id}<div className="muted small">{ch.field}</div></td><td><span className="chip">{ch.kind}</span></td><td className="num small">{ch.from} → {ch.to}</td></tr>)}</tbody></table>
              </>
            )}
            {run.aggregation.unknown_assets && run.aggregation.unknown_assets.length > 0 && (
              <><h2 style={{ marginTop: 14 }}>{t("risk_unknown")}</h2>{run.aggregation.unknown_assets.map((u) => <div key={u.asset_id} className="small muted">{u.asset_id}: {lang === "ar" ? u.reason_ar : u.reason}</div>)}</>
            )}
          </div>
        </div>
      )}

      {tab === "measures" && (
        <div className="grid cols-2">
          {measures.map((m) => (
            <div key={m.id} className="card">
              <h2 style={{ color: "var(--ink)" }}>{lang === "ar" ? m.name_ar : m.name_en}</h2>
              <div className="muted small">{lang === "ar" ? m.notes_ar : m.notes_en}</div>
              <div className="row" style={{ marginTop: 12, justifyContent: "space-between" }}>
                <span className="num">{t("capex")}: AED {fmt(m.capex_aed, lang)}</span>
                <button className="btn sm" onClick={() => { setMeasure(m.id); setTab("comparisons"); }}>{t("comparisons")} →</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === "comparisons" && (
        <div className="stack">
          <div className="row">
            <select value={asset} onChange={(e) => setAsset(e.target.value)}>{assets.map((a) => <option key={a.asset_id} value={a.asset_id}>{a.asset_id} · {a.description}</option>)}</select>
            <select value={measure} onChange={(e) => setMeasure(e.target.value)}>{measures.map((m) => <option key={m.id} value={m.id}>{lang === "ar" ? m.name_ar : m.name_en}</option>)}</select>
            {busy && <span className="muted small">…</span>}
          </div>
          {cmp && (
            <div className="grid cols-2-1">
              <div className="card">
                <h2>{lang === "ar" ? cmp.measure.name_ar : cmp.measure.name_en}</h2>
                <div className="grid cols-3" style={{ marginBottom: 14 }}>
                  <div className="card" style={{ padding: 12 }}><div className="muted small">{t("avoided")}</div><div className="num" style={{ fontSize: 20, color: "var(--low)" }}>AED {fmt(cmp.avoided_loss_event_aed, lang, true)}</div></div>
                  <div className="card" style={{ padding: 12 }}><div className="muted small">{t("bcr")}</div><div className="num" style={{ fontSize: 20 }}>{cmp.event_conditional_benefit_cost_ratio ?? "—"}</div></div>
                  <div className="card" style={{ padding: 12 }}><div className="muted small">{t("capex")}</div><div className="num" style={{ fontSize: 20 }}>AED {fmt(cmp.capex_aed, lang, true)}</div></div>
                </div>
                <div className="row small" style={{ gap: 16, marginBottom: 6 }}><span><span className="dot" style={{ background: "var(--high)" }} /> {t("baseline")}</span><span><span className="dot" style={{ background: "var(--accent)" }} /> {t("protected")}</span></div>
                {bd !== null && pd !== null && bb !== null && pb !== null && (
                  <LineCompare a={[bd, bd + bb]} b={[pd, pd + pb]} labels={[t("damage"), `${t("damage")} + ${t("bi")}`]} />
                )}
                <table style={{ marginTop: 12 }}><thead><tr><th></th><th>{t("baseline")}</th><th>{t("protected")}</th></tr></thead><tbody>
                  {(["physical_damage_total_aed", "interruption_cost_aed", "insured_loss_aed", "uninsured_physical_damage_aed"] as const).map((k) => <tr key={k}><td className="muted">{k.replace(/_aed$/, "").replace(/_/g, " ")}</td><td className="num">{fmt(cmp.baseline[k], lang)}</td><td className="num">{fmt(cmp.protected[k], lang)}</td></tr>)}
                  <tr><td className="muted">{t("npv")}</td><td colSpan={2} className="muted small">{fmt(cmp.npv_aed, lang)}</td></tr>
                </tbody></table>
                <div className="muted small" style={{ marginTop: 10 }}>{lang === "ar" ? cmp.disclaimer_ar : cmp.disclaimer_en}</div>
              </div>
              <div className="card">
                <h2>{t("top_reco")}</h2>
                <div className="question">
                  <div>{lang === "ar" ? cmp.measure.name_ar : cmp.measure.name_en}</div>
                  <div className="muted small" style={{ margin: "6px 0 10px" }}>{t("residual")}: AED {fmt(cmp.residual_damage_event_aed, lang)}</div>
                  <a className="btn sm" href="/reports">{t("add_plan")} → {t("nav_reports")}</a>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}

export default function RiskPage() {
  return <Suspense fallback={null}><RiskInner /></Suspense>;
}
