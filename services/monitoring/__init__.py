"""Change detection between scenario runs.

Classifies each change as a data correction, new evidence, model/dataset change or new risk
signal so reviewers can tell a fixed typo from a genuinely different exposure.
"""
from __future__ import annotations

from typing import Any

from services.register import Store

WATCHED = ["flood_depth_m", "physical_damage_total_aed", "interruption_cost_aed", "insured_loss_aed", "collateral_value_sensitivity_aed", "precision", "status"]


def _fmt(v: Any) -> str:
    if isinstance(v, dict):
        if v.get("unknown"):
            return f"unknown ({v.get('reason')})"
        return f"{v['low']:,.0f}-{v['high']:,.0f} (driver: {v['driver']})"
    return f"{v:,.2f}" if isinstance(v, float) else str(v)


def diff_runs(store: Store, prev_id: str | None, curr_id: str) -> dict[str, Any]:
    curr = store.s.runs[curr_id]
    if not prev_id or prev_id not in store.s.runs:
        return {"previous_run": None, "current_run": curr_id, "changes": [], "summary_en": "First run; nothing to compare.", "summary_ar": "التشغيل الأول؛ لا شيء للمقارنة."}
    prev = store.s.runs[prev_id]
    p_by = {r["asset_id"]: r for r in prev["assets"]}
    changes: list[dict[str, Any]] = []
    for r in curr["assets"]:
        old = p_by.get(r["asset_id"])
        if not old:
            changes.append({"asset_id": r["asset_id"], "field": "*", "kind": "new_record", "from": None, "to": "added"})
            continue
        attr_changes = {k: (old["attributes"].get(k), v) for k, v in r["attributes"].items() if old["attributes"].get(k) != v}
        for k in WATCHED:
            if old.get(k) != r.get(k):
                kind = _classify(old, r, k, attr_changes, prev, curr)
                changes.append({"asset_id": r["asset_id"], "field": k, "kind": kind, "from": _fmt(old.get(k)), "to": _fmt(r.get(k)), "because": {a: f"{f} -> {t}" for a, (f, t) in attr_changes.items()}})
    kinds = sorted({c["kind"] for c in changes})
    return {"previous_run": prev_id, "current_run": curr_id, "changes": changes, "summary_en": f"{len(changes)} changed values across {len({c['asset_id'] for c in changes})} assets ({', '.join(kinds) or 'none'}).", "summary_ar": f"{len(changes)} قيمة متغيرة عبر {len({c['asset_id'] for c in changes})} أصول."}


def _classify(old: dict[str, Any], new: dict[str, Any], field: str, attr_changes: dict[str, Any], prev: dict[str, Any], curr: dict[str, Any]) -> str:
    if prev["scenario"] != curr["scenario"]:
        return "scenario_change"
    if curr.get("overrides"):
        return "protective_measure_applied"
    if old.get("precision") != new.get("precision"):
        return "location_resolved" if new.get("precision") != "unresolved" else "location_withdrawn"
    if attr_changes:
        return "new_evidence" if any(f in (None, "unknown") for f, _ in attr_changes.values()) else "data_correction"
    if old["provenance"]["dataset_versions"] != new["provenance"]["dataset_versions"] or old["provenance"]["engine_version"] != new["provenance"]["engine_version"]:
        return "model_or_dataset_change"
    return "new_risk_signal"
