"""Agent runtime: LLM provider, typed tool broker, telemetry and policy hooks, base agent."""
from __future__ import annotations

import os
import time
from typing import Any, Callable

import httpx
from pydantic import BaseModel, ValidationError

from evolution.genome import Genome, GenomeRegistry
from evolution.policy import PolicyViolation, check_actor_may_decide, validate_output
from evolution.telemetry import Telemetry


# --- LLM providers ---------------------------------------------------------------------------

class LLMProvider:
    name = "base"

    def phrase(self, system: str, user: str, facts: dict[str, Any], lang: str) -> str | None:
        """Return natural-language prose for already-computed facts, or None to use templates."""
        raise NotImplementedError


class MockProvider(LLMProvider):
    """Offline provider: agents fall back to their bilingual templates. Deterministic."""

    name = "mock"

    def phrase(self, system: str, user: str, facts: dict[str, Any], lang: str) -> str | None:
        return None


class OpenAICompatibleProvider(LLMProvider):
    """Any OpenAI-compatible endpoint (vLLM in-region, etc.). Only used to *phrase* facts."""

    name = "openai-compatible"

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url, self.api_key, self.model = base_url.rstrip("/"), api_key, model

    def phrase(self, system: str, user: str, facts: dict[str, Any], lang: str) -> str | None:
        try:
            r = httpx.post(f"{self.base_url}/chat/completions", headers={"Authorization": f"Bearer {self.api_key}"}, json={"model": self.model, "temperature": 0, "messages": [{"role": "system", "content": system + "\nRespond in " + ("Arabic" if lang == "ar" else "English") + ". Use only numbers present in FACTS."}, {"role": "user", "content": f"QUESTION: {user}\nFACTS: {facts}"}]}, timeout=30)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception:
            return None


def provider_from_env() -> LLMProvider:
    if os.environ.get("TRACE_LLM_BASE_URL") and os.environ.get("TRACE_LLM_API_KEY"):
        return OpenAICompatibleProvider(os.environ["TRACE_LLM_BASE_URL"], os.environ["TRACE_LLM_API_KEY"], os.environ.get("TRACE_LLM_MODEL", "default"))
    return MockProvider()


# --- Tool broker -----------------------------------------------------------------------------

class Tool(BaseModel):
    name: str
    description: str
    input_model: type[BaseModel]
    fn: Callable[..., Any]
    mutating: bool = False

    model_config = {"arbitrary_types_allowed": True}


class ToolBroker:
    """Agents call tools by name with validated arguments; every call is telemetered."""

    def __init__(self, telemetry: Telemetry):
        self.tools: dict[str, Tool] = {}
        self.telemetry = telemetry

    def register(self, name: str, description: str, input_model: type[BaseModel], fn: Callable[..., Any], mutating: bool = False) -> None:
        self.tools[name] = Tool(name=name, description=description, input_model=input_model, fn=fn, mutating=mutating)

    def call(self, agent: "Agent", name: str, **kwargs: Any) -> Any:
        tool = self.tools[name]
        if name in ("decide_case",):
            check_actor_may_decide(agent.actor)
        try:
            args = tool.input_model(**kwargs)
        except ValidationError as e:
            self.telemetry.tool_call(agent.name, agent.genome.version, name, kwargs, False, 0)
            raise PolicyViolation("typed_tools_only", f"{name}: {e.errors()[0]['msg']}")
        t0 = time.perf_counter()
        try:
            out = tool.fn(**args.model_dump())
            self.telemetry.tool_call(agent.name, agent.genome.version, name, args.model_dump(), True, (time.perf_counter() - t0) * 1000)
            return out
        except Exception:
            self.telemetry.tool_call(agent.name, agent.genome.version, name, args.model_dump(), False, (time.perf_counter() - t0) * 1000)
            raise

    def describe(self) -> list[dict[str, Any]]:
        return [{"name": t.name, "description": t.description, "schema": t.input_model.model_json_schema(), "mutating": t.mutating} for t in self.tools.values()]


# --- Base agent ------------------------------------------------------------------------------

class Runtime:
    def __init__(self, registry: GenomeRegistry | None = None, telemetry: Telemetry | None = None, provider: LLMProvider | None = None):
        self.registry = registry or GenomeRegistry()
        self.telemetry = telemetry or Telemetry()
        self.provider = provider or provider_from_env()
        self.broker = ToolBroker(self.telemetry)


class Agent:
    name = "base"

    def __init__(self, rt: Runtime, genome: Genome | None = None):
        self.rt = rt
        self.genome = genome or rt.registry.load(self.name)

    @property
    def actor(self) -> str:
        return f"agent:{self.name}"

    def tool(self, name: str, **kwargs: Any) -> Any:
        return self.rt.broker.call(self, name, **kwargs)

    def decide(self, subject: str, decision: str, **detail: Any) -> None:
        self.rt.telemetry.decision(self.name, self.genome.version, subject, decision, **detail)

    def say(self, text: str, refs: dict[str, Any], lang: str, user: str = "") -> dict[str, Any]:
        """Emit user-facing prose. An LLM may rephrase, but the policy validator has the last word."""
        phrased = self.rt.provider.phrase(self.genome.prompts.get(lang, ""), user, refs, lang)
        final = phrased or text
        try:
            validate_output(final, refs)
        except PolicyViolation as e:
            self.rt.telemetry.blocked(self.name, self.genome.version, e.invariant, detail=e.detail, provider=self.rt.provider.name)
            if phrased:  # fall back to the deterministic template, re-validated
                validate_output(text, refs)
                final = text
            else:
                raise
        return {"text": final, "refs": sorted(refs.keys()), "lang": lang, "agent": self.name, "genome": self.genome.version}
