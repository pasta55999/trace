"""The self-evolution loop, end to end, on a throwaway registry."""
from __future__ import annotations

import pytest

from agents.orchestrator import Orchestrator
from agents.runtime import Runtime
from evolution.evals.scorecard import scorecard
from evolution.evolvers.guardian import Guardian
from evolution.evolvers.proposer import ProposerAgent
from evolution.evolvers.reflector import ReflectorAgent
from evolution.loop import run_cycle
from services import governance


@pytest.mark.usefixtures("clean_regression")
def test_correction_evolves_resolution_genome(registry, telemetry, store):
    rt = Runtime(registry=registry, telemetry=telemetry)
    o = Orchestrator(rt, store)
    r = o.start()
    assert registry.active_version("resolution") == "v0001"
    loc = next(q for q in r["status"]["questions"] if q["kind"] == "location")
    o.answer(loc["id"], "G-003")

    out = run_cycle(rt)
    assert [h["signature"] for h in out["hypotheses"]] == ["resolution:alias_miss"]
    oc = out["outcomes"][0]
    verdicts = {v["change"]: v for v in oc["verdicts"]}
    assert len(verdicts) == 3
    # the aggressive mutation must be rejected by the adversarial suite
    aggressive = next(v for c, v in verdicts.items() if "disable ambiguity" in c)
    assert not aggressive["pass"] and any("hard fail" in x for x in aggressive["reasons"])
    assert oc["promoted"] == "v0002" and oc["stage"] == "canary"
    assert registry.active_version("resolution") == "v0002"
    # the regression case grown from the correction is now part of the suite and passes
    sc = scorecard(registry, "resolution", version="v0002")
    assert sc["suites"]["regression"]["n"] == 1 and sc["suites"]["regression"]["score"] == 1.0
    # re-running the investigation on the evolved genome needs no human help for A-003
    r2 = Orchestrator(Runtime(registry=registry, telemetry=telemetry), store).start()
    assert next(x for x in r2["resolution"]["resolutions"] if x["asset_id"] == "A-003")["action"] == "commit"
    # promotion is an audit event with a scorecard
    promo = telemetry.events("promotion")
    assert promo and promo[0]["version"] == "v0002"
    assert registry.load("resolution", "v0002").manifest["eval"]["overall"] >= sc["overall"] - 1e-9
    # canary graduates to full once live SLIs are healthy
    assert Guardian(registry, telemetry).check("resolution")["action"] == "canary_promoted_to_full"


def test_guardian_rolls_back_on_slo_breach_and_freezes(registry, telemetry, tmp_path, store):
    rt = Runtime(registry=registry, telemetry=telemetry)
    reg = registry
    # fabricate a promoted version with a bad live override rate
    cand = reg.create_candidate("resolution", lambda d, r: r.__setitem__("min_confidence", 0.85), "test mutation")
    v = reg.promote("resolution", cand, {"overall": 1.0}, state="canary")
    for i in range(3):
        telemetry.decision("resolution", v, f"S{i}", "commit")
        telemetry.correction("resolution", v, f"S{i}", "resolution:threshold_too_strict")
    g = Guardian(reg, telemetry)
    assert g.check("resolution")["action"] == "rolled_back_to_v0001"
    assert reg.active_version("resolution") == "v0001"
    assert reg.load("resolution", v).manifest["promotion_state"] == "rolled_back"


def test_tier_c_signal_becomes_governance_proposal(registry, telemetry, monkeypatch, tmp_path):
    monkeypatch.setattr(governance, "PROPOSALS", tmp_path / "proposals.jsonl")
    rt = Runtime(registry=registry, telemetry=telemetry)
    telemetry.correction("analyst", "v0001", "A-002", "vulnerability:curve_disputed", detail="validator disputes stock curve")
    hyps = ReflectorAgent(rt).run()
    assert hyps[0]["tier"] == "C"
    out = ProposerAgent(rt).run(hyps)
    assert out["candidates"] == [] and out["proposals"][0]["status"] == "awaiting_model_validator"
    assert registry.versions("resolution") == ["v0001"]  # nothing self-modified


def test_kill_switch_and_freeze_block_evolution(registry, telemetry):
    rt = Runtime(registry=registry, telemetry=telemetry)
    registry.freeze("test")
    assert "skipped" in run_cycle(rt)
    registry.unfreeze()
    (registry.root / "KILL_resolution").write_text("x")
    telemetry.correction("resolution", "v0001", "A-003", "resolution:alias_miss", query="مستودع الساحل 2", chosen_feature="G-003", method="name:fuzzy(0.93)", confidence=0.88)
    out = run_cycle(rt)
    assert out["outcomes"] and out["outcomes"][0].get("skipped") == "kill switch"
