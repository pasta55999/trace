"""Deterministic financial engine. Pure functions; same inputs -> identical outputs.

Financial categories are kept separate and never summed across:
  replacement value != market value; physical damage != insured loss != lender credit loss.
Expected annual loss is Unknown unless a probabilistic event model is registered.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from services import vulnerability as vuln
from services.common import Provenance, Range, Unknown

ENGINE_VERSION = "fin-engine 0.1.0-prototype"
DAILY_BI_RATE = 0.0004  # stated assumption: daily interruption cost = 0.04% of insured-type value base
Value = float | Range | Unknown


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def mul(value: float | None, frac: Value, unknown_reason: str = "value missing") -> Value:
    if value is None:
        return Unknown(reason=unknown_reason)
    if isinstance(frac, Unknown):
        return frac
    if isinstance(frac, Range):
        return Range(low=round(value * frac.low, 2), high=round(value * frac.high, 2), driver=frac.driver)
    return round(value * frac, 2)


def add(*vals: Value) -> Value:
    unknowns = [v for v in vals if isinstance(v, Unknown)]
    if unknowns:
        return Unknown(reason="; ".join(sorted({u.reason for u in unknowns})))
    lo = sum(v.low if isinstance(v, Range) else v for v in vals)
    hi = sum(v.high if isinstance(v, Range) else v for v in vals)
    drivers = sorted({v.driver for v in vals if isinstance(v, Range)})
    return round(lo, 2) if not drivers else Range(low=round(lo, 2), high=round(hi, 2), driver=",".join(drivers))


def apply_terms(loss: Value, deductible: float | None, limit: float | None) -> Value:
    def one(x: float) -> float:
        d = deductible or 0.0
        v = max(x - d, 0.0)
        return round(min(v, limit) if limit is not None else v, 2)

    if isinstance(loss, Unknown):
        return loss
    if isinstance(loss, Range):
        return Range(low=one(loss.low), high=one(loss.high), driver=loss.driver)
    return one(loss)


class AssetInputs(BaseModel):
    asset_id: str
    asset_type: str
    replacement_value_aed: float | None
    equipment_value_aed: float | None
    stock_value_aed: float | None
    market_value_aed: float | None
    attributes: dict[str, str]
    flood_depth_m: float | Unknown
    precision: str
    flood_covered: bool | None
    sum_insured_aed: float | None
    flood_deductible_aed: float | None
    facility_exposures: list[dict[str, Any]] = Field(default_factory=list)  # {facility_id, borrower, sector, allocated_outstanding}


class AssetResult(BaseModel):
    asset_id: str
    depth_above_floor_m: float | Unknown
    damage_fraction_building: Value
    damage_fraction_equipment: Value
    physical_damage_building_aed: Value
    physical_damage_equipment_aed: Value
    physical_damage_stock_aed: Value
    physical_damage_total_aed: Value
    interruption_days: Value
    interruption_cost_aed: Value
    insured_loss_aed: Value
    uninsured_physical_damage_aed: Value
    collateral_value_sensitivity_aed: Value
    outstanding_allocated_aed: float
    expected_annual_loss_aed: Value
    status: Literal["computed", "partial", "unknown"]
    provenance: Provenance


def assess_asset(inp: AssetInputs, scenario: dict[str, Any], dataset_versions: dict[str, str]) -> AssetResult:
    assumptions = [
        f"Daily interruption cost assumed at {DAILY_BI_RATE:.2%} of (replacement + equipment + stock) value; replace with borrower financials when available.",
        "Damage functions are illustrative and not validated against observed UAE losses.",
        "Collateral sensitivity = market value x building damage fraction; it is NOT a credit loss estimate.",
    ]
    prov = Provenance(dataset_versions={**dataset_versions, **vuln.versions()}, engine_version=ENGINE_VERSION, scenario=scenario, spatial_precision=inp.precision, assumptions=assumptions)  # type: ignore[arg-type]
    unresolved = isinstance(inp.flood_depth_m, Unknown)
    outstanding = round(sum(f["allocated_outstanding"] for f in inp.facility_exposures), 2)
    if unresolved:
        u = inp.flood_depth_m  # type: ignore[assignment]
        return AssetResult(asset_id=inp.asset_id, depth_above_floor_m=u, damage_fraction_building=u, damage_fraction_equipment=u, physical_damage_building_aed=u, physical_damage_equipment_aed=u, physical_damage_stock_aed=u, physical_damage_total_aed=u, interruption_days=u, interruption_cost_aed=u, insured_loss_aed=u, uninsured_physical_damage_aed=u, collateral_value_sensitivity_aed=u, outstanding_allocated_aed=outstanding, expected_annual_loss_aed=Unknown(reason="no event-frequency model registered"), status="unknown", provenance=prov)

    elev = float(inp.attributes.get("ground_floor_elevation_m", 0.0) or 0.0)
    if "ground_floor_elevation_m" not in inp.attributes:
        prov.assumptions.append("Ground floor elevation unknown; assumed 0.0 m (conservative).")
    depth = round(max(float(inp.flood_depth_m) - elev, 0.0), 3)

    f_b = vuln.damage_fraction(vuln.function_for(inp.asset_type), depth, inp.attributes)
    f_e = vuln.damage_fraction("vuln:plant_equipment_uae_demo", depth, inp.attributes)
    f_s = vuln.damage_fraction("vuln:stock_generic_demo", depth, inp.attributes)
    d_b = mul(inp.replacement_value_aed, f_b, "replacement value not extracted")
    d_e = mul(inp.equipment_value_aed, f_e, "equipment value not extracted") if inp.equipment_value_aed is not None else 0.0
    d_s = mul(inp.stock_value_aed, f_s) if inp.stock_value_aed is not None else 0.0
    total = add(d_b, d_e, d_s)

    days = vuln.interruption_days(depth, inp.attributes)
    base_value = (inp.replacement_value_aed or 0) + (inp.equipment_value_aed or 0) + (inp.stock_value_aed or 0)
    bi_cost = mul(base_value * DAILY_BI_RATE, days) if base_value else Unknown(reason="no value base for interruption cost")

    if inp.flood_covered is None:
        insured: Value = Unknown(reason="flood cover status not evidenced", reason_ar="حالة تغطية الفيضان غير مثبتة")
    elif not inp.flood_covered:
        insured = 0.0
        prov.assumptions.append("Policy excludes flood: insured loss is nil by policy terms, not by low hazard.")
    else:
        insured = apply_terms(total, inp.flood_deductible_aed, inp.sum_insured_aed)
    gap = _gap(total, insured, inp.flood_deductible_aed, inp.sum_insured_aed)
    coll = mul(inp.market_value_aed, f_b, "market value not extracted")

    range_present = any(isinstance(v, Range) for v in (total, bi_cost, insured))
    if range_present:
        drv = next(v.driver for v in (total, bi_cost, insured) if isinstance(v, Range))
        prov.uncertainty = {"driver": drv, "note": f"result is a range because '{drv}' is unknown"}
    status: Literal["computed", "partial"] = "partial" if range_present or isinstance(insured, Unknown) else "computed"
    return AssetResult(asset_id=inp.asset_id, depth_above_floor_m=depth, damage_fraction_building=f_b, damage_fraction_equipment=f_e, physical_damage_building_aed=d_b, physical_damage_equipment_aed=d_e, physical_damage_stock_aed=d_s, physical_damage_total_aed=total, interruption_days=days, interruption_cost_aed=bi_cost, insured_loss_aed=insured, uninsured_physical_damage_aed=gap, collateral_value_sensitivity_aed=coll, outstanding_allocated_aed=outstanding, expected_annual_loss_aed=Unknown(reason="no event-frequency model registered; EAL cannot be inferred from one scenario", reason_ar="لا يوجد نموذج لتكرار الأحداث؛ لا يمكن استنتاج الخسارة السنوية المتوقعة من سيناريو واحد"), status=status, provenance=prov)


def _gap(total: Value, insured: Value, deductible: float | None, limit: float | None) -> Value:
    """Uninsured share = total - insured, evaluated bound-by-bound so ranges stay coherent."""
    if isinstance(total, Unknown):
        return total
    if isinstance(insured, Unknown):
        return Unknown(reason=f"uninsured share unknown: {insured.reason}")
    if _is_num(insured) and insured == 0.0:
        return total
    def one(x: float) -> float:
        return round(x - float(apply_terms(x, deductible, limit)), 2)  # type: ignore[arg-type]
    if isinstance(total, Range):
        return Range(low=one(total.low), high=one(total.high), driver=total.driver)
    return one(total)


def value_to_json(v: Value) -> Any:
    if isinstance(v, Unknown):
        return {"unknown": True, "reason": v.reason, "reason_ar": v.reason_ar}
    if isinstance(v, Range):
        return {"low": v.low, "high": v.high, "driver": v.driver}
    return v
