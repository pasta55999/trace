from __future__ import annotations

from typing import Any

from agents.runtime import Agent


class EvidenceGapAgent(Agent):
    """Finds the unknown attribute that moves the result most and asks one targeted question."""

    name = "evidence_gap"

    def run(self, run: dict[str, Any], open_questions: list[dict[str, Any]]) -> dict[str, Any]:
        asked_keys = {(q["asset_id"], q["kind"]) for q in open_questions}
        ranked = []
        for a in run["assets"]:
            v = a["physical_damage_total_aed"]
            if isinstance(v, dict) and "low" in v:
                for drv in v["driver"].split(","):
                    if (a["asset_id"], drv) not in asked_keys:
                        ranked.append({"asset_id": a["asset_id"], "attribute": drv, "spread": v["high"] - v["low"], "low": v["low"], "high": v["high"], "desc": a["description"], "borrower": a["borrower"]})
        ranked.sort(key=lambda r: r["spread"], reverse=True)
        asked = []
        templates = self.genome.param("question_templates", {})
        for r in ranked[: self.genome.param("max_questions_per_round", 1)]:
            t = templates.get(r["attribute"], {"en": "For {asset}: what is '" + r["attribute"] + "'? Spread {low:,.0f}-{high:,.0f} AED.", "ar": "بالنسبة إلى {asset}: ما قيمة '" + r["attribute"] + "'؟ المدى {low:,.0f}-{high:,.0f} درهم."})
            label = f"{r['desc']} ({r['asset_id']}, {r['borrower']})"
            q = self.tool("create_question", asset_id=r["asset_id"], kind=r["attribute"], created_by=self.actor, question_en=t["en"].format(asset=label, low=r["low"], high=r["high"]), question_ar=t["ar"].format(asset=label, low=r["low"], high=r["high"]), evidence=[f"result://{r['asset_id']}"])
            self.decide(r["asset_id"], "asked", attribute=r["attribute"], spread=r["spread"])
            asked.append(q)
        return {"ranked": ranked, "asked": asked}
