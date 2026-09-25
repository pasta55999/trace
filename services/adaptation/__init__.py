"""Adaptation comparison: baseline vs protected scenario for a given asset and measure.

Output supports prioritisation and engineering review; it does not certify safety.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from services.aggregation import run_scenario
from services.common import SYNTHETIC, Range, Unknown
from services.register import Store


@lru_cache(maxsize=1)
def measures() -> dict[str, dict[str, Any]]:
    data = yaml.safe_load((SYNTHETIC / "measures.yaml").read_text(encoding="utf-8"))
    return {m["id"]: m for m in data["measures"]}


def _override(measure: dict[str, Any]) -> dict[str, Any]:
    eff = measure["effect"]
    if eff["type"] == "reduce_depth":
        return {"reduce_depth_m": eff["metres"] * measure["assumed_effectiveness"]}
    return {"attributes": {eff["attribute"]: eff["value"]}}


def _num(v: Any) -> float | None:
    if isinstance(v, dict):
        if v.get("unknown"):
            return None
        return (v["low"] + v["high"]) / 2
    return float(v)


def compare(store: Store, asset_id: str, measure_id: str, horizon_years: int = 10, scenario: dict[str, Any] | None = None) -> dict[str, Any]:
    m = measures()[measure_id]
    base = run_scenario(store, scenario, label="baseline")
    prot = run_scenario(store, scenario, overrides={asset_id: _override(m)}, label=f"protected:{measure_id}")
    b = next(r for r in base["assets"] if r["asset_id"] == asset_id)
    p = next(r for r in prot["assets"] if r["asset_id"] == asset_id)
    out: dict[str, Any] = {
        "asset_id": asset_id, "measure": m, "horizon_years": horizon_years,
        "baseline_run": base["run_id"], "protected_run": prot["run_id"],
        "baseline": {k: b[k] for k in ("physical_damage_total_aed", "interruption_cost_aed", "insured_loss_aed", "uninsured_physical_damage_aed")},
        "protected": {k: p[k] for k in ("physical_damage_total_aed", "interruption_cost_aed", "insured_loss_aed", "uninsured_physical_damage_aed")},
        "capex_aed": m["capex_aed"], "maintenance_over_horizon_aed": m["annual_maintenance_aed"] * horizon_years,
        "disclaimer_en": "Avoided loss is conditional on this single illustrative event. Payback is NOT computable without an event-frequency model; shown only as event-conditional ratio.",
        "disclaimer_ar": "الخسارة المتجنبة مشروطة بهذا الحدث التوضيحي الوحيد. لا يمكن حساب فترة الاسترداد دون نموذج لتكرار الأحداث؛ تُعرض فقط كنسبة مشروطة بالحدث.",
    }
    bd, pd_ = _num(b["physical_damage_total_aed"]), _num(p["physical_damage_total_aed"])
    bb, pb = _num(b["interruption_cost_aed"]), _num(p["interruption_cost_aed"])
    if None in (bd, pd_, bb, pb):
        out["avoided_loss_event_aed"] = {"unknown": True, "reason": "baseline or protected result is unknown"}
        out["residual_damage_event_aed"] = p["physical_damage_total_aed"]
        return out
    avoided = round((bd - pd_) + (bb - pb), 2)  # type: ignore[operator]
    out["avoided_loss_event_aed"] = avoided
    out["residual_damage_event_aed"] = p["physical_damage_total_aed"]
    out["event_conditional_benefit_cost_ratio"] = round(avoided / (m["capex_aed"] + out["maintenance_over_horizon_aed"]), 3)
    out["npv_aed"] = {"unknown": True, "reason": "requires annual event probabilities and a discount rate; not registered", "reason_ar": "يتطلب احتمالات سنوية للأحداث ومعدل خصم؛ غير مسجل"}
    out["sensitivity_en"] = f"Result depends on assumed effectiveness {m['assumed_effectiveness']:.0%} and illustrative damage curves."
    return out
