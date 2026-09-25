"use client";
import { useCallback, useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { api, type Cycle, type Governance, type GuardianCheck } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useStatus } from "@/lib/useStatus";

const STEPS = [
  { k: "intake", ico: "▤", cls: "a", states: ["extracted", "linked", "located", "assessed", "aggregated", "reviewed", "reported"] },
  { k: "extract", ico: "✓", cls: "b", states: ["extracted", "linked", "located", "assessed", "aggregated", "reviewed", "reported"] },
  { k: "resolve", ico: "◎", cls: "b", states: ["located", "assessed", "aggregated", "reviewed", "reported"] },
  { k: "gap", ico: "?", cls: "d", states: ["assessed", "aggregated", "reviewed", "reported"] },
  { k: "analyst", ico: "✦", cls: "c", states: ["assessed", "aggregated", "reviewed", "reported"] },
  { k: "critic", ico: "◑", cls: "c", states: ["reported"] },
] as const;

export default function AgentsPage() {
  const { t } = useI18n();
  const { status: s } = useStatus();
  const [g, setG] = useState<Governance | null>(null);
  const [guard, setGuard] = useState<GuardianCheck[]>([]);
  const [tel, setTel] = useState<Record<string, unknown>[]>([]);
  const [cycle, setCycle] = useState<Cycle | null>(null);
  const [busy, setBusy] = useState(false);
  const load = useCallback(async () => {
    const [gv, gd, tl] = await Promise.all([api.governance(), api.guardian(), api.telemetry(30)]);
    setG(gv); setGuard(gd); setTel(tl);
  }, []);
  useEffect(() => { load().catch(() => {}); }, [load]);
  const runCycle = async () => { setBusy(true); try { setCycle(await api.cycle()); await load(); } finally { setBusy(false); } };
  const rollback = async (agent: string) => { setBusy(true); try { await api.rollback(agent); await load(); } finally { setBusy(false); } };

  const state = s?.investigation.state ?? "uploaded";
  const openQ = s?.questions.length ?? 0;
  const stepState = (st: readonly string[], k: string) => (st.includes(state) ? (k === "gap" && openQ > 0 ? "active" : k === "analyst" ? "active" : "completed") : state === "uploaded" ? "waiting" : "in_progress");

  return (
    <AppShell>
      <div className="hero"><div><h1>{t("agents_title")}</h1><div className="sub">{t("agents_sub")}</div></div></div>
      <div className="grid cols-1-2">
        <div className="card">
          <div className="timeline">
            {STEPS.map((st, i) => { const ss = stepState(st.states, st.k); return (
              <div key={st.k} className="step">
                <span className={`ico ${st.cls}`}>{st.ico}</span>
                <div><div>{i + 1}. {t(`ag_${st.k}` as "ag_intake")}</div><div className="desc">{t(`ag_${st.k}_d` as "ag_intake_d")}</div></div>
                <span className={`chip ${ss === "completed" ? "low" : ss === "active" ? "accent" : ss === "in_progress" ? "medium" : ""}`}>{t(ss as "completed")}</span>
              </div>
            ); })}
          </div>
          <div className="muted small" style={{ marginTop: 12 }}>✦ {t("powered")}</div>
          {guard.map((gc) => (
            <div key={gc.agent} className="question" style={{ marginTop: 12 }}>
              <div className="row" style={{ justifyContent: "space-between" }}><b>{t("guardian")} · {gc.agent}</b><span className={`chip ${gc.action.startsWith("rolled") ? "high" : gc.action === "none" ? "" : "low"}`}>{gc.action}</span></div>
              <div className="muted small num">{gc.version} · {gc.state} · override {gc.sli.override_rate} · decisions {gc.sli.decisions} · blocks {gc.sli.policy_blocks}</div>
            </div>
          ))}
        </div>

        <div className="stack">
          <div className="card">
            <div className="row" style={{ justifyContent: "space-between" }}>
              <h2>{t("evolution")} — {t("genomes")}</h2>
              <div className="row">
                {g && Object.keys(g.genomes).some((a) => g.genomes[a].length > 1) && <button className="btn ghost sm" disabled={busy} onClick={() => rollback("resolution")}>{t("rollback")}</button>}
                <button className="btn sm" disabled={busy || g?.frozen} onClick={runCycle}>{busy ? "…" : t("run_cycle")}</button>
              </div>
            </div>
            {g?.frozen && <div className="chip high" style={{ marginBottom: 8 }}>{t("frozen")}</div>}
            <div className="muted small" style={{ marginBottom: 10 }}>{t("tiers")}</div>
            {g && Object.entries(g.genomes).map(([agent, versions]) => (
              <div key={agent} style={{ marginBottom: 8 }}>
                <div className="row"><b>{agent}</b><span className="muted small">{versions.length} {t("version").toLowerCase()}{versions.length > 1 ? "s" : ""}</span></div>
                {versions.length > 1 && (
                  <table><thead><tr><th>{t("version")}</th><th>{t("state")}</th><th>{t("change")}</th><th>{t("score")}</th></tr></thead><tbody>
                    {versions.map((v) => <tr key={v.version}><td className="num">{v.version} {v.active && <span className="chip accent">{t("active")}</span>}</td><td><span className={`chip ${v.promotion_state === "rolled_back" ? "high" : v.promotion_state === "full" ? "low" : "medium"}`}>{v.promotion_state}</span></td><td dir="auto">{v.change_record}</td><td className="num">{v.eval?.overall ?? "—"}</td></tr>)}
                  </tbody></table>
                )}
              </div>
            ))}
          </div>

          {cycle && (
            <div className="card">
              <h2>{t("last_cycle")}</h2>
              {cycle.skipped && <div className="chip high">{cycle.skipped}</div>}
              <div className="muted small">hypotheses: {cycle.hypotheses.map((h) => `${h.signature} (tier ${h.tier}, n=${h.n})`).join(", ") || "none"}</div>
              {cycle.outcomes.map((o, i) => (
                <div key={i} style={{ marginTop: 8 }}>
                  <table><tbody>{o.verdicts?.map((v) => <tr key={v.candidate}><td><span className={`chip ${v.pass ? "low" : "high"}`}>{v.pass ? "pass" : "fail"}</span></td><td className="num">{v.overall}</td><td dir="auto">{v.change}<div className="muted small">{v.reasons.join("; ")}</div></td></tr>)}</tbody></table>
                  <div className="small" style={{ marginTop: 6 }}>{o.promoted ? <span style={{ color: "var(--low)" }}>{t("promoted")} {o.promoted} ({o.stage}): {o.change_record}</span> : <span className="muted">{o.skipped ?? t("nothing_promoted")}</span>}</div>
                </div>
              ))}
            </div>
          )}

          <div className="grid cols-2">
            <div className="card"><h2>{t("proposals")}</h2>{!g || g.proposals.length === 0 ? <div className="muted small">—</div> : g.proposals.map((p) => <div key={p.id} className="small"><span className="chip medium">{p.status}</span> {p.target} — <span className="muted">{p.rationale}</span></div>)}</div>
            <div className="card"><h2>{t("telemetry")}</h2><pre style={{ maxHeight: 220, overflow: "auto" }}>{tel.slice().reverse().map((e) => `${String(e.at).slice(11, 19)}  ${e.kind}  ${e.agent}  ${e.signature ?? e.tool ?? e.decision ?? e.invariant ?? e.version ?? ""}`).join("\n")}</pre></div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
