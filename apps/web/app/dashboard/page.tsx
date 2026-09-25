"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import AppShell from "@/components/AppShell";
import Scene, { sceneFor } from "@/components/Scene";
import UAEMap, { type Marker } from "@/components/UAEMap";
import type { Activity, AssetRow, Status } from "@/lib/api";
import { fmt, useI18n, type Lang } from "@/lib/i18n";
import { greetingKey, mid, riskLevel } from "@/lib/risk";
import { useStatus } from "@/lib/useStatus";

const hhmm = (iso: string, lang: Lang) => new Date(iso).toLocaleTimeString(lang === "ar" ? "ar-AE" : "en-GB", { hour: "2-digit", minute: "2-digit" });

function Rail({ s, lang, t }: { s: Status; lang: Lang; t: (k: never) => string }) {
  const T = t as (k: string) => string;
  const AGENT_STEPS = [
    ["intake", "documents_extracted", `${T("ag_intake")} · ${s.documents.length}`],
    ["extract", "documents_extracted", `${T("ag_extract")} · ${s.documents.reduce((n, d) => n + d.fields, 0)}`],
    ["resolve", "location_committed", `${T("ag_resolve")} · ${s.coverage.assets_location_confirmed}/${s.coverage.assets_total}`],
    ["gap", "question_created", `${T("ag_gap")} · ${s.questions.length}`],
    ["case", "case_opened", `${T("ag_critic")}`],
  ] as const;
  const firstAt = (action: string) => s.activity.find((a) => a.action === action)?.at;
  const recent = s.activity.slice().reverse().filter((a) => !["state"].includes(a.action)).slice(0, 6);
  const labelFor = (a: Activity) => ({ portfolio_loaded: "Portfolio loaded", documents_extracted: "Documents extracted", location_committed: `Location resolved · ${a.asset_id ?? ""}`, question_created: `Question raised · ${a.asset_id ?? ""}`, scenario_run: "Scenario computed", case_opened: "Review case opened", question_answered: "Answer recorded", case_decided: "Decision recorded" } as Record<string, string>)[a.action] ?? a.action;
  return (
    <>
      <div className="card flat">
        <div className="head"><span className="ico-box">✦</span><div><h2>{T("intel")}</h2><div className="sub">{T("intel_sub")}</div></div></div>
        <div className="list feed">
          {AGENT_STEPS.map(([k, action, label]) => { const at = firstAt(action); const pending = k === "gap" && s.questions.length > 0; return (
            <div className="item" key={k}><span className={`tick ${pending ? "amber" : at ? "" : "grey"}`}>{pending ? "!" : at ? "✓" : "○"}</span><div><div className="t">{label}</div></div><span className="time num">{at ? hhmm(at, lang) : "—"}</span></div>
          ); })}
        </div>
      </div>
      <div className="card flat">
        <div className="head"><h2>{T("recent")}</h2><Link href="/agents" className="link right">{T("view_all")} →</Link></div>
        <div className="list feed">
          {recent.map((a, i) => <div className="item" key={i}><span className={`tick ${a.actor.startsWith("user") ? "sea" : a.action.includes("question") ? "amber" : ""}`}>{a.actor.startsWith("user") ? "→" : "✓"}</span><div><div className="t">{labelFor(a)}</div><div className="m">{a.actor}</div></div><span className="time num">{hhmm(a.at, lang)}</span></div>)}
        </div>
      </div>
      <div className="card flat">
        <div className="head"><h2>{T("bilingual_docs")}</h2><Link href="/portfolio" className="link right">{T("view_all")} →</Link></div>
        {s.documents.slice(0, 3).map((d) => (
          <div className="row" key={d.id} style={{ padding: "6px 0" }}>
            <span className="ico-box grey" style={{ width: 28, height: 28, fontSize: 12 }}>▤</span>
            <div style={{ minWidth: 0 }}><div className="small" dir="auto" style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: 200 }}>{d.title}</div><div className="xs muted">{d.related_collateral} · {d.fields} fields{d.firewall_flags.length ? " · quarantined text" : ""}</div></div>
            <span className={`chip ${d.language === "ar" ? "accent" : ""}`} style={{ marginInlineStart: "auto" }}>{d.language === "ar" ? T("arabic") : d.language === "en" ? T("english") : "ar/en"}</span>
          </div>
        ))}
      </div>
      <Link href="/reports" className="cta-card">
        <Scene kind="cold" style={{ opacity: .9 }} />
        <div style={{ background: "rgba(255,255,255,.85)", borderRadius: 12, padding: 12 }}>
          <div style={{ fontWeight: 600 }}>{T("cta_title")}</div>
          <div className="small muted" style={{ margin: "4px 0 10px" }}>{T("cta_sub")}</div>
          <span className="btn sm">{T("cta_btn")} →</span>
        </div>
      </Link>
    </>
  );
}

