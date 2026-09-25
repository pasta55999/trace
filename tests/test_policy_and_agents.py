"""Policy invariants and the agent workflow."""
from __future__ import annotations

import pytest

from agents.orchestrator import Orchestrator
from agents.runtime import LLMProvider, Runtime
from evolution.policy import PolicyViolation, check_candidate_paths, check_param_bounds, validate_output
from services import reporting
from services.cases import AgentMayNotDecide, decide


def test_numbers_need_provenance():
    validate_output("Damage is 1,250,000 AED", {"result://A": {"damage": 1_250_000.0}})
    with pytest.raises(PolicyViolation):
        validate_output("Damage is 9,999,999 AED", {"result://A": {"damage": 1_250_000.0}})


def test_no_regulatory_claims_or_unknown_as_low():
    with pytest.raises(PolicyViolation):
        validate_output("This export is CBUAE-approved", {})
    with pytest.raises(PolicyViolation):
        validate_output("Flood depth is unknown, so risk is low", {})


def test_tier_scopes_and_bounds():
    check_candidate_paths(["evolution/genome/resolution/candidates/x/routing.yaml"])
    with pytest.raises(PolicyViolation):
        check_candidate_paths(["services/fin_engine/__init__.py"])
    with pytest.raises(PolicyViolation):
        check_candidate_paths(["evolution/evals/golden/resolution.json"])
    with pytest.raises(PolicyViolation):
        check_param_bounds({"min_confidence": 0.5})


def _investigation(registry, telemetry, store):
    rt = Runtime(registry=registry, telemetry=telemetry)
    o = Orchestrator(rt, store)
    return o, o.start()


def test_workflow_links_locates_and_surfaces_concentration(registry, telemetry, store):
    o, r = _investigation(registry, telemetry, store)
    cov = r["status"]["coverage"]
    assert cov["assets_total"] == 4 and cov["assets_location_confirmed"] == 2 and cov["documents_with_firewall_flags"] == 1
    kinds = {q["kind"] for q in r["status"]["questions"]}
    assert kinds == {"location", "switchboard_location"}
    run = r["status"]["run"]
    assert run["aggregation"]["concentration"]["assets_in_footprint"] == ["A-001", "A-002"]
    unknown = [a for a in run["assets"] if a["status"] == "unknown"]
    assert {a["asset_id"] for a in unknown} == {"A-003", "A-004"}


def test_answers_update_results_and_diff_classifies(registry, telemetry, store):
    o, r = _investigation(registry, telemetry, store)
    loc = next(q for q in r["status"]["questions"] if q["kind"] == "location")
    a = o.answer(loc["id"], "G-003")
    assert {c["kind"] for c in a["diff"]["changes"]} == {"location_resolved"}
    sw = next(q for q in o.status()["questions"] if q["kind"] == "switchboard_location")
    a = o.answer(sw["id"], "basement")
    assert {c["kind"] for c in a["diff"]["changes"]} == {"new_evidence"}
    run = o.status()["run"]
    assert len(run["aggregation"]["concentration"]["sectors"]) == 3
    assert telemetry.events("human_correction")[0]["signature"] == "resolution:alias_miss"


def test_analyst_is_grounded_in_both_languages(registry, telemetry, store):
    o, _ = _investigation(registry, telemetry, store)
    en = o.ask("Which properties are most exposed to flooding?")
    ar = o.ask("ما العقارات الأكثر عرضة للفيضانات؟")
    assert en["lang"] == "en" and ar["lang"] == "ar" and en["intent"] == ar["intent"] == "flood_ranking"
    assert "not a credit loss" in en["text"] and "A-001" in ar["text"]
    assert "unknown" in en["text"]  # A-003/A-004 reported as unknown, not omitted


class HallucinatingProvider(LLMProvider):
    name = "hallucinating"

    def phrase(self, system, user, facts, lang):
        return "Total exposure is 123,456,789 AED and this analysis is CBUAE-approved."


def test_policy_blocks_llm_hallucination_and_falls_back(registry, telemetry, store):
    rt = Runtime(registry=registry, telemetry=telemetry, provider=HallucinatingProvider())
    o = Orchestrator(rt, store)
    o.start()
    out = o.ask("concentration?")
    assert "123,456,789" not in out["text"] and "CBUAE" not in out["text"]
    assert telemetry.events("policy_block")


def test_brief_parity_and_critic(registry, telemetry, store):
    o, _ = _investigation(registry, telemetry, store)
    b = o.brief()
    assert b["ok"], b["findings"]
    assert reporting.numeric_parity(b["tree"])
    assert "not modelled" in b["html"]["en"] and 'dir="rtl"' in b["html"]["ar"]


def test_agents_cannot_decide_cases(registry, telemetry, store):
    o, _ = _investigation(registry, telemetry, store)
    case_id = next(iter(store.s.cases))
    with pytest.raises(AgentMayNotDecide):
        decide(store, case_id, "approve", actor="agent:analyst")
    with pytest.raises(PolicyViolation):
        o.tool("decide_case", case_id=case_id, decision="approve", actor="agent:orchestrator")
    assert decide(store, case_id, "deeper review", actor="user:credit-committee").status == "decided"
