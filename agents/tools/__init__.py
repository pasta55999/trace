"""Typed tool contracts. Agents may only reach the domain through these."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agents.runtime import Runtime
from services import adaptation, aggregation, cases, governance, hazard, ingestion, location, monitoring, reporting
from services.common import new_id
from services.register import PendingLink, Store


class Empty(BaseModel):
    pass


class AssetId(BaseModel):
    asset_id: str


class CandidatesIn(BaseModel):
    asset_id: str
    aliases: dict[str, str] = Field(default_factory=dict)
    fuzzy_cutoff: float = 0.82


class CommitIn(BaseModel):
    asset_id: str
    candidate: dict[str, Any] | None
    reason: str
    actor: str


class QuestionIn(BaseModel):
    asset_id: str
    kind: str
    question_en: str
    question_ar: str
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    created_by: str


class RunIn(BaseModel):
    label: str = "baseline"
    overrides: dict[str, Any] = Field(default_factory=dict)
    actor: str = "agent:orchestrator"


class DiffIn(BaseModel):
    prev_run_id: str | None
    run_id: str


class CompareIn(BaseModel):
    asset_id: str
    measure_id: str


class RenderIn(BaseModel):
    run_id: str
    lang: str
    diff: dict[str, Any] | None = None
    adaptation: dict[str, Any] | None = None


class OpenCaseIn(BaseModel):
    title: str
    owner: str
    evidence_request: list[str]
    linked_results: list[str]
    actor: str


class DecideIn(BaseModel):
    case_id: str
    decision: str
    actor: str


class ProposalIn(BaseModel):
    target: str
    rationale: str
    evidence: list[str]
    suggested_patch: str
    proposed_by: str


def register_tools(rt: Runtime, store: Store) -> None:
    b = rt.broker
    b.register("load_portfolio", "Load the portfolio spreadsheet into the register", Empty, lambda: ingestion.load_portfolio(store), mutating=True)
    b.register("load_documents", "Extract fields from uploaded documents (content firewall applied)", Empty, lambda: ingestion.load_documents(store), mutating=True)
    b.register("list_assets", "List physical assets with attributes and links", Empty, lambda: [a.model_dump() for a in store.s.assets.values()])
    b.register("list_documents", "List documents with extracted fields and firewall flags", Empty, lambda: [d.model_dump() for d in store.s.documents.values()])
    b.register("geocode_candidates", "Ranked location candidates for an asset", CandidatesIn, lambda asset_id, aliases, fuzzy_cutoff: [c.model_dump() for c in location.candidates(store.s.assets[asset_id], aliases, fuzzy_cutoff)])
    b.register("commit_location", "Commit a chosen candidate (or unresolved) for an asset", CommitIn, lambda asset_id, candidate, reason, actor: location.commit(store, store.s.assets[asset_id], location.Candidate(**candidate) if candidate else None, reason, actor).model_dump(), mutating=True)
    b.register("create_question", "Create a targeted pending question for a human", QuestionIn, lambda **kw: _create_question(store, **kw), mutating=True)
    b.register("run_scenario", "Run the flood scenario over the portfolio (deterministic engine)", RunIn, lambda label, overrides, actor: aggregation.run_scenario(store, None, overrides, label, actor), mutating=True)
    b.register("get_run", "Fetch a stored run", type("RunId", (BaseModel,), {"__annotations__": {"run_id": str}}), lambda run_id: store.s.runs[run_id])
    b.register("diff_runs", "Explain what changed between two runs", DiffIn, lambda prev_run_id, run_id: monitoring.diff_runs(store, prev_run_id, run_id))
    b.register("compare_measure", "Compare baseline vs a protective measure for one asset", CompareIn, lambda asset_id, measure_id: adaptation.compare(store, asset_id, measure_id))
    b.register("list_measures", "Available adaptation measures", Empty, lambda: list(adaptation.measures().values()))
    b.register("sample_heat", "District-level heat indicator (25 km source)", AssetId, lambda asset_id: hazard.sample_heat(store.s.assets[asset_id].district_id).model_dump())
    b.register("render_brief", "Render the bilingual brief from a run", RenderIn, lambda run_id, lang, diff, adaptation: reporting.render_brief(reporting.brief_tree(store, store.s.runs[run_id], diff, adaptation), lang))
    b.register("brief_tree", "Structured result tree for a run", RenderIn, lambda run_id, lang, diff, adaptation: reporting.brief_tree(store, store.s.runs[run_id], diff, adaptation))
    b.register("open_case", "Open a review case for humans", OpenCaseIn, lambda **kw: cases.open_case(store, **kw).model_dump(), mutating=True)
    b.register("decide_case", "Record a human decision on a case (humans only)", DecideIn, lambda case_id, decision, actor: cases.decide(store, case_id, decision, actor).model_dump(), mutating=True)
    b.register("coverage", "Transparent coverage counters", Empty, store.coverage)
    b.register("governance_registry", "Model, dataset and regulatory-mapping versions", Empty, governance.registry)
    b.register("file_proposal", "File a Tier C change proposal for human model validators", ProposalIn, lambda **kw: governance.file_proposal(governance.Proposal(**kw)).model_dump(), mutating=True)


def _create_question(store: Store, **kw: Any) -> dict[str, Any]:
    p = PendingLink(id=new_id("Q"), **kw)
    store.s.pending[p.id] = p
    store.audit(kw["created_by"], "question_created", question_id=p.id, asset_id=kw["asset_id"], kind=kw["kind"])
    return p.model_dump()
