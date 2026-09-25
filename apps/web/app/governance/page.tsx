"use client";
import { useCallback, useEffect, useState } from "react";
import { api, type Cycle, type Governance, type GuardianCheck } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export default function GovernancePage() {
  const { t } = useI18n();
  const [g, setG] = useState<Governance | null>(null);
  const [guard, setGuard] = useState<GuardianCheck[]>([]);
  const [tel, setTel] = useState<Record<string, unknown>[]>([]);
  const [cycle, setCycle] = useState<Cycle | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [gv, gd, tl] = await Promise.all([api.governance(), api.guardian(), api.telemetry(30)]);
      setG(gv); setGuard(gd); setTel(tl); setErr(null);
    } catch (e) { setErr(String(e)); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const runCycle = async () => { setBusy(true); try { setCycle(await api.cycle()); await load(); } catch (e) { setErr(String(e)); } finally { setBusy(false); } };
  const rollback = async (agent: string) => { setBusy(true); try { await api.rollback(agent); await load(); } finally { setBusy(false); } };

  if (!g) return <div className="panel muted">{err ?? "…"}</div>;
  return (
    <div className="stack">
      <h2 style={{ margin: 0 }}>{t("gov_title")}</h2>
      {g.frozen && <div className="panel bad"><b>{t("frozen")}</b></div>}
      {err && <div className="panel bad">{err}</div>}
      <div className="grid cols-3">
        <div className="panel">
          <h2>{t("engine")} / {t("datasets")}</h2>
          <div className="num">{g.engine_version}</div>
          <table><tbody>{Object.entries(g.datasets).map(([k, v]) => <tr key={k}><td className="muted">{k}</td><td className="num">{v}</td></tr>)}</tbody></table>
        </div>
        <div className="panel">
          <h2>{t("dmg")}</h2>
          <table><tbody>{Object.entries(g.damage_functions).map(([k, v]) => <tr key={k}><td className="muted">{k}</td><td className="num">{v.version}</td><td><span className="chip">{v.validation_status}</span></td></tr>)}</tbody></table>
        </div>
        <div className="panel">
          <h2>{t("reg")} <span className="chip">{g.regulatory_mapping.version}</span></h2>
          <p className="muted">{g.regulatory_mapping.status}</p>
          <table><tbody>{g.regulatory_mapping.items.map((i) => <tr key={i.requirement}><td>{i.requirement}</td><td className="muted">{i.output}</td><td><span className="chip">{i.coverage}</span></td></tr>)}</tbody></table>
        </div>
      </div>

      <div className="panel">
        <div className="row">
          <h2 style={{ margin: 0 }}>{t("genomes")}</h2>
          <span style={{ marginInlineStart: "auto" }}><button className="primary" disabled={busy || g.frozen} onClick={runCycle}>{t("run_cycle")}</button></span>
        </div>
        <p className="muted">{t("tiers")}</p>
        {Object.entries(g.genomes).map(([agent, versions]) => (
          <div key={agent} style={{ marginBottom: 10 }}>
            <div className="row"><b>{agent}</b>{versions.length > 1 && <button className="ghost" disabled={busy} onClick={() => rollback(agent)}>{t("rollback")}</button>}</div>
            <table>
              <thead><tr><th>{t("version")}</th><th>{t("state")}</th><th>{t("change")}</th><th>{t("score")}</th><th>hypothesis</th><th>created</th></tr></thead>
              <tbody>
                {versions.map((v) => (
                  <tr key={v.version}>
                    <td className="num">{v.version} {v.active && <span className="chip active">{t("active")}</span>}</td>
                    <td><span className={`chip ${v.promotion_state === "rolled_back" ? "fail" : v.promotion_state === "full" ? "ok" : ""}`}>{v.promotion_state}</span></td>
                    <td dir="auto">{v.change_record}</td>
                    <td className="num">{v.eval?.overall ?? "—"}</td>
                    <td className="muted">{v.hypothesis?.signature ?? "—"}</td>
                    <td className="num muted">{v.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>

      {cycle && (
        <div className="panel">
          <h2>Last evolution cycle</h2>
          {cycle.skipped && <p className="bad">{cycle.skipped}</p>}
          <p className="muted">hypotheses: {cycle.hypotheses.map((h) => `${h.signature} (tier ${h.tier}, n=${h.n})`).join(", ") || "none"}</p>
          {cycle.outcomes.map((o, i) => (
            <div key={i} className="stack">
              {o.skipped && <p className="bad">{o.agent}: {o.skipped}</p>}
              <table>
                <thead><tr><th>candidate</th><th>verdict</th><th>score</th><th>change</th><th>reasons</th></tr></thead>
                <tbody>{o.verdicts?.map((v) => <tr key={v.candidate}><td className="num">{v.candidate}</td><td><span className={`chip ${v.pass ? "ok" : "fail"}`}>{v.pass ? "pass" : "fail"}</span></td><td className="num">{v.overall}</td><td dir="auto">{v.change}</td><td className="muted">{v.reasons.join("; ")}</td></tr>)}</tbody>
              </table>
              <p>{o.promoted ? <span className="good">promoted {o.promoted} ({o.stage}): {o.change_record}</span> : <span className="muted">nothing promoted</span>}</p>
            </div>
          ))}
        </div>
      )}

      <div className="grid cols-2">
        <div className="panel">
          <h2>{t("guardian")}</h2>
          {guard.map((gc) => (
            <div key={gc.agent} className="row">
              <b>{gc.agent}</b><span className="num">{gc.version}</span><span className="chip">{gc.state}</span>
              <span className="muted num">override {gc.sli.override_rate} · decisions {gc.sli.decisions} · blocks {gc.sli.policy_blocks}</span>
              <span className={`chip ${gc.action.startsWith("rolled") ? "fail" : gc.action === "none" ? "" : "ok"}`}>{gc.action}</span>
            </div>
          ))}
          <h2 style={{ marginTop: 14 }}>{t("proposals")}</h2>
          {g.proposals.length === 0 ? <p className="muted">—</p> : <table><tbody>{g.proposals.map((p) => <tr key={p.id}><td className="num">{p.id}</td><td>{p.target}</td><td className="muted">{p.rationale}</td><td><span className="chip">{p.status}</span></td></tr>)}</tbody></table>}
        </div>
        <div className="panel">
          <h2>{t("telemetry")}</h2>
          <pre style={{ maxHeight: 260, overflow: "auto" }}>{tel.slice().reverse().map((e) => `${e.at}  ${e.kind}  ${e.agent}  ${e.signature ?? e.tool ?? e.decision ?? e.invariant ?? e.version ?? ""}`).join("\n")}</pre>
          <h2>{t("audit")}</h2>
          <pre style={{ maxHeight: 200, overflow: "auto" }}>{g.audit_tail.slice().reverse().map((a) => `${a.at}  ${a.actor}  ${a.action}`).join("\n")}</pre>
        </div>
      </div>
    </div>
  );
}
