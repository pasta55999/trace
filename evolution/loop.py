"""One evolution cycle: Reflector -> Proposer -> Verifier -> Promoter, then Guardian.

Scheduled nightly in production and triggered on failure clusters; callable on demand here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from agents.runtime import Runtime
from evolution.evolvers.guardian import Guardian
from evolution.evolvers.promoter import Promoter
from evolution.evolvers.proposer import ProposerAgent
from evolution.evolvers.reflector import ReflectorAgent
from evolution.evolvers.verifier import Verifier


def run_cycle(rt: Runtime) -> dict[str, Any]:
    reg, tel = rt.registry, rt.telemetry
    guardian = Guardian(reg, tel)
    if reg.is_frozen():
        return {"skipped": "evolution frozen by guardian", "guardian": [guardian.check(a) for a in ("resolution",)]}
    hypotheses = ReflectorAgent(rt).run()
    proposed = ProposerAgent(rt).run(hypotheses)
    verifier, promoter = Verifier(reg, tel), Promoter(reg, tel)
    outcomes = []
    by_agent: dict[str, list[Path]] = {}
    for c in proposed["candidates"]:
        p = Path(c)
        by_agent.setdefault(p.parent.parent.name, []).append(p)
    for agent, cands in by_agent.items():
        if guardian.kill_switch(agent):
            outcomes.append({"agent": agent, "skipped": "kill switch"})
            continue
        verdicts = [verifier.verify(agent, c) for c in cands]
        summaries = [{"candidate": v["candidate"], "pass": v["pass"], "reasons": v["reasons"], "overall": v["candidate_score"]["overall"], "change": reg_change(cands, v["candidate"])} for v in verdicts]
        evidence = [e for h in hypotheses if h["agent"] == agent for e in h["evidence"]]
        result = promoter.select_and_promote(agent, verdicts, {c.name: c for c in cands}, evidence)
        outcomes.append({"agent": agent, "verdicts": summaries, **result})
    # mark corrections consumed so the same cluster is not re-proposed forever
    _consume_corrections(tel)
    return {"hypotheses": hypotheses, "proposals": proposed["proposals"], "outcomes": outcomes, "guardian": [guardian.check(a) for a in ("resolution",)], "history": {a: reg.history(a) for a in ("resolution",)}}


def reg_change(cands: list[Path], name: str) -> str | None:
    import json

    for c in cands:
        if c.name == name and (c / "manifest.json").exists():
            return json.loads((c / "manifest.json").read_text(encoding="utf-8")).get("change_record")
    return None


def _consume_corrections(tel: Any) -> None:
    import json

    if not tel.path.exists():
        return
    lines = []
    for line in tel.path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        ev = json.loads(line)
        if ev["kind"] == "human_correction":
            ev["consumed"] = True
        lines.append(json.dumps(ev, ensure_ascii=False, default=str))
    tel.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
