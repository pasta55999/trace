export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API}${path}`, { ...init, headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) }, cache: "no-store" });
  if (!r.ok) {
    let detail: unknown = await r.text();
    try { detail = JSON.parse(detail as string); } catch { /* text */ }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return r.json() as Promise<T>;
}

export const api = {
  health: () => req<{ ok: boolean; llm_provider: string }>("/health"),
  start: () => req<Status>("/investigation/start").then((r) => (r as unknown as { status: Status }).status),
  status: (autostart = false) => req<Status>(`/investigation/status${autostart ? "?autostart=true" : ""}`),
  answer: (id: string, answer: string) => req<{ diff: Diff; status: Status }>(`/investigation/questions/${id}/answer`, { method: "POST", body: JSON.stringify({ answer }) }),
  ask: (question: string) => req<Answer>("/assistant/ask", { method: "POST", body: JSON.stringify({ question }) }),
  measures: () => req<Measure[]>("/measures"),
  compare: (asset_id: string, measure_id: string) => req<Comparison>("/adaptation/compare", { method: "POST", body: JSON.stringify({ asset_id, measure_id }) }),
  briefTree: (asset_id?: string, measure_id?: string) => req<{ tree: unknown; findings: string[] }>(`/report/brief?format=json${asset_id ? `&asset_id=${asset_id}&measure_id=${measure_id}` : ""}`),
  governance: () => req<Governance>("/governance"),
  cycle: () => req<Cycle>("/evolution/cycle", { method: "POST" }),
  guardian: () => req<GuardianCheck[]>("/evolution/guardian"),
  rollback: (agent: string) => req<{ active: string }>(`/evolution/rollback/${agent}?reason=manual`, { method: "POST" }),
  telemetry: (limit = 40) => req<Record<string, unknown>[]>(`/evolution/telemetry?limit=${limit}`),
  decide: (case_id: string, decision: string) => req<Case>(`/cases/${case_id}/decide`, { method: "POST", body: JSON.stringify({ decision, actor: "user:credit-committee" }) }),
};

export type Value = number | { unknown: true; reason: string; reason_ar?: string } | { low: number; high: number; driver: string };
export interface AssetRow { asset_id: string; description: string; asset_type: string; borrower: string; borrower_ar: string; sector: string; precision: string; status: string; depth_above_floor_m: Value; outstanding_allocated_aed: number; physical_damage_total_aed: Value; interruption_cost_aed: Value; insured_loss_aed: Value; uninsured_physical_damage_aed: Value; collateral_value_sensitivity_aed: Value; flood_depth_m: Value; attributes: Record<string, string>; facilities: { facility_id: string; borrower: string; sector: string; allocated_outstanding: number; maturity_year: number }[]; ref: string }
export interface Run { run_id: string; label: string; scenario: { label_en: string; label_ar: string }; assets: AssetRow[]; aggregation: { portfolio_outstanding_aed: number; concentration: { assets_in_footprint: string[]; borrowers: string[]; sectors: string[]; outstanding_in_footprint_aed: number; share_of_portfolio_outstanding: number; physical_damage_total_aed: Value; insured_loss_total_aed: Value }; diversification_warning_en: string; diversification_warning_ar: string; unknown_assets?: { asset_id: string; reason: string; reason_ar: string }[] } }
export interface Question { id: string; asset_id: string; kind: string; question_en: string; question_ar: string; candidates: { feature_id: string | null; label: string; precision: string; confidence: number }[] }
export interface Diff { previous_run: string | null; current_run: string; changes: { asset_id: string; field: string; kind: string; from: string; to: string }[]; summary_en: string; summary_ar: string }
export interface Case { id: string; title: string; owner: string; status: string; evidence_request: string[]; decision: string | null }
export interface Status { investigation: { id: string; state: string }; coverage: Record<string, number>; questions: Question[]; run: Run | null; diff: Diff | null; cases: Case[] }
export interface Answer { text: string; refs: string[]; lang: string; agent: string; genome: string; intent: string }
export interface Measure { id: string; name_en: string; name_ar: string; capex_aed: number; notes_en?: string; notes_ar?: string }
export interface Comparison { measure: Measure; capex_aed: number; avoided_loss_event_aed: Value; residual_damage_event_aed: Value; event_conditional_benefit_cost_ratio?: number; npv_aed: Value; disclaimer_en: string; disclaimer_ar: string; baseline: Record<string, Value>; protected: Record<string, Value> }
export interface GenomeEntry { version: string; active: boolean; parent: string | null; created_at: string; change_record: string; eval: { overall: number } | null; promotion_state: string; hypothesis?: { signature: string } | null }
export interface Governance { engine_version: string; datasets: Record<string, string>; damage_functions: Record<string, { version: string; validation_status: string }>; regulatory_mapping: { version: string; status: string; items: { requirement: string; output: string; coverage: string }[] }; proposals: { id: string; target: string; rationale: string; status: string; created_at: string }[]; genomes: Record<string, GenomeEntry[]>; frozen: boolean; audit_tail: { at: string; actor: string; action: string }[] }
export interface Cycle { hypotheses: { signature: string; tier: string; n: number }[]; outcomes: { agent: string; verdicts?: { candidate: string; pass: boolean; reasons: string[]; overall: number; change: string }[]; promoted?: string | null; stage?: string; change_record?: string; skipped?: string }[]; guardian: GuardianCheck[]; skipped?: string }
export interface GuardianCheck { agent: string; version: string; state: string; sli: { decisions: number; corrections: number; override_rate: number; policy_blocks: number }; action: string; frozen: boolean }
