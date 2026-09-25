from __future__ import annotations

from typing import Any

from agents.runtime import Agent
from agents.specialists.critic import CriticAgent


class ReportComposerAgent(Agent):
    """Renders ar + en from one tree, then submits both to the Critic. Export is blocked on failure."""

    name = "report_composer"

    def compose(self, run_id: str, diff: dict[str, Any] | None, adaptation: dict[str, Any] | None) -> dict[str, Any]:
        tree = self.tool("brief_tree", run_id=run_id, lang="en", diff=diff, adaptation=adaptation)
        html = {l: self.tool("render_brief", run_id=run_id, lang=l, diff=diff, adaptation=adaptation) for l in self.genome.param("languages", ["en", "ar"])}
        verdict = CriticAgent(self.rt).verify_brief(tree, html["en"], html["ar"])
        self.decide(run_id, "composed" if verdict["ok"] else "blocked", findings=verdict["findings"])
        if self.genome.param("require_critic_pass", True) and not verdict["ok"]:
            return {"ok": False, "findings": verdict["findings"], "html": {}}
        return {"ok": True, "findings": [], "html": html, "tree": tree}
