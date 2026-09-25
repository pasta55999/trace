from __future__ import annotations

import re
from typing import Any

from agents.runtime import Agent
from evolution.policy import PolicyViolation, validate_result_tree
from services import reporting


class CriticAgent(Agent):
    """Adversarial second reader for anything user-facing."""

    name = "critic"

    def verify_brief(self, tree: dict[str, Any], html_en: str, html_ar: str) -> dict[str, Any]:
        findings: list[str] = []
        try:
            validate_result_tree(tree["run"])
        except PolicyViolation as e:
            findings.append(str(e))
        for phrase in self.genome.param("forbidden_phrases", []):
            if phrase in html_en.lower():
                findings.append(f"forbidden phrase: {phrase}")
        if self.genome.param("require_parity", True) and not reporting.numeric_parity(tree):
            findings.append("ar/en numeric parity mismatch")
        for a in tree["run"]["assets"]:
            if a["status"] == "unknown" and re.search(rf"{a['asset_id']}.{{0,400}}>0<", html_en, re.S):
                findings.append(f"{a['asset_id']} unknown rendered as 0")
        if "not modelled" not in html_en:
            findings.append("credit-loss column must state 'not modelled'")
        ok = not findings
        self.decide("brief", "pass" if ok else "fail", findings=findings)
        return {"ok": ok, "findings": findings}
