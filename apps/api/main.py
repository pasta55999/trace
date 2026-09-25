"""TRACE API gateway (prototype: modular monolith, single demo tenant).

Run:  uvicorn apps.api.main:app --reload --port 8000
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from agents.orchestrator import Orchestrator
from agents.runtime import Runtime
from evolution.evolvers.guardian import Guardian
from evolution.loop import run_cycle
from evolution.policy import PolicyViolation
from services import governance
from services.cases import AgentMayNotDecide, decide
from services.register import Store

app = FastAPI(title="TRACE - UAE Climate Financial Risk Intelligence (prototype)", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], allow_methods=["*"], allow_headers=["*"])

rt = Runtime()
store = Store().load()
orch = Orchestrator(rt, store)


class AnswerIn(BaseModel):
    answer: str
    actor: str = "user:analyst"


class AskIn(BaseModel):
    question: str


class CompareIn(BaseModel):
    asset_id: str
    measure_id: str


class DecideIn(BaseModel):
    decision: str
    actor: str = "user:credit-committee"


class FlagIn(BaseModel):
    """A human disputes a modelled result: becomes a Tier C signal for the evolution loop."""

    subject: str
    signature: str  # e.g. "vulnerability:curve_disputed"
    detail: str = ""


@app.exception_handler(PolicyViolation)
async def _policy(_: Any, e: PolicyViolation):
    return HTMLResponse(status_code=422, content=f"policy violation: {e}")


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "llm_provider": rt.provider.name, "tenant": store.tenant_id, "notice": "SYNTHETIC DATA - illustrative scenario, not an operational prediction"}


@app.post("/investigation/start")
def start() -> dict[str, Any]:
    return orch.start()


@app.get("/investigation/status")
def status() -> dict[str, Any]:
    if not orch.inv.last_run_id:
        raise HTTPException(404, "no investigation yet; POST /investigation/start")
    return orch.status()


@app.post("/investigation/questions/{question_id}/answer")
def answer(question_id: str, body: AnswerIn) -> dict[str, Any]:
    if question_id not in store.s.pending:
        raise HTTPException(404, "unknown question")
    return orch.answer(question_id, body.answer, body.actor)


@app.post("/assistant/ask")
def ask(body: AskIn) -> dict[str, Any]:
    if not orch.inv.last_run_id:
        raise HTTPException(409, "start an investigation first")
    return orch.ask(body.question)


@app.get("/measures")
def measures() -> list[dict[str, Any]]:
    return orch.tool("list_measures")


@app.post("/adaptation/compare")
def compare(body: CompareIn) -> dict[str, Any]:
    return orch.compare(body.asset_id, body.measure_id)


@app.get("/report/brief")
def brief(lang: str = "en", asset_id: str | None = None, measure_id: str | None = None, format: str = "html") -> Any:
    adaptation = orch.compare(asset_id, measure_id) if asset_id and measure_id else None
    out = orch.brief(adaptation)
    if not out["ok"]:
        raise HTTPException(422, {"blocked_by_critic": out["findings"]})
    return HTMLResponse(out["html"][lang]) if format == "html" else {"tree": out["tree"], "findings": out["findings"]}


@app.get("/cases")
def cases() -> list[dict[str, Any]]:
    return [c.model_dump() for c in store.s.cases.values()]


@app.post("/cases/{case_id}/decide")
def decide_case(case_id: str, body: DecideIn) -> dict[str, Any]:
    try:
        c = decide(store, case_id, body.decision, body.actor)
    except AgentMayNotDecide as e:
        raise HTTPException(403, str(e))
    store.save()
    return c.model_dump()


@app.post("/results/flag")
def flag(body: FlagIn) -> dict[str, Any]:
    ev = rt.telemetry.correction("analyst", rt.registry.active_version("analyst"), body.subject, body.signature, detail=body.detail)
    return {"recorded": ev}


@app.get("/governance")
def gov() -> dict[str, Any]:
    reg = governance.registry()
    agents = [p.name for p in rt.registry.root.iterdir() if p.is_dir() and (p / "ACTIVE").exists()]
    reg["genomes"] = {a: rt.registry.history(a) for a in agents}
    reg["frozen"] = rt.registry.is_frozen()
    reg["audit_tail"] = store.s.audit[-25:]
    reg["tools"] = rt.broker.describe()
    return reg


@app.get("/evolution/telemetry")
def telemetry(kind: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    return rt.telemetry.events(kind)[-limit:]


@app.post("/evolution/cycle")
def cycle() -> dict[str, Any]:
    return run_cycle(rt)


@app.get("/evolution/guardian")
def guardian() -> list[dict[str, Any]]:
    return [Guardian(rt.registry, rt.telemetry).check(a) for a in ("resolution",)]


@app.post("/evolution/rollback/{agent}")
def rollback(agent: str, reason: str = "manual") -> dict[str, Any]:
    return {"active": rt.registry.rollback(agent, reason)}


@app.get("/evolution/genome/{agent}/{version}")
def genome(agent: str, version: str) -> dict[str, Any]:
    g = rt.registry.load(agent, version)
    return {"agent": agent, "version": g.version, "routing": g.routing, "prompts": g.prompts, "skills": g.skills, "manifest": g.manifest}
