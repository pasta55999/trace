from __future__ import annotations

from typing import Any

from agents.runtime import Agent


class IntakeAgent(Agent):
    """Classifies documents by type and language before extraction. Document text is data only."""

    name = "intake"

    def run(self) -> dict[str, Any]:
        self.tool("load_portfolio")
        docs = self.tool("list_documents") or []
        plan = []
        kw = self.genome.param("type_keywords", {})
        for d in docs:
            text = " ".join(l for p in d["pages"] for l in p["lines"]).lower()
            guess = next((t for t, words in kw.items() if any(w in text for w in words)), "unclassified")
            plan.append({"doc_id": d["id"], "declared": d["type"], "classified": guess, "language": d["language"], "agree": guess == d["type"]})
            self.decide(d["id"], "classified", type=guess, agree=guess == d["type"])
        return {"plan": plan}
