"""Guardian: always-on SLO watch, auto-rollback, kill switch, freeze. NOT evolvable.

Runs under a separate identity. It never reads documents or tenant records - only SLIs.
"""
from __future__ import annotations

import json
from typing import Any

from evolution.genome import GenomeRegistry
from evolution.telemetry import Telemetry

SLO = {"max_override_rate": 0.34, "min_decisions_for_judgement": 3, "max_policy_blocks": 3, "consecutive_rollbacks_to_freeze": 3}


class Guardian:
    actor = "evolver:guardian"

    def __init__(self, registry: GenomeRegistry, telemetry: Telemetry):
        self.registry, self.telemetry = registry, telemetry

    def kill_switch(self, agent: str) -> bool:
        return (self.registry.root / f"KILL_{agent}").exists()

    def check(self, agent: str) -> dict[str, Any]:
        version = self.registry.active_version(agent)
        manifest = self.registry.load(agent, version).manifest
        sli = self.telemetry.sli(agent, version)
        action = "none"
        if self.kill_switch(agent):
            action = "kill_switch_active"
        elif manifest.get("promotion_state") in ("canary", "full") and manifest.get("parent"):
            breach = (sli["decisions"] >= SLO["min_decisions_for_judgement"] and sli["override_rate"] > SLO["max_override_rate"]) or sli["policy_blocks"] > SLO["max_policy_blocks"]
            if breach:
                parent = self.registry.rollback(agent, f"SLO breach: {sli}")
                action = f"rolled_back_to_{parent}"
                self.telemetry.emit("rollback", "guardian", target_agent=agent, from_version=version, to_version=parent, sli=sli)
                if self._consecutive_rollbacks(agent) >= SLO["consecutive_rollbacks_to_freeze"]:
                    self.registry.freeze(f"{agent}: {SLO['consecutive_rollbacks_to_freeze']} consecutive rollbacks")
                    action += "+frozen"
            elif manifest.get("promotion_state") == "canary" and sli["decisions"] >= SLO["min_decisions_for_judgement"]:
                manifest["promotion_state"] = "full"
                (self.registry.agent_dir(agent) / version / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
                action = "canary_promoted_to_full"
                self.telemetry.emit("promotion", "guardian", target_agent=agent, version=version, stage="full", sli=sli)
        return {"agent": agent, "version": version, "state": manifest.get("promotion_state"), "sli": sli, "slo": SLO, "action": action, "frozen": self.registry.is_frozen()}

    def _consecutive_rollbacks(self, agent: str) -> int:
        n = 0
        for e in reversed(self.telemetry.events(agent=None)):
            if e["kind"] == "rollback" and e.get("target_agent") == agent:
                n += 1
            elif e["kind"] == "promotion" and e.get("target_agent") == agent and e.get("stage") == "full":
                break
        return n
