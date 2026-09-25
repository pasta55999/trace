"""The signature demonstration, end to end, from the command line.

    python scripts/demo.py [--reset-genomes]

All data is SYNTHETIC. The scenario is illustrative, not an operational prediction.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.orchestrator import Orchestrator  # noqa: E402
from agents.runtime import Runtime  # noqa: E402
from evolution.genome import GENOME_ROOT  # noqa: E402
from evolution.genome.bootstrap import bootstrap  # noqa: E402
from evolution.loop import run_cycle  # noqa: E402
from evolution.telemetry import Telemetry  # noqa: E402
from services.common import RUNTIME  # noqa: E402
from services.register import Store  # noqa: E402


def hr(title: str) -> None:
    print("\n" + "=" * 88 + f"\n{title}\n" + "=" * 88)


def fmt(v):  # noqa: ANN001
    if isinstance(v, dict):
        return f"unknown ({v['reason']})" if v.get("unknown") else f"{v['low']:,.0f}-{v['high']:,.0f} [driver: {v['driver']}]"
    return f"{v:,.0f}" if isinstance(v, (int, float)) else str(v)


def main() -> None:
    if "--reset-genomes" in sys.argv:
        for a in ("resolution",):
            for v in (GENOME_ROOT / a).glob("v00[0-9][2-9]"):
                shutil.rmtree(v)
            shutil.rmtree(GENOME_ROOT / a / "candidates", ignore_errors=True)
            (GENOME_ROOT / a / "ACTIVE").write_text("v0001", encoding="utf-8")
        reg = Path(__file__).resolve().parents[1] / "evolution" / "evals" / "regression" / "resolution.json"
        reg.unlink(missing_ok=True)
        (GENOME_ROOT / "FROZEN").unlink(missing_ok=True)
    bootstrap(GENOME_ROOT)
    tel = Telemetry(RUNTIME / "telemetry.jsonl")
    tel.clear()
    rt = Runtime(telemetry=tel)
    orch = Orchestrator(rt, Store())

    hr("1. Upload portfolio  ->  extract  ->  link  ->  locate  ->  assess (agents on genome " + rt.registry.active_version("resolution") + ")")
    r = orch.start()
    print("extraction:", {k: r["extraction"][k] for k in ("documents", "fields", "firewall_flags")})
    print("quarantined instruction text:", r["extraction"]["quarantined"])
    for x in r["resolution"]["resolutions"]:
        print(f"  {x['asset_id']}: {x['action']:15s} {x['precision']:11s} {x['reason']}")
    cov = r["status"]["coverage"]
    print(f"coverage: {cov['assets_location_confirmed']} of {cov['assets_total']} asset locations confirmed, {cov['assets_district_only']} district-only, {cov['assets_unresolved']} unresolved, {cov['open_questions']} open questions")

    hr("2. Targeted questions from the agents")
    for q in r["status"]["questions"]:
        print(f"[{q['id']}] ({q['kind']})\n  EN: {q['question_en']}\n  AR: {q['question_ar']}")

    hr("3. Analyst (bilingual, grounded)")
    print(orch.ask("Which properties in our portfolio are most exposed to flooding, and what financial exposure is associated with them?")["text"])
    print()
    print(orch.ask("ما العقارات الأكثر عرضة للفيضانات في محفظتنا، وما حجم التعرض المالي المرتبط بها؟")["text"])

    hr("4. Human answers: confirm the Arabic warehouse match, then the switchboard location")
    loc_q = next((q for q in r["status"]["questions"] if q["kind"] == "location"), None)
    if loc_q:
        a = orch.answer(loc_q["id"], "G-003")
        print("after location answer:", a["diff"]["summary_en"])
    sw_q = next((q for q in orch.status()["questions"] if q["kind"] == "switchboard_location"), None)
    if sw_q:
        a = orch.answer(sw_q["id"], "basement")
        print("after switchboard answer:", a["diff"]["summary_en"])
        for ch in a["diff"]["changes"]:
            print(f"   {ch['asset_id']} {ch['field']}: {ch['from']} -> {ch['to']}  [{ch['kind']}]")
    print(orch.ask("is there concentration across sectors?")["text"])

    hr("5. Protective measure comparison")
    cmp = orch.compare("A-001", "measure:raise_switchboards")
    print(f"measure: {cmp['measure']['name_en']}  capex {cmp['capex_aed']:,.0f} AED")
    print(f"baseline damage {fmt(cmp['baseline']['physical_damage_total_aed'])}  ->  protected {fmt(cmp['protected']['physical_damage_total_aed'])}")
    print(f"avoided loss (this event): {fmt(cmp['avoided_loss_event_aed'])}   event-conditional B/C: {cmp.get('event_conditional_benefit_cost_ratio')}   NPV: {fmt(cmp['npv_aed'])}")

    hr("6. Bilingual brief (composer + critic)")
    b = orch.brief(cmp)
    print("critic verdict:", "PASS" if b["ok"] else f"BLOCKED {b['findings']}")
    if b["ok"]:
        for l in ("en", "ar"):
            p = RUNTIME / f"brief_{l}.html"
            p.write_text(b["html"][l], encoding="utf-8")
            print("  wrote", p)

    hr("7. Evolution cycle: Reflector -> Proposer -> Verifier -> Promoter -> Guardian")
    out = run_cycle(rt)
    print("hypotheses:", [(h["signature"], "tier " + h["tier"], h["n"]) for h in out["hypotheses"]])
    for oc in out["outcomes"]:
        for v in oc["verdicts"]:
            print(f"  candidate [{'PASS' if v['pass'] else 'FAIL'}] score {v['overall']}: {v['change']} {v['reasons'] or ''}")
        print(f"  => promoted {oc.get('promoted')} ({oc.get('stage')}): {oc.get('change_record')}")
    print("guardian:", out["guardian"][0]["action"], out["guardian"][0]["sli"])

    hr("8. Re-run with the evolved genome " + rt.registry.active_version("resolution"))
    r2 = Orchestrator(Runtime(telemetry=tel), Store()).start()
    for x in r2["resolution"]["resolutions"]:
        print(f"  {x['asset_id']}: {x['action']:15s} {x['precision']:11s} {x['reason']}")
    cov = r2["status"]["coverage"]
    print(f"coverage now: {cov['assets_location_confirmed']} of {cov['assets_total']} confirmed without human help; open questions: {cov['open_questions']}")
    print("guardian after live decisions:", run_cycle(Runtime(telemetry=tel))["guardian"][0]["action"])
    print("\ngenome history:", json.dumps([{k: h[k] for k in ("version", "active", "promotion_state", "change_record")} for h in rt.registry.history("resolution")], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
