"use client";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { BarChart, BarLabels } from "@/components/Charts";
import Scene, { sceneFor } from "@/components/Scene";
import { fmt, useI18n } from "@/lib/i18n";
import { greetingKey, mid, riskLevel } from "@/lib/risk";
import { useStatus } from "@/lib/useStatus";

const PINS: Record<string, [number, number]> = { "A-001": [46, 50], "A-002": [60, 42], "A-003": [42, 30], "A-004": [14, 78] };

export default function Dashboard() {
  const { lang, t, prefs } = useI18n();
  const { status: s, busy, error, restart } = useStatus();
  const run = s?.run ?? null;
  const assets = run?.assets ?? [];
  const high = assets.filter((a) => riskLevel(a) === "high");
  const sectors = new Map<string, { n: number; outstanding: number; worst: string }>();
  for (const a of assets) {
    const g = sectors.get(a.sector) ?? { n: 0, outstanding: 0, worst: "low" };
    g.n += 1; g.outstanding += a.outstanding_allocated_aed;
    const r = riskLevel(a); if (r === "high" || (r === "medium" && g.worst !== "high") || (r === "unknown" && g.worst === "low")) g.worst = r;
    sectors.set(a.sector, g);
  }
  const bars = assets.map((a) => { const v = a.physical_damage_total_aed; const r = typeof v === "object" && "low" in v ? v : null; return { label: a.asset_id, value: mid(v), low: r?.low, high: r?.high }; });
  const c = run?.aggregation.concentration;

  return (
    <AppShell title={`${t(greetingKey())}, ${prefs.name}`} subtitle={t("snapshot")}>
      {error && <div className="card" style={{ color: "var(--high)" }}>{error}</div>}
      {!s ? <div className="empty"><div className="muted">{t("running")}</div></div> : (
        <div className="stack">
          <div className="grid cols-4">
            <div className="card kpi"><span className="ico">◈</span><div><div className="label">{t("kpi_portfolio")}</div><div className="value num">AED {fmt(run?.aggregation.portfolio_outstanding_aed ?? 0, lang, true)}</div><div className="foot">{s.investigation.state} · {t("last_updated")} <span className="num">{new Date().toLocaleTimeString(lang === "ar" ? "ar-AE" : "en-GB", { hour: "2-digit", minute: "2-digit" })}</span></div></div></div>
            <div className="card kpi"><span className="ico">▦</span><div><div className="label">{t("kpi_assets")}</div><div className="value num">{s.coverage.assets_total}</div><div className="foot">{t("across_sectors", { n: sectors.size })} · {t("confirmed_of", { a: s.coverage.assets_location_confirmed, b: s.coverage.assets_total })}</div></div></div>
            <div className="card kpi"><span className="ico" style={{ background: "rgba(255,107,107,.14)", color: "var(--high)" }}>▲</span><div><div className="label">{t("kpi_high")}</div><div className="value num">{high.length}</div><div className="foot" style={{ color: "var(--high)" }}>{t("needs_attention")} · AED {fmt(high.reduce((x, a) => x + a.outstanding_allocated_aed, 0), lang, true)}</div></div></div>
            <div className="card kpi"><span className="ico" style={{ background: "rgba(71,201,138,.14)", color: "var(--low)" }}>✓</span><div><div className="label">{t("kpi_actions")}</div><div className="value num">{s.questions.length + (c ? 1 : 0)}</div><div className="foot">{t("open_questions_n", { n: s.questions.length })} · {s.cases.length} case</div></div></div>
          </div>

          <div className="grid cols-2-1">
            <div className="card">
              <div className="row" style={{ justifyContent: "space-between" }}><h2>{t("by_sector")}</h2><Link href="/portfolio" className="muted small">{t("view_details")} →</Link></div>
              <div className="grid cols-3" style={{ height: "calc(100% - 34px)" }}>
                {[...sectors.entries()].map(([sec, g]) => (
                  <Link key={sec} href="/portfolio" className="photo" style={{ minHeight: 210 }}>
                    <Scene kind={sceneFor(sec)} />
                    <div className="t">{sec}</div>
                    <div className="s num">AED {fmt(g.outstanding, lang, true)} · {g.n} {t("properties")}</div>
                    <span className={`chip ${g.worst}`}>{t(`risk_${g.worst}` as "risk_high")}</span>
                  </Link>
                ))}
              </div>
            </div>
            <div className="card">
              <h2>{t("outlook")}</h2>
              <div className="map">
                <div className="grid-lines" /><div className="flood" /><div className="heat" />
                {assets.map((a) => { const p = PINS[a.asset_id] ?? [50, 50]; const r = riskLevel(a); return <div key={a.asset_id} className={`pin ${r === "unknown" ? "dashed" : ""}`} style={{ left: `${p[0]}%`, top: `${p[1]}%` }}><span className="dot" style={{ background: `var(--${r})` }} />{a.asset_id}</div>; })}
                <span className="tag">UAE · {run ? (lang === "ar" ? run.scenario.label_ar : run.scenario.label_en) : ""}</span>
                <div className="legend"><span><span className="dot" style={{ background: "var(--blue)" }} /> {t("flood_risk")}</span><span><span className="dot" style={{ background: "var(--high)" }} /> {t("heat_stress")}</span><span>{t("sketch")}</span></div>
              </div>
            </div>
          </div>

          <div className="grid cols-2-1">
            <div className="card">
              <div className="row" style={{ justifyContent: "space-between" }}><h2>{t("exposure_chart")}</h2><span className="muted small">AED</span></div>
              <BarChart rows={bars} /><BarLabels rows={bars} />
            </div>
            <div className="card">
              <h2>{t("top_hazards")}</h2>
              <div className="stack">
                {[
                  { k: "hazard_flood", pct: c && run ? c.share_of_portfolio_outstanding : 0, note: `${c?.assets_in_footprint.length ?? 0} ${t("in_footprint")}` },
                  { k: "hazard_heat", pct: null, note: "district-level indicator only (25 km)" },
                  { k: "hazard_storm", pct: null, note: t("not_assessed") },
                  { k: "hazard_sea", pct: null, note: t("not_assessed") },
                ].map((h) => (
                  <div key={h.k}>
                    <div className="row" style={{ justifyContent: "space-between" }}><span>{t(h.k as "hazard_flood")}</span><span className="num muted small">{h.pct === null ? "—" : `${(h.pct * 100).toFixed(0)}%`}</span></div>
                    <div className="bar"><i style={{ width: `${(h.pct ?? 0) * 100}%` }} /></div>
                    <div className="muted small">{h.note}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {c && (
            <div className="card" style={{ borderColor: "rgba(255,107,107,.35)" }}>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <div><h2 style={{ color: "var(--high)" }}>{t("concentration")}</h2><div>{lang === "ar" ? run!.aggregation.diversification_warning_ar : run!.aggregation.diversification_warning_en}</div><div className="muted small num">{c.borrowers.join(" · ")} — AED {fmt(c.outstanding_in_footprint_aed, lang)} ({(c.share_of_portfolio_outstanding * 100).toFixed(1)}% {t("share")})</div></div>
                <div className="row"><Link href="/risk" className="btn sm">{t("nav_risk")} →</Link><button className="btn ghost sm" onClick={restart} disabled={busy}>{busy ? t("running") : t("restart")}</button></div>
              </div>
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
