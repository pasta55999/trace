"""Orchestrator: drives the investigation state machine (scattered portfolio -> defensible case)."""
from __future__ import annotations

from typing import Any

from agents.runtime import Agent, Runtime
from agents.specialists.analyst import AnalystAgent
from agents.specialists.evidence_gap import EvidenceGapAgent
from agents.specialists.extraction import ExtractionAgent
from agents.specialists.intake import IntakeAgent
from agents.specialists.report_composer import ReportComposerAgent
from agents.specialists.resolution import ResolutionAgent
from agents.tools import register_tools
from services.common import new_id, now_iso
from services.register import Investigation, Store


class Orchestrator(Agent):
    name = "orchestrator"

    def __init__(self, rt: Runtime, store: Store):
        from evolution.genome import Genome

        self.rt, self.store = rt, store
        self.genome = Genome(agent="orchestrator", version="static", path=None, routing={}, prompts={}, skills={})  # type: ignore[arg-type]
        register_tools(rt, store)
        self.inv: Investigation = next(iter(store.s.investigations.values()), None) or Investigation(id=new_id("INV"))
        store.s.investigations[self.inv.id] = self.inv

    # --- state machine -------------------------------------------------------------------
    def _transition(self, state: str, **detail: Any) -> None:
        self.inv.state = state  # type: ignore[assignment]
        self.inv.history.append({"at": now_iso(), "state": state, **detail})
        self.store.audit(self.actor, "state", state=state)

    def start(self) -> dict[str, Any]:
        self.store.reset()
        self.inv = Investigation(id=new_id("INV"))
        self.store.s.investigations[self.inv.id] = self.inv
        self._transition("uploaded")
        intake = IntakeAgent(self.rt).run()
        extraction = ExtractionAgent(self.rt).run()
        self._transition("extracted", fields=extraction["fields"], quarantined=len(extraction["quarantined"]))
        resolution = ResolutionAgent(self.rt).run()
        self._transition("linked")
        self._transition("located", **self.store.coverage())
        run = self._assess("baseline")
        self.store.save()
        return {"investigation": self.inv.model_dump(), "intake": intake, "extraction": extraction, "resolution": resolution, "run_id": run["run_id"], "status": self.status()}

    def _assess(self, label: str) -> dict[str, Any]:
        run = self.tool("run_scenario", label=label, actor=self.actor)
        self.inv.previous_run_id, self.inv.last_run_id = self.inv.last_run_id, run["run_id"]
        self._transition("assessed", run_id=run["run_id"])
        self._transition("aggregated")
        EvidenceGapAgent(self.rt).run(run, [q.model_dump() for q in self.store.open_questions()])
        if not self.store.s.cases:
            c = run["aggregation"]["concentration"]
            self.tool("open_case", title="Shared flood footprint across sectors", owner="credit-risk-analyst", evidence_request=["confirm asset locations", "confirm switchboard locations", "obtain flood cover status where unknown"], linked_results=[f"result://{a}" for a in c["assets_in_footprint"]], actor=self.actor)
            self._transition("reviewed")
        return run

    # --- human answers (the learning signal) -------------------------------------------
    def answer(self, question_id: str, answer: str, actor: str = "user:analyst") -> dict[str, Any]:
        q = self.store.s.pending[question_id]
        asset = self.store.s.assets[q.asset_id]
        q.status, q.answer = "answered", answer
        if q.kind == "location":
            chosen = next((c for c in q.candidates if c["feature_id"] == answer), None)
            if chosen is None:
                from services import location as loc_svc

                asset.attributes["plot_ref"] = answer
                asset.attribute_sources["plot_ref"] = f"user://{actor}"
                cands = loc_svc.candidates(asset)
                chosen = cands[0].model_dump() if cands and cands[0].confidence >= 0.9 else None
                signature = "resolution:missing_evidence"
            else:
                signature = "resolution:alias_miss" if chosen["method"].startswith("name:fuzzy") else "resolution:threshold_too_strict"
            if chosen is None:
                return {"error": "could not resolve from the provided reference"}
            self.tool("commit_location", asset_id=asset.id, candidate=chosen, reason=f"confirmed by {actor}", actor=actor)
            genome = self.rt.registry.active_version("resolution")
            self.rt.telemetry.correction("resolution", genome, asset.id, signature, query=asset.recorded_address, description=asset.description, chosen_feature=chosen["feature_id"], chosen_label=chosen["label"], method=chosen["method"], confidence=chosen["confidence"], tenant_consent="synthetic")
        else:
            asset.attributes[q.kind] = answer
            asset.attribute_sources[q.kind] = f"user://{actor}"
        self.store.audit(actor, "question_answered", question_id=question_id, kind=q.kind)
        run = self._assess("after-answer")
        diff = self.tool("diff_runs", prev_run_id=self.inv.previous_run_id, run_id=run["run_id"])
        self.store.save()
        return {"run_id": run["run_id"], "diff": diff, "status": self.status()}

    # --- queries ------------------------------------------------------------------------
    def status(self) -> dict[str, Any]:
        run = self.store.s.runs.get(self.inv.last_run_id) if self.inv.last_run_id else None
        diff = self.tool("diff_runs", prev_run_id=self.inv.previous_run_id, run_id=self.inv.last_run_id) if self.inv.last_run_id else None
        docs = [{"id": d.id, "type": d.type, "language": d.language, "related_collateral": d.related_collateral, "fields": len([f for f in d.fields if not f.flagged_instruction]), "firewall_flags": d.firewall_flags, "title": d.pages[0]["lines"][0] if d.pages and d.pages[0]["lines"] else d.id} for d in self.store.s.documents.values()]
        return {"investigation": self.inv.model_dump(), "coverage": self.store.coverage(), "questions": [q.model_dump() for q in self.store.open_questions()], "run": run, "diff": diff, "cases": [c.model_dump() for c in self.store.s.cases.values()], "assets": [a.model_dump() for a in self.store.s.assets.values()], "locations": [l.model_dump() for l in self.store.s.locations.values() if l.id in {a.location_id for a in self.store.s.assets.values()}], "documents": docs, "activity": self.store.s.audit[-40:]}

    def ask(self, question: str) -> dict[str, Any]:
        run = self.store.s.runs[self.inv.last_run_id]
        diff = self.tool("diff_runs", prev_run_id=self.inv.previous_run_id, run_id=self.inv.last_run_id)
        return AnalystAgent(self.rt).ask(question, run, diff)

    def compare(self, asset_id: str, measure_id: str) -> dict[str, Any]:
        return self.tool("compare_measure", asset_id=asset_id, measure_id=measure_id)

    def brief(self, adaptation: dict[str, Any] | None = None) -> dict[str, Any]:
        diff = self.tool("diff_runs", prev_run_id=self.inv.previous_run_id, run_id=self.inv.last_run_id)
        out = ReportComposerAgent(self.rt).compose(self.inv.last_run_id, diff, adaptation)
        if out["ok"]:
            self._transition("reported")
            self.store.save()
        return out
