"""Promoter: shadow -> canary -> full. Selects the best verified candidate and moves the pointer.

Prototype staging: 'shadow' replays the corrections that triggered the hypothesis against the
candidate (must reproduce the human's choice); 'canary' is a pointer promotion recorded with
state=canary; the Guardian upgrades to 'full' or rolls back based on live SLIs.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from agents.runtime import MockProvider, Runtime
from agents.specialists.resolution import ResolutionAgent
from agents.tools import register_tools
from evolution.genome import GenomeRegistry
from evolution.telemetry import Telemetry
from services.register import PhysicalAsset, Store


class Promoter:
    actor = "evolver:promoter"

    def __init__(self, registry: GenomeRegistry, telemetry: Telemetry):
        self.registry, self.telemetry = registry, telemetry

    def shadow(self, agent: str, candidate: Path, evidence: list[dict[str, Any]]) -> bool:
        if agent != "resolution":
            return True
        import tempfile

        tmp = Path(tempfile.mkdtemp(prefix="trace-shadow-"))
        rt = Runtime(registry=self.registry, telemetry=Telemetry(tmp / "t.jsonl"), provider=MockProvider())
        store = Store(tenant_id="shadow", path=tmp / "s.json")
        register_tools(rt, store)
        a = ResolutionAgent(rt, self.registry.load(agent, path=candidate))
        for e in evidence:
            if not e.get("query"):
                continue
            asset = PhysicalAsset(id=e["subject"], description=e.get("description") or "", asset_type="warehouse", recorded_address=e["query"])
            store.s.assets[asset.id] = asset
            d = a.decide_asset(asset.model_dump())
            if not (d["action"] == "commit" and d["candidate"]["feature_id"] == e["chosen_feature"]):
                return False
        return True

    def select_and_promote(self, agent: str, verdicts: list[dict[str, Any]], candidates: dict[str, Path], evidence: list[dict[str, Any]], stage: str = "canary") -> dict[str, Any]:
        passing = [v for v in verdicts if v["pass"]]
        rejected = [v for v in verdicts if not v["pass"]]
        for v in rejected:
            shutil.rmtree(candidates[v["candidate"]], ignore_errors=True)
        if not passing:
            return {"promoted": None, "rejected": [(v["candidate"], v["reasons"]) for v in rejected]}
        # best score first; ties broken by the narrowest change (fewest parameters touched)
        passing.sort(key=lambda v: (-v["candidate_score"]["overall"], len(v["candidate_score"].get("changed_params", []))))
        for v in passing:
            path = candidates[v["candidate"]]
            if not self.shadow(agent, path, evidence):
                v["reasons"].append("shadow replay did not reproduce the human correction")
                rejected.append(v)
                shutil.rmtree(path, ignore_errors=True)
                continue
            version = self.registry.promote(agent, path, v["candidate_score"], state=stage)
            self.telemetry.emit("promotion", "promoter", target_agent=agent, version=version, stage=stage, overall=v["candidate_score"]["overall"], change_record=self.registry.load(agent, version).manifest.get("change_record"))
            for other in passing:
                if other is not v:
                    shutil.rmtree(candidates[other["candidate"]], ignore_errors=True)
            return {"promoted": version, "stage": stage, "score": v["candidate_score"]["overall"], "change_record": self.registry.load(agent, version).manifest.get("change_record"), "rejected": [(r["candidate"], r["reasons"]) for r in rejected], "also_passed_not_selected": [o["candidate"] for o in passing if o is not v]}
        return {"promoted": None, "rejected": [(v["candidate"], v["reasons"]) for v in rejected]}
