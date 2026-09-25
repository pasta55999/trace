"""Case management. Agents may open cases and attach evidence; only humans decide/close."""
from __future__ import annotations

from services.common import new_id, now_iso
from services.register import Case, Store


class AgentMayNotDecide(PermissionError):
    pass


def open_case(store: Store, title: str, owner: str, evidence_request: list[str], linked_results: list[str], actor: str) -> Case:
    c = Case(id=new_id("CASE"), title=title, owner=owner, evidence_request=evidence_request, linked_results=linked_results, history=[{"at": now_iso(), "actor": actor, "event": "opened"}])
    store.s.cases[c.id] = c
    store.audit(actor, "case_opened", case_id=c.id)
    return c


def decide(store: Store, case_id: str, decision: str, actor: str) -> Case:
    if actor.startswith("agent:") or actor.startswith("evolver:"):
        store.audit(actor, "case_decision_blocked", case_id=case_id)
        raise AgentMayNotDecide("consequential decisions require a human actor")
    c = store.s.cases[case_id]
    c.status, c.decision = "decided", decision
    c.history.append({"at": now_iso(), "actor": actor, "event": "decided", "decision": decision})
    store.audit(actor, "case_decided", case_id=case_id)
    return c
