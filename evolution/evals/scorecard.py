"""Eval harness. One entry point produces the manifest `eval` block for a genome path.

Suites: golden (human-owned), regression (grown from production corrections), adversarial
(human-owned; any false commit is a hard fail), invariants (policy checks on the genome).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents.runtime import MockProvider, Runtime
from agents.specialists.resolution import ResolutionAgent
from agents.tools import register_tools
from evolution.genome import GenomeRegistry
from evolution.policy import PolicyViolation, check_param_bounds
from evolution.telemetry import Telemetry
from services.common import ROOT
from services.register import PhysicalAsset, Store

EVALS = ROOT / "evolution" / "evals"


def _cases(suite: str, agent: str) -> list[dict[str, Any]]:
    p = EVALS / suite / f"{agent}.json"
    return json.loads(p.read_text(encoding="utf-8"))["cases"] if p.exists() else []


def _sandbox_runtime(registry: GenomeRegistry) -> tuple[Runtime, Store]:
    """Isolated runtime: mock provider, throwaway telemetry, empty store. No tenant data."""
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="trace-verifier-"))
    rt = Runtime(registry=registry, telemetry=Telemetry(tmp / "telemetry.jsonl"), provider=MockProvider())
    store = Store(tenant_id="sandbox", path=tmp / "sandbox.json")
    register_tools(rt, store)
    return rt, store


def _judge(decision: dict[str, Any], expected: dict[str, Any]) -> tuple[float, str]:
    act = decision["action"]
    chosen = decision["candidate"]["feature_id"] if decision["candidate"] else None
    if chosen and chosen in expected.get("must_not", []):
        return 0.0, "false_commit"
    exp = expected["action"]
    if exp == "commit":
        if act == "commit" and chosen == expected["feature_id"]:
            return 1.0, "ok"
        if act == "commit":
            return 0.0, "false_commit"
        return 0.5, "safe_miss"  # asked instead of committing; recoverable
    if exp == "ask":
        return (1.0, "ok") if act == "ask" else (0.0, "false_commit" if act == "commit" else "district_instead_of_ask")
    if exp == "district":
        return (1.0, "ok") if act == "commit_district" else (0.5, "safe_miss") if act == "ask" else (0.0, "false_commit")
    if exp == "ask_or_district":
        return (1.0, "ok") if act in ("ask", "commit_district") else (0.0, "false_commit")
    return 0.0, "unknown_expectation"


def score_resolution(registry: GenomeRegistry, genome_path: Path | None = None, version: str | None = None) -> dict[str, Any]:
    rt, store = _sandbox_runtime(registry)
    genome = registry.load("resolution", version=version, path=genome_path)
    agent = ResolutionAgent(rt, genome)
    suites: dict[str, Any] = {}
    hard_fail = False
    for suite in ("golden", "regression", "adversarial"):
        cases = _cases(suite, "resolution")
        results = []
        for c in cases:
            asset = PhysicalAsset(**c["asset"])
            store.s.assets[asset.id] = asset
            d = agent.decide_asset(asset.model_dump())
            s, verdict = _judge(d, c["expected"])
            results.append({"id": c["id"], "score": s, "verdict": verdict, "action": d["action"], "chosen": d["candidate"]["feature_id"] if d["candidate"] else None})
            if suite == "adversarial" and verdict == "false_commit":
                hard_fail = True
        suites[suite] = {"n": len(cases), "score": round(sum(r["score"] for r in results) / len(cases), 4) if cases else None, "false_commits": sum(r["verdict"] == "false_commit" for r in results), "results": results}
    invariants_ok, inv_detail = True, ""
    try:
        check_param_bounds(genome.routing)
    except PolicyViolation as e:
        invariants_ok, inv_detail = False, str(e)
    overall = sum(v["score"] for v in suites.values() if v["score"] is not None) / max(1, sum(1 for v in suites.values() if v["score"] is not None))
    return {"agent": "resolution", "genome": genome.version, "suites": suites, "invariants_ok": invariants_ok, "invariants_detail": inv_detail, "hard_fail": hard_fail or not invariants_ok, "overall": round(overall, 4), "changed_params": genome.manifest.get("changed_params", [])}


def scorecard(registry: GenomeRegistry, agent: str, genome_path: Path | None = None, version: str | None = None) -> dict[str, Any]:
    if agent == "resolution":
        return score_resolution(registry, genome_path, version)
    return {"agent": agent, "suites": {}, "hard_fail": False, "overall": 1.0, "note": "no eval suite yet for this agent"}


if __name__ == "__main__":
    import sys

    reg = GenomeRegistry()
    print(json.dumps(scorecard(reg, sys.argv[1] if len(sys.argv) > 1 else "resolution"), indent=1, ensure_ascii=False))
