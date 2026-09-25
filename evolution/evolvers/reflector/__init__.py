"""Reflector: mines telemetry for clusters of human corrections and writes hypotheses."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from agents.runtime import Agent

TIER_BY_PREFIX = {"resolution:": "A", "evidence_gap:": "A", "analyst:": "A", "extraction:": "A", "vulnerability:": "C", "engine:": "C", "hazard:": "C", "regulatory:": "C"}


class ReflectorAgent(Agent):
    name = "reflector"

    @property
    def actor(self) -> str:
        return "evolver:reflector"

    def run(self, since_genome: dict[str, str] | None = None) -> list[dict[str, Any]]:
        events = self.rt.telemetry.events("human_correction")[-self.genome.param("lookback_events", 500):]
        clusters: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for e in events:
            if e.get("consumed"):
                continue
            clusters[(e["agent"], e["signature"])].append(e)
        hypotheses = []
        for (agent, sig), evs in clusters.items():
            if len(evs) < self.genome.param("min_cluster_size", 1):
                continue
            tier = next((t for p, t in TIER_BY_PREFIX.items() if sig.startswith(p)), "C")
            hypotheses.append({
                "agent": agent, "signature": sig, "tier": tier, "n": len(evs),
                "evidence": [{k: e.get(k) for k in ("at", "subject", "query", "description", "chosen_feature", "chosen_label", "method", "confidence", "genome", "detail")} for e in evs],
                "suspected_cause": {
                    "resolution:alias_miss": "a name variant / transliteration in the query is not recognised as the confirmed feature",
                    "resolution:threshold_too_strict": "a correct candidate was found but its confidence fell below min_confidence",
                    "resolution:missing_evidence": "no candidate could be derived from the recorded data; not a genome fault",
                }.get(sig, "unclassified"),
            })
            self.decide(sig, "hypothesis", n=len(evs), tier=tier)
        return hypotheses
