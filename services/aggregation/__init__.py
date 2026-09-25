"""Scenario runner and portfolio aggregation / concentration.

Concentration is computed from event co-occurrence (assets inside the same event footprint),
not by summing independently computed worst cases.
"""
from __future__ import annotations

from typing import Any

from services import hazard
from services.common import Range, Unknown, new_id, now_iso
from services.fin_engine import AssetInputs, AssetResult, Value, add, assess_asset, value_to_json
from services.register import PhysicalAsset, Store

DEFAULT_SCENARIO = {
    "id": "scn:flood_rp100_2050_ssp245_illustrative",
    "label_en": "ILLUSTRATIVE pluvial flood, 1-in-100, 2050, SSP2-4.5",
    "label_ar": "فيضان سطحي توضيحي، 1 في 100، 2050، SSP2-4.5",
    "hazard": "flood_depth",
    "pathway": "SSP2-4.5",
    "horizon": 2050,
    "return_period": 100,
    "illustrative": True,
}


def _inputs(store: Store, a: PhysicalAsset, overrides: dict[str, Any]) -> AssetInputs:
    loc = store.location_of(a.id)
    prec = loc.precision if loc else "unresolved"
    sample = hazard.sample_flood(loc.lon if loc else None, loc.lat if loc else None, loc.footprint if loc else None, prec)
    depth: float | Unknown = sample.value
    attrs = dict(a.attributes)
    ov = overrides.get(a.id, {})
    if isinstance(depth, float) and "reduce_depth_m" in ov:
        depth = round(max(depth - ov["reduce_depth_m"], 0.0), 3)
    attrs.update(ov.get("attributes", {}))
    ins = store.insurance_of(a.id)
    exposures = []
    for f in store.facilities_for_asset(a.id):
        b = store.s.borrowers[f.borrower_id]
        exposures.append({"facility_id": f.id, "borrower_id": b.id, "borrower": b.name_en, "borrower_ar": b.name_ar, "sector": b.sector, "maturity_year": f.maturity_year, "allocated_outstanding": round(f.outstanding_aed * store.allocation(f.id, a.id), 2)})
    return AssetInputs(asset_id=a.id, asset_type=a.asset_type, replacement_value_aed=a.replacement_value_aed, equipment_value_aed=a.equipment_value_aed, stock_value_aed=a.stock_value_aed, market_value_aed=a.market_value_aed, attributes=attrs, flood_depth_m=depth, precision=prec, flood_covered=ins.flood_covered if ins else None, sum_insured_aed=ins.sum_insured_aed if ins else None, flood_deductible_aed=ins.flood_deductible_aed if ins else None, facility_exposures=exposures)


def run_scenario(store: Store, scenario: dict[str, Any] | None = None, overrides: dict[str, Any] | None = None, label: str = "baseline", actor: str = "service:aggregation") -> dict[str, Any]:
    scenario = scenario or DEFAULT_SCENARIO
    overrides = overrides or {}
    versions = hazard.dataset_versions()
    results: list[tuple[AssetInputs, AssetResult]] = []
    for a in store.s.assets.values():
        inp = _inputs(store, a, overrides)
        results.append((inp, assess_asset(inp, scenario, versions)))
    run = {
        "run_id": new_id("RUN"),
        "label": label,
        "scenario": scenario,
        "created_at": now_iso(),
        "overrides": overrides,
        "assets": [_asset_row(store, inp, r) for inp, r in results],
        "aggregation": aggregate(store, results),
    }
    store.s.runs[run["run_id"]] = run
    store.audit(actor, "scenario_run", run_id=run["run_id"], label=label, scenario=scenario["id"])
    return run


