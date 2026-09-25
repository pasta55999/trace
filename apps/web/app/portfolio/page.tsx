"use client";
import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { api, type AssetRow, type Measure } from "@/lib/api";
import { fmt, useI18n } from "@/lib/i18n";
import { riskLevel } from "@/lib/risk";
import Scene, { sceneFor } from "@/components/Scene";
import { useStatus } from "@/lib/useStatus";

export default function Portfolio() {
  const { lang, t } = useI18n();
  const { status: s, busy, answer } = useStatus();
  const [filter, setFilter] = useState<string>("all");
  const [search, setSearch] = useState("");
  const [sel, setSel] = useState<string | null>(null);
  const [tab, setTab] = useState<"overview" | "climate" | "financials" | "actions">("overview");
  const [measures, setMeasures] = useState<Measure[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  useEffect(() => { api.measures().then(setMeasures).catch(() => {}); }, []);

  const assets = s?.run?.assets ?? [];
  const sectors = [...new Set(assets.map((a) => a.sector))];
  const list = assets.filter((a) => (filter === "all" || a.sector === filter) && (!search || `${a.asset_id} ${a.description} ${a.borrower} ${a.borrower_ar}`.toLowerCase().includes(search.toLowerCase())));
  const a: AssetRow | undefined = assets.find((x) => x.asset_id === sel) ?? list[0];
  const qs = s?.questions.filter((q) => q.asset_id === a?.asset_id) ?? [];
  const fac = a?.facilities?.[0];

  return (
    <AppShell title={t("nav_portfolio")}>
      <div className="grid cols-1-2">
        <div className="card">
          <div className="row" style={{ marginBottom: 10 }}>
            <input placeholder={t("search")} value={search} onChange={(e) => setSearch(e.target.value)} style={{ flex: 1 }} />
          </div>
          <div className="tabs" style={{ marginBottom: 12 }}>
            <button className={filter === "all" ? "on" : ""} onClick={() => setFilter("all")}>{t("all")} ({assets.length})</button>
            {sectors.map((x) => <button key={x} className={filter === x ? "on" : ""} onClick={() => setFilter(x)}>{x.split(" ")[0]} ({assets.filter((y) => y.sector === x).length})</button>)}
          </div>
          <div className="stack">
            {list.map((x) => { const r = riskLevel(x); return (
              <button key={x.asset_id} onClick={() => { setSel(x.asset_id); setTab("overview"); }} style={{ all: "unset", cursor: "pointer", display: "block", width: "100%" }}>
                <div className="photo" style={{ minHeight: 110, outline: a?.asset_id === x.asset_id ? "1px solid var(--accent)" : "none" }}>
                  <Scene kind={sceneFor(x.asset_type)} />
                  <div className="row" style={{ justifyContent: "space-between" }}><div className="t">{x.description}</div><span className={`chip ${r}`}>{t(`risk_${r}` as "risk_high")}</span></div>
                  <div className="s num">{t("loan")} {fac ? "" : ""}{x.facilities?.[0]?.facility_id} · AED {fmt(x.outstanding_allocated_aed, lang, true)} · {lang === "ar" ? x.borrower_ar : x.borrower}</div>
                  <div className="row small muted"><span>{x.asset_id}</span><span>·</span><span>{x.precision}</span>{x.attributes?.switchboard_location && <><span>·</span><span>{t("attr_switchboard")}: {x.attributes.switchboard_location}</span></>}</div>
                </div>
              </button>
            ); })}
          </div>
        </div>

        {a && (
          <div className="card">
            <div className="photo" style={{ minHeight: 190 }}>
              <Scene kind={sceneFor(a.asset_type)} />
              <div className="row" style={{ justifyContent: "space-between" }}><h2 style={{ color: "var(--ink)", fontSize: 20, margin: 0 }}>{a.description} · {a.asset_id}</h2><span className={`chip ${riskLevel(a)}`}>{t(`risk_${riskLevel(a)}` as "risk_high")}</span></div>
              <div className="s num">{lang === "ar" ? a.borrower_ar : a.borrower} · {a.sector} · {t("loan")} {fac?.facility_id} · AED {fmt(a.outstanding_allocated_aed, lang)} {t("outstanding").toLowerCase()}</div>
            </div>
            <div className="tabs" style={{ margin: "14px 0" }}>
              {(["overview", "climate", "financials", "actions"] as const).map((k) => <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{t(k)}</button>)}
            </div>

            {tab === "overview" && (
              <div className="stack">
                <div className="grid cols-3">
                  <div className="card" style={{ padding: 12 }}><div className="muted small">{t("precision")}</div><div>{a.precision}</div></div>
                  <div className="card" style={{ padding: 12 }}><div className="muted small">{t("attr_switchboard")}</div><div>{a.attributes?.switchboard_location ?? t("unknown")}</div></div>
                  <div className="card" style={{ padding: 12 }}><div className="muted small">{t("attr_basement")}</div><div>{a.attributes?.basement ?? t("unknown")}</div></div>
                  <div className="card" style={{ padding: 12 }}><div className="muted small">{t("attr_elevation")}</div><div className="num">{a.attributes?.ground_floor_elevation_m ?? t("unknown")} m</div></div>
                  <div className="card" style={{ padding: 12 }}><div className="muted small">{t("depth")}</div><div className="num">{fmt(a.depth_above_floor_m, lang)} m</div></div>
                  <div className="card" style={{ padding: 12 }}><div className="muted small">{t("state")}</div><span className={`chip ${a.status === "computed" ? "low" : a.status === "unknown" ? "unknown" : "medium"}`}>{a.status}</span></div>
                </div>
                <h2>{t("missing")}</h2>
                {qs.length === 0 ? <div className="muted small">{t("no_questions")}</div> : qs.map((q) => (
                  <div key={q.id} className="question">
                    <div className="q">{lang === "ar" ? q.question_ar : q.question_en}</div>
                    <div className="row">
                      {q.kind === "location" ? (
                        <select value={answers[q.id] ?? q.candidates[0]?.feature_id ?? ""} onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}>{q.candidates.filter((c) => c.feature_id).map((c) => <option key={c.feature_id!} value={c.feature_id!}>{c.label} ({c.precision}, {c.confidence})</option>)}</select>
                      ) : q.kind === "switchboard_location" ? (
                        <select value={answers[q.id] ?? ""} onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}><option value="">{t("answer")}</option><option value="basement">basement / الطابق السفلي</option><option value="ground_floor">ground floor / الطابق الأرضي</option><option value="raised">raised / مرفوعة</option></select>
                      ) : <input value={answers[q.id] ?? ""} onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })} placeholder={t("answer")} />}
                      <button className="btn sm" disabled={busy} onClick={() => answer(q.id, answers[q.id] ?? q.candidates[0]?.feature_id ?? "")}>{t("submit")}</button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {tab === "climate" && (
              <div className="grid cols-3">
                <div className="card" style={{ padding: 12 }}><div className="muted small">{t("hazard_flood")}</div><div className="num">{fmt(a.flood_depth_m, lang)} m</div><span className={`chip ${riskLevel(a)}`}>{riskLevel(a)}</span></div>
                <div className="card" style={{ padding: 12 }}><div className="muted small">{t("hazard_heat")}</div><div className="muted">district-level indicator</div><span className="chip">screening</span></div>
                <div className="card" style={{ padding: 12 }}><div className="muted small">{t("hazard_storm")}</div><div className="muted">{t("not_assessed")}</div><span className="chip unknown">—</span></div>
                <div className="card" style={{ padding: 12, gridColumn: "1 / -1" }}><div className="muted small">{t("scenario")}</div><div>{s?.run ? (lang === "ar" ? s.run.scenario.label_ar : s.run.scenario.label_en) : ""}</div></div>
              </div>
            )}

            {tab === "financials" && (
              <table><tbody>
                <tr><th>{t("outstanding")}</th><td className="num">AED {fmt(a.outstanding_allocated_aed, lang)}</td></tr>
                <tr><th>{t("damage")}</th><td className="num">AED {fmt(a.physical_damage_total_aed, lang)}</td></tr>
                <tr><th>{t("bi")}</th><td className="num">AED {fmt(a.interruption_cost_aed, lang)}</td></tr>
                <tr><th>{t("insured")}</th><td className="num">AED {fmt(a.insured_loss_aed, lang)}</td></tr>
                <tr><th>{t("uninsured")}</th><td className="num">AED {fmt(a.uninsured_physical_damage_aed, lang)}</td></tr>
                <tr><th>{t("collateral")}</th><td className="num">AED {fmt(a.collateral_value_sensitivity_aed, lang)}</td></tr>
                <tr><th>{t("credit")}</th><td className="muted">{t("not_modelled")}</td></tr>
              </tbody></table>
            )}

            {tab === "actions" && (
              <div className="stack">
                <h2>{t("recommended")}</h2>
                {measures.map((m) => (
                  <div key={m.id} className="question row" style={{ justifyContent: "space-between" }}>
                    <div><div>{lang === "ar" ? m.name_ar : m.name_en}</div><div className="muted small num">AED {fmt(m.capex_aed, lang)}</div></div>
                    <a className="btn ghost sm" href={`/risk?asset=${a.asset_id}&measure=${encodeURIComponent(m.id)}`}>{t("comparisons")} →</a>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