export default function Dashboard() {
  const { lang, t, prefs } = useI18n();
  const router = useRouter();
  const { status: s, error } = useStatus();
  const [mapTab, setMapTab] = useState<"uae" | "region" | "all">("uae");
  if (!s) return <AppShell><div className="empty">{error ?? t("running")}</div></AppShell>;
  const run = s.run!; const assets = run.assets; const c = run.aggregation.concentration;
  const total = run.aggregation.portfolio_outstanding_aed;
  const inFoot = assets.filter((a) => c.assets_in_footprint.includes(a.asset_id));
  const exposurePct = c.share_of_portfolio_outstanding * 100;
  const sectors = new Set(assets.map((a) => a.sector)).size;
  const locByAsset = new Map(s.locations.map((l) => [l.asset_id, l]));
  const markers: Marker[] = assets.map((a) => { const l = locByAsset.get(a.asset_id); return { id: a.asset_id, lon: l?.lon ?? null, lat: l?.lat ?? null, level: riskLevel(a), label: `${a.asset_id} · ${a.description}`, district: l?.district_id }; });
  const dmg = (rows: AssetRow[]) => rows.reduce((x, a) => x + (mid(a.physical_damage_total_aed) ?? 0), 0);
  const impactRows = [
    { k: "hazard_flood", ico: "◍", cls: "sea", n: inFoot.length, exposure: c.outstanding_in_footprint_aed, impact: dmg(inFoot) },
    { k: "hazard_heat", ico: "☼", cls: "amber", n: assets.filter((a) => a.precision !== "unresolved").length, exposure: null, impact: null },
    { k: "hazard_storm", ico: "≋", cls: "grey", n: 0, exposure: null, impact: null },
    { k: "hazard_sea", ico: "◠", cls: "grey", n: 0, exposure: null, impact: null },
  ];
  const maxImpact = Math.max(1, ...impactRows.map((r) => r.impact ?? 0));
  const featured = assets.slice().sort((a, b) => (mid(b.physical_damage_total_aed) ?? -1) - (mid(a.physical_damage_total_aed) ?? -1)).slice(0, 3);

  return (
    <AppShell rail={<Rail s={s} lang={lang} t={t as never} />}>
      <div className="hero">
        <div><h1>{t(greetingKey())}, {prefs.name}.</h1><div className="sub">{t("overview_sub")}</div></div>
        <div className="right"><span className="live">{t("live")}</span><span>{t("last_updated")} <span className="num">{hhmm(s.activity.at(-1)?.at ?? new Date().toISOString(), lang)}</span></span></div>
      </div>
      <div className="note" style={{ marginBottom: 12 }}>{t("synthetic")}</div>

      <div className="grid cols-4">
        <div className="card kpi"><div className="row"><span className="ico-box">◈</span><span className="label">{t("kpi_portfolio")}</span></div><div className="value num">AED {fmt(total, lang, true)}</div><div className="foot"><span>{t("monitored")}</span><span className="delta">{assets.length} {t("props_fac").toLowerCase()}</span></div></div>
        <div className="card kpi"><div className="row"><span className="ico-box">◫</span><span className="label">{t("kpi_linked")}</span></div><div className="value num">{s.coverage.assets_location_confirmed}<span className="muted" style={{ fontSize: 16 }}> / {s.coverage.assets_total}</span></div><div className="foot"><span>{t("props_fac")}</span><span className="delta">{sectors} sectors</span></div></div>
        <div className="card kpi"><div className="row"><span className="ico-box amber">△</span><span className="label">{t("kpi_exposure")}</span></div><div className="value num">{exposurePct.toFixed(1)}%</div><div className="foot"><span>{t("potentially")}</span><span className="delta bad">AED {fmt(c.outstanding_in_footprint_aed, lang, true)}</span></div></div>
        <div className="card kpi"><div className="row"><span className="ico-box sea">▤</span><span className="label">{t("kpi_reviews")}</span></div><div className="value num">{s.questions.length + s.cases.filter((k) => k.status !== "decided").length}</div><div className="foot"><span>{t("requiring")}</span><span className="delta">{t("open_questions_n", { n: s.questions.length })}</span></div></div>
      </div>

      <div className="grid cols-map" style={{ marginTop: 14 }}>
        <div className="card">
          <div className="head"><div><h2>{t("map_title")}</h2><div className="sub">{t("map_sub")}</div></div>
            <div className="right"><div className="tabs">{(["uae", "region", "all"] as const).map((k) => <button key={k} className={mapTab === k ? "on" : ""} onClick={() => setMapTab(k)}>{k === "uae" ? "UAE" : k === "region" ? "Region" : "All"}</button>)}</div></div></div>
          <div className="mapwrap">
            <UAEMap markers={markers} onSelect={(id) => router.push(`/portfolio?asset=${id}`)} />
            <span className="caption">{lang === "ar" ? run.scenario.label_ar : run.scenario.label_en}</span>
            <div className="legend"><span><span className="dot" style={{ background: "var(--red)" }} /> {t("risk_high")}</span><span><span className="dot" style={{ background: "var(--amber)" }} /> {t("risk_medium")}</span><span><span className="dot" style={{ background: "var(--sage)" }} /> {t("risk_low")}</span><span><span className="dot" style={{ background: "var(--faint)" }} /> {t("risk_unknown")}</span></div>
            <span className="north">N ↑</span>
          </div>
        </div>
        <div className="card">
          <div className="head"><div><h2>{t("signals")}</h2><div className="sub">{t("signals_sub")}</div></div></div>
          <div className="list">
            {impactRows.map((r) => (
              <Link href="/risk" className="item" key={r.k}>
                <span className={`ico-box ${r.cls}`}>{r.ico}</span>
                <div><div className="title">{t(r.k as "hazard_flood")}</div><div className="meta num">{r.n} {t("assets_col").toLowerCase()} · {r.exposure !== null ? `AED ${fmt(r.exposure, lang, true)}` : t("not_assessed")}</div></div>
                <span className="chev">›</span>
              </Link>
            ))}
          </div>
          {c.sectors.length > 1 && <div className="chip high" style={{ marginTop: 10 }}>⚠ {lang === "ar" ? run.aggregation.diversification_warning_ar : run.aggregation.diversification_warning_en}</div>}
        </div>
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <div className="head"><div><h2>{t("impact_title")}</h2><div className="sub">{t("impact_sub")}</div></div><div className="right"><span className="tabs"><button className="on">{t("all_hazards")}</button></span></div></div>
        <table>
          <thead><tr><th>{t("hazard")}</th><th>{t("assets_col")}</th><th>{t("exposure_col")}</th><th style={{ width: "40%" }}>{t("impact_col")}</th><th></th></tr></thead>
          <tbody>
            {impactRows.map((r) => (
              <tr key={r.k}>
                <td><span className="row"><span className={`ico-box ${r.cls}`} style={{ width: 26, height: 26, fontSize: 12 }}>{r.ico}</span>{t(r.k as "hazard_flood")}</span></td>
                <td className="num">{r.n}</td>
                <td className="num">{r.exposure !== null ? `AED ${fmt(r.exposure, lang, true)}` : <span className="muted">—</span>}</td>
                <td>{r.impact !== null ? <div className={`bar ${r.cls === "sea" ? "" : r.cls}`}><i style={{ width: `${(r.impact / maxImpact) * 100}%` }} /></div> : <div className="bar"><i style={{ width: 0 }} /></div>}</td>
                <td className="num muted small">{r.impact !== null ? `AED ${fmt(r.impact, lang, true)}` : t("not_assessed")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <div className="head"><h2>{t("featured")}</h2><Link href="/portfolio" className="link right">{t("view_all")} →</Link></div>
        <div className="grid cols-3">
          {featured.map((a) => { const r = riskLevel(a); const frac = mid(a.physical_damage_total_aed); const rv = a.outstanding_allocated_aed; const p = frac !== null && rv ? Math.min(100, Math.round((frac / rv) * 100)) : null; return (
            <Link href={`/portfolio?asset=${a.asset_id}`} className="feature" key={a.asset_id}>
              <div className="thumb"><Scene kind={sceneFor(a.asset_type)} /></div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="row" style={{ justifyContent: "space-between" }}><div style={{ fontWeight: 600 }}>{lang === "ar" ? a.borrower_ar : a.borrower}</div><span className="chip">{a.asset_type.replace(/_/g, " ")}</span></div>
                <div className="xs muted num">{t("loan")} {a.facilities?.[0]?.facility_id} · {a.asset_id} · {a.precision}</div>
                <div className="row" style={{ justifyContent: "space-between", marginTop: 8 }}>
                  <div><div className="num" style={{ fontWeight: 700 }}>AED {fmt(rv, lang, true)}</div><div className="xs muted">{t("loan_amount")}</div></div>
                  <span className={`chip ${r}`}>{t(`risk_${r}` as "risk_high")}</span>
                  <div className="row" style={{ gap: 6 }}><div className={`ring ${r}`} style={{ ["--p" as string]: p ?? 0 }}><span>{p ?? "?"}</span></div><span className="xs muted">{t("dmg_frac")} %</span></div>
                </div>
              </div>
            </Link>
          ); })}
        </div>
      </div>
    </AppShell>
  );
}
