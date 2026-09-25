"use client";
import { useCallback, useEffect, useState } from "react";
import { api, type Question, type Status } from "@/lib/api";
import { fmt, useI18n } from "@/lib/i18n";

const PINS: Record<string, [number, number]> = { "A-001": [44, 52], "A-002": [58, 46], "A-003": [40, 34], "A-004": [10, 82] };

export default function ReviewPage() {
  const { lang, t } = useI18n();
  const [s, setS] = useState<Status | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    try { setS(await api.status()); setErr(null); } catch { setS(null); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const start = async () => {
    setBusy(true);
    try { await api.start(); await load(); } catch (e) { setErr(String(e)); } finally { setBusy(false); }
  };
  const answer = async (q: Question) => {
    const a = answers[q.id] ?? (q.candidates[0]?.feature_id ?? "");
    if (!a) return;
    setBusy(true);
    try { await api.answer(q.id, a); await load(); } catch (e) { setErr(String(e)); } finally { setBusy(false); }
  };
  const decide = async (id: string) => { setBusy(true); try { await api.decide(id, "deeper review required"); await load(); } finally { setBusy(false); } };

  if (!s) {
    return (
      <div className="panel stack">
        <p className="muted">{err ?? ""}</p>
        <button className="primary" onClick={start} disabled={busy}>{busy ? t("starting") : t("start")}</button>
      </div>
    );
  }
  const c = s.coverage; const run = s.run; const conc = run?.aggregation.concentration;
  return (
    <div className="stack">
      <div className="row">
        <span className="chip active">{s.investigation.state}</span>
        <span className="muted">{run ? (lang === "ar" ? run.scenario.label_ar : run.scenario.label_en) : ""}</span>
        <span style={{ marginInlineStart: "auto" }}><button className="ghost" onClick={start} disabled={busy}>{busy ? t("starting") : t("restart")}</button></span>
      </div>
      {err && <div className="panel bad">{err}</div>}
      <div className="grid cols-3">
        <div className="panel">
          <h2>{t("coverage")}</h2>
          <div className="kpi">
            <div><b className="num">{c.assets_location_confirmed} / {c.assets_total}</b><span>{t("confirmed")}</span></div>
            <div><b className="num">{c.assets_district_only}</b><span>{t("district_only")}</span></div>
            <div><b className="num">{c.assets_unresolved}</b><span>{t("unresolved")}</span></div>
            <div><b className="num">{c.documents_with_firewall_flags}</b><span>{t("firewall")}</span></div>
            <div><b className="num">{c.open_questions}</b><span>{t("open_q")}</span></div>
            <div><b className="num">{c.cases_open}</b><span>{t("cases")}</span></div>
          </div>
        </div>
        <div className="panel">
          <h2>{t("concentration")}</h2>
          {conc && (
            <div className="kpi">
              <div><b className="num">{conc.assets_in_footprint.length}</b><span>{t("in_footprint")} · {conc.sectors.length} {t("sectors")}</span></div>
              <div><b className="num">{fmt(conc.outstanding_in_footprint_aed, lang)}</b><span>{t("outstanding")} ({(conc.share_of_portfolio_outstanding * 100).toFixed(1)}% {t("share")})</span></div>
              <div><b className="num">{fmt(conc.physical_damage_total_aed, lang)}</b><span>{t("damage")}</span></div>
            </div>
          )}
          <p className="warn">{run ? (lang === "ar" ? run.aggregation.diversification_warning_ar : run.aggregation.diversification_warning_en) : ""}</p>
        </div>
        <div className="panel">
          <div className="mapbox" aria-label="illustrative footprint sketch">
            <div className="flood" />
            {run?.assets.map((a) => {
              const p = PINS[a.asset_id] ?? [50, 50];
              const unknown = a.status === "unknown";
              return <div key={a.asset_id} className={`pin ${unknown ? "unknown" : ""}`} style={{ left: `${p[0]}%`, top: `${p[1]}%` }}>{a.asset_id} · {a.precision}</div>;
            })}
            <div className="legend">illustrative footprint sketch - not a map</div>
          </div>
        </div>
      </div>

      <div className="panel">
        <h2>{t("assets")}</h2>
        <table>
          <thead><tr><th>{t("asset")}</th><th>{t("borrower")}</th><th>{t("sector")}</th><th>{t("precision")}</th><th>{t("depth")}</th><th>{t("exposure")}</th><th>{t("phys")}</th><th>{t("bi")}</th><th>{t("insured")}</th><th>{t("collateral")}</th><th>{t("credit")}</th><th>{t("status")}</th></tr></thead>
          <tbody>
            {run?.assets.map((a) => (
              <tr key={a.asset_id}>
                <td>{a.asset_id}<br /><span className="muted">{a.description}</span></td>
                <td>{lang === "ar" ? a.borrower_ar : a.borrower}</td>
                <td>{a.sector}</td>
                <td><span className={`chip ${a.precision === "footprint" || a.precision === "parcel" ? "ok" : ""}`}>{a.precision}</span></td>
                <td className="num">{fmt(a.depth_above_floor_m, lang)}</td>
                <td className="num">{fmt(a.outstanding_allocated_aed, lang)}</td>
                <td className="num">{fmt(a.physical_damage_total_aed, lang)}</td>
                <td className="num">{fmt(a.interruption_cost_aed, lang)}</td>
                <td className="num">{fmt(a.insured_loss_aed, lang)}</td>
                <td className="num">{fmt(a.collateral_value_sensitivity_aed, lang)}</td>
                <td className="muted">{t("not_modelled")}</td>
                <td><span className={`chip ${a.status === "computed" ? "ok" : a.status === "unknown" ? "fail" : ""}`}>{a.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid cols-2">
        <div className="panel">
          <h2>{t("questions")}</h2>
          {s.questions.length === 0 && <p className="muted">—</p>}
          {s.questions.map((q) => (
            <div className="question" key={q.id}>
              <div className="q">{lang === "ar" ? q.question_ar : q.question_en}</div>
              <div className="row">
                {q.kind === "location" ? (
                  <select value={answers[q.id] ?? q.candidates[0]?.feature_id ?? ""} onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}>
                    {q.candidates.filter((c) => c.feature_id).map((c) => <option key={c.feature_id!} value={c.feature_id!}>{c.label} ({c.precision}, {c.confidence})</option>)}
                  </select>
                ) : q.kind === "switchboard_location" ? (
                  <select value={answers[q.id] ?? ""} onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}>
                    <option value="">{t("answer")}</option><option value="basement">basement / الطابق السفلي</option><option value="ground_floor">ground floor / الطابق الأرضي</option><option value="raised">raised / مرفوعة</option>
                  </select>
                ) : (
                  <input value={answers[q.id] ?? ""} onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })} placeholder={t("answer")} />
                )}
                <button className="primary" disabled={busy} onClick={() => answer(q)}>{t("send")}</button>
              </div>
            </div>
          ))}
          <h2 style={{ marginTop: 16 }}>{t("cases")}</h2>
          {s.cases.map((k) => (
            <div className="question" key={k.id}>
              <div className="row"><b>{k.title}</b><span className={`chip ${k.status === "decided" ? "ok" : ""}`}>{k.status}</span><span className="muted">{k.owner}</span></div>
              <ul className="muted">{k.evidence_request.map((e) => <li key={e}>{e}</li>)}</ul>
              {k.status !== "decided" ? <button className="ghost" disabled={busy} onClick={() => decide(k.id)}>{t("decide")}</button> : <span className="good">{t("decided")}: {k.decision}</span>}
            </div>
          ))}
        </div>
        <div className="panel">
          <h2>{t("changes")}</h2>
          {!s.diff || s.diff.changes.length === 0 ? <p className="muted">{t("no_changes")}</p> : (
            <>
              <p className="muted">{lang === "ar" ? s.diff.summary_ar : s.diff.summary_en}</p>
              <table>
                <thead><tr><th>{t("asset")}</th><th>field</th><th>{t("kind")}</th><th>from</th><th>to</th></tr></thead>
                <tbody>{s.diff.changes.map((ch, i) => <tr key={i}><td>{ch.asset_id}</td><td>{ch.field}</td><td><span className="chip">{ch.kind}</span></td><td className="num">{ch.from}</td><td className="num">{ch.to}</td></tr>)}</tbody>
              </table>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
