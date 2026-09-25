"""Verifier: scores a candidate genome in an isolated sandbox against the active genome.

Pass criteria: no hard fail (adversarial false commit / invariant breach), no regression in
overall score vs active, and every regression case derived from corrections must now pass.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from evolution.evals.scorecard import scorecard
from evolution.genome import GenomeRegistry
from evolution.telemetry import Telemetry


class Verifier:
    actor = "evolver:verifier"

    def __init__(self, registry: GenomeRegistry, telemetry: Telemetry):
        self.registry, self.telemetry = registry, telemetry

    def verify(self, agent: str, candidate: Path) -> dict[str, Any]:
        active = scorecard(self.registry, agent, version=self.registry.active_version(agent))
        cand = scorecard(self.registry, agent, genome_path=candidate)
        reasons = []
        if cand["hard_fail"]:
            reasons.append("hard fail: " + ("adversarial false commit" if any(s.get("false_commits") for s in cand["suites"].values()) else cand.get("invariants_detail", "invariant breach")))
        if cand["overall"] < active["overall"] - 1e-9:
            reasons.append(f"regression: overall {cand['overall']} < active {active['overall']}")
        reg = cand["suites"].get("regression")
        if reg and reg["score"] is not None and reg["score"] < 1.0:
            reasons.append(f"regression suite not fully passed ({reg['score']})")
        verdict = {"candidate": candidate.name, "pass": not reasons, "reasons": reasons, "candidate_score": cand, "active_score": {"genome": active["genome"], "overall": active["overall"]}}
        self.telemetry.emit("verification", "verifier", candidate=candidate.name, target_agent=agent, passed=verdict["pass"], reasons=reasons, overall=cand["overall"], active_overall=active["overall"])
        return verdict
