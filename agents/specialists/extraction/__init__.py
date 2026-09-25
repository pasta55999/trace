from __future__ import annotations

from typing import Any

from agents.runtime import Agent


class ExtractionAgent(Agent):
    """Drives extraction, reports quarantined lines, and flags cross-document conflicts."""

    name = "extraction"

    def run(self) -> dict[str, Any]:
        summary = self.tool("load_documents")
        docs = self.tool("list_documents")
        quarantined = [{"doc_id": d["id"], "flags": d["firewall_flags"]} for d in docs if d["firewall_flags"]]
        low = [(d["id"], f["field"], f["confidence"]) for d in docs for f in d["fields"] if not f["flagged_instruction"] and f["confidence"] < self.genome.param("min_field_confidence", 0.6)]
        # conflicts: same collateral, same field, materially different values
        seen: dict[tuple[str, str], tuple[str, Any]] = {}
        conflicts = []
        tol = self.genome.param("conflict_tolerance_pct", 2.0) / 100
        for d in docs:
            for f in d["fields"]:
                if f["flagged_instruction"] or not isinstance(f["value"], (int, float)):
                    continue
                k = (d["related_collateral"], f["field"])
                if k in seen and seen[k][0] != d["id"] and abs(seen[k][1] - f["value"]) > tol * max(abs(f["value"]), 1):
                    conflicts.append({"asset_id": k[0], "field": k[1], "docs": [seen[k][0], d["id"]], "values": [seen[k][1], f["value"]]})
                seen.setdefault(k, (d["id"], f["value"]))
        for q in quarantined:
            self.decide(q["doc_id"], "quarantined_instruction_text", flags=q["flags"])
        return {**summary, "quarantined": quarantined, "low_confidence_fields": low, "conflicts": conflicts}
