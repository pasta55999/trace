"""Proposer: turns hypotheses into candidate genomes (Tier A/B) or governance proposals (Tier C).

For each hypothesis it produces a small population of mutations, from narrowest to broadest,
and always adds a regression eval derived from the correction (Tier B path).
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path
from typing import Any

from agents.runtime import Agent
from evolution.policy import PolicyViolation, check_candidate_paths, relpath
from services import governance
from services.common import ROOT, has_arabic, normalise_arabic, normalise_digits
from services.location import gazetteer

REGRESSION = ROOT / "evolution" / "evals" / "regression" / "resolution.json"


def _norm(s: str) -> str:
    s = normalise_digits(s)
    s = normalise_arabic(s) if has_arabic(s) else s
    return re.sub(r"[^\w\s\-]", " ", s.lower()).strip()


def _best_alias_key(query: str, feature_id: str) -> tuple[str, str] | None:
    """The query n-gram most similar to the confirmed feature's names -> alias key; value = canonical en name."""
    f = next((x for x in gazetteer()["features"] if x["id"] == feature_id), None)
    if not f:
        return None
    words = _norm(query).split()
    grams = [" ".join(words[i : i + n]) for n in range(1, 5) for i in range(len(words) - n + 1)]
    names = [_norm(f["name_en"]), _norm(f["name_ar"])]
    best = max(((difflib.SequenceMatcher(None, n, g).ratio(), g) for n in names for g in grams), default=(0, ""))
    return (best[1], f["name_en"]) if best[0] >= 0.6 else None


class ProposerAgent(Agent):
    name = "proposer"

    @property
    def actor(self) -> str:
        return "evolver:proposer"

    def run(self, hypotheses: list[dict[str, Any]]) -> dict[str, Any]:
        candidates: list[Path] = []
        proposals: list[dict[str, Any]] = []
        for h in hypotheses:
            if h["tier"] == "C":
                p = governance.file_proposal(governance.Proposal(target=h["signature"], rationale=h["suspected_cause"], evidence=[json.dumps(e, ensure_ascii=False, default=str) for e in h["evidence"]], suggested_patch="(model validator to assess)", proposed_by=self.actor))
                self.decide(h["signature"], "filed_tier_c_proposal", proposal_id=p.id)
                proposals.append(p.model_dump())
                continue
            if h["agent"] == "resolution" and h["signature"] in ("resolution:alias_miss", "resolution:threshold_too_strict"):
                candidates += self._resolution_mutations(h)
        return {"candidates": [str(c) for c in candidates], "proposals": proposals}

    def _resolution_mutations(self, h: dict[str, Any]) -> list[Path]:
        reg = self.rt.registry
        step = self.genome.param("threshold_step", 0.05)
        out: list[Path] = []
        aliases: dict[str, str] = {}
        for e in h["evidence"]:
            if e.get("query") and e.get("chosen_feature"):
                k = _best_alias_key(e["query"], e["chosen_feature"])
                if k:
                    aliases[k[0]] = k[1]
                self._add_regression_case(e)

        def m_alias(dst: Path, routing: dict[str, Any]) -> None:
            routing.setdefault("aliases", {}).update(aliases)

        def m_threshold(dst: Path, routing: dict[str, Any]) -> None:
            routing["min_confidence"] = round(routing.get("min_confidence", 0.9) - step, 3)

        def m_aggressive(dst: Path, routing: dict[str, Any]) -> None:
            routing["min_confidence"] = round(routing.get("min_confidence", 0.9) - step, 3)
            routing["ambiguity_margin"] = 0.0

        population = [(m_alias, f"learn alias(es) {aliases} from confirmed match", ["aliases"])] if aliases else []
        population += [(m_threshold, f"lower min_confidence by {step}", ["min_confidence"]), (m_aggressive, f"lower min_confidence by {step} and disable ambiguity guard", ["min_confidence", "ambiguity_margin"])]
        for fn, record, changed in population[: self.genome.param("population_size", 3)]:
            try:
                path = reg.create_candidate("resolution", fn, record, hypothesis={k: h[k] for k in ("signature", "n", "suspected_cause")})
                m = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
                m["changed_params"] = changed
                (path / "manifest.json").write_text(json.dumps(m, indent=1, ensure_ascii=False), encoding="utf-8")
                out.append(path)
                self.decide(h["signature"], "candidate_created", path=path.name, record=record)
            except PolicyViolation as e:
                self.rt.telemetry.blocked(self.name, self.genome.version, e.invariant, detail=e.detail)
        return out

    def _add_regression_case(self, e: dict[str, Any]) -> None:
        check_candidate_paths([relpath(str(REGRESSION))], self.actor)  # Tier B path
        data = json.loads(REGRESSION.read_text(encoding="utf-8")) if REGRESSION.exists() else {"_notice": "Grown automatically from production corrections (Tier B).", "cases": []}
        cid = f"r-{e['subject']}-{e['chosen_feature']}"
        if any(c["id"] == cid for c in data["cases"]):
            return
        data["cases"].append({"id": cid, "source": "human_correction", "at": e["at"], "asset": {"id": e["subject"], "description": e.get("description") or "", "asset_type": "warehouse", "recorded_address": e["query"], "attributes": {}}, "expected": {"action": "commit", "feature_id": e["chosen_feature"]}})
        REGRESSION.parent.mkdir(parents=True, exist_ok=True)
        REGRESSION.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
