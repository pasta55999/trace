from __future__ import annotations

from typing import Any

from agents.runtime import Agent


class ResolutionAgent(Agent):
    """Entity + location resolution. Deterministic candidates come from the location service;
    the *decision* (commit / district screening / ask) is governed by this agent's genome and
    is therefore the main target of the evolution loop."""

    name = "resolution"

    def decide_asset(self, asset: dict[str, Any]) -> dict[str, Any]:
        g = self.genome
        cands = self.tool("geocode_candidates", asset_id=asset["id"], aliases=g.param("aliases", {}), fuzzy_cutoff=g.param("fuzzy_cutoff", 0.82))
        usable = [c for c in cands if not (g.param("never_use_office_as_site", True) and c.get("kind") == "office")]
        best = usable[0] if usable else None
        min_conf = g.param("min_confidence", 0.85)
        footprints = [c for c in usable if c["precision"] in ("footprint", "parcel")]
        ambiguous = len(footprints) > 1 and footprints[0]["confidence"] - footprints[1]["confidence"] < g.param("ambiguity_margin", 0.02) and footprints[0]["feature_id"] != footprints[1]["feature_id"]
        if ambiguous and best and best["confidence"] >= min_conf and best["method"].startswith("name:fuzzy"):
            return {"action": "ask", "candidate": None, "candidates": usable, "reason": f"ambiguous: {footprints[0]['feature_id']} vs {footprints[1]['feature_id']} within margin"}
        if best and best["precision"] in ("footprint", "parcel") and best["confidence"] >= min_conf:
            return {"action": "commit", "candidate": best, "candidates": usable, "reason": f"{best['method']} confidence {best['confidence']:.2f} >= {min_conf}"}
        district = next((c for c in usable if c["precision"] == "district"), None)
        if district and g.param("accept_district_as_screening", True) and not any(c["precision"] in ("footprint", "parcel") and c["confidence"] > 0 for c in usable):
            return {"action": "commit_district", "candidate": district, "candidates": usable, "reason": "district-level screening only; building-level hazard will be refused"}
        return {"action": "ask", "candidate": None, "candidates": usable, "reason": "no candidate above threshold" if not best else f"best {best['method']} confidence {best['confidence']:.2f} < {min_conf}"}

    def run(self) -> dict[str, Any]:
        out = []
        for asset in self.tool("list_assets"):
            if asset.get("location_id"):
                continue
            d = self.decide_asset(asset)
            self.decide(asset["id"], d["action"], reason=d["reason"], top=[(c["feature_id"], c["confidence"]) for c in d["candidates"][:3]])
            if d["action"] in ("commit", "commit_district"):
                loc = self.tool("commit_location", asset_id=asset["id"], candidate=d["candidate"], reason=d["reason"], actor=self.actor)
            else:
                loc = self.tool("commit_location", asset_id=asset["id"], candidate=None, reason=d["reason"], actor=self.actor)
                top = d["candidates"][:3]
                opts_en = "; ".join(f"{c['label']} [{c['precision']}, {c['method']}]" for c in top) or "no candidates"
                opts_ar = "؛ ".join(f"{c['label']} [{c['precision']}]" for c in top) or "لا يوجد مرشحون"
                self.tool("create_question", asset_id=asset["id"], kind="location", created_by=self.actor,
                          question_en=f"Where is {asset['description']} ({asset['id']})? Recorded address: '{asset['recorded_address']}'. Candidates: {opts_en}. Confirm one or provide a plot reference.",
                          question_ar=f"أين يقع {asset['description']} ({asset['id']})؟ العنوان المسجل: '{asset['recorded_address']}'. المرشحون: {opts_ar}. أكد أحدها أو قدم رقم القطعة.",
                          candidates=top, evidence=[f"asset://{asset['id']}/recorded_address"])
            out.append({"asset_id": asset["id"], **{k: d[k] for k in ("action", "reason")}, "precision": loc["precision"]})
        return {"resolutions": out}