def _asset_row(store: Store, inp: AssetInputs, r: AssetResult) -> dict[str, Any]:
    a = store.s.assets[r.asset_id]
    b = store.borrower_for_asset(r.asset_id)
    d = r.model_dump()
    for k in ("depth_above_floor_m", "damage_fraction_building", "damage_fraction_equipment", "physical_damage_building_aed", "physical_damage_equipment_aed", "physical_damage_stock_aed", "physical_damage_total_aed", "interruption_days", "interruption_cost_aed", "insured_loss_aed", "uninsured_physical_damage_aed", "collateral_value_sensitivity_aed", "expected_annual_loss_aed"):
        d[k] = value_to_json(getattr(r, k))
    d.update({"description": a.description, "asset_type": a.asset_type, "borrower": b.name_en if b else None, "borrower_ar": b.name_ar if b else None, "sector": b.sector if b else None, "precision": inp.precision, "flood_depth_m": value_to_json(inp.flood_depth_m), "attributes": inp.attributes, "facilities": inp.facility_exposures, "district_id": a.district_id, "ref": f"result://{r.asset_id}"})
    return d


def _sum(vals: list[Value]) -> Value:
    return add(*vals) if vals else 0.0


def aggregate(store: Store, results: list[tuple[AssetInputs, AssetResult]]) -> dict[str, Any]:
    total_outstanding = sum(f.outstanding_aed for f in store.s.facilities.values())
    in_event = [(i, r) for i, r in results if isinstance(i.flood_depth_m, float) and i.flood_depth_m > 0]
    unknown = [(i, r) for i, r in results if isinstance(i.flood_depth_m, Unknown)]
    borrowers = sorted({e["borrower"] for i, _ in in_event for e in i.facility_exposures})
    sectors = sorted({e["sector"] for i, _ in in_event for e in i.facility_exposures})
    concentration = {
        "event": "shared flood footprint",
        "assets_in_footprint": [i.asset_id for i, _ in in_event],
        "borrowers": borrowers,
        "sectors": sectors,
        "outstanding_in_footprint_aed": round(sum(r.outstanding_allocated_aed for _, r in in_event), 2),
        "share_of_portfolio_outstanding": round(sum(r.outstanding_allocated_aed for _, r in in_event) / total_outstanding, 4) if total_outstanding else 0,
        "physical_damage_total_aed": value_to_json(_sum([r.physical_damage_total_aed for _, r in in_event])),
        "insured_loss_total_aed": value_to_json(_sum([r.insured_loss_aed for _, r in in_event])),
        "interruption_cost_total_aed": value_to_json(_sum([r.interruption_cost_aed for _, r in in_event])),
        "note_en": "Loss totals are for one co-occurring event; they are not additive across scenarios. Credit loss is not computed.",
        "note_ar": "إجماليات الخسائر لحدث واحد متزامن؛ لا تُجمع عبر السيناريوهات. لم تُحتسب خسائر الائتمان.",
    }
    by_sector: dict[str, dict[str, Any]] = {}
    for i, r in results:
        for e in i.facility_exposures:
            g = by_sector.setdefault(e["sector"], {"outstanding_aed": 0.0, "assets": 0, "in_footprint": 0, "unknown": 0})
            g["outstanding_aed"] += e["allocated_outstanding"]
            g["assets"] += 1
            g["in_footprint"] += int((i, r) in in_event)
            g["unknown"] += int(isinstance(i.flood_depth_m, Unknown))
    return {
        "portfolio_outstanding_aed": total_outstanding,
        "concentration": concentration,
        "by_sector": by_sector,
        "unknown_assets": [{"asset_id": i.asset_id, "reason": i.flood_depth_m.reason, "reason_ar": i.flood_depth_m.reason_ar} for i, _ in unknown],  # type: ignore[union-attr]
        "diversification_warning_en": f"{len(sectors)} sectors appear diversified but {len(in_event)} assets share one physical vulnerability." if len(sectors) > 1 else "",
        "diversification_warning_ar": f"{len(sectors)} قطاعات تبدو متنوعة لكن {len(in_event)} أصول تشترك في نقطة ضعف مادية واحدة." if len(sectors) > 1 else "",
    }
