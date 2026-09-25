"""Telemetry & feedback store (append-only JSONL). Input to the Reflector and the Guardian."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable

from services.common import RUNTIME, now_iso

DEFAULT_PATH = RUNTIME / "telemetry.jsonl"


class Telemetry:
    def __init__(self, path: Path | None = None):
        self.path = Path(os.environ.get("TRACE_TELEMETRY_PATH", path or DEFAULT_PATH))

    def emit(self, kind: str, agent: str, **data: Any) -> dict[str, Any]:
        ev = {"at": now_iso(), "kind": kind, "agent": agent, **data}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False, default=str) + "\n")
        return ev

    def events(self, kind: str | None = None, agent: str | None = None) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            ev = json.loads(line)
            if (kind is None or ev["kind"] == kind) and (agent is None or ev["agent"] == agent):
                out.append(ev)
        return out

    # convenience emitters -----------------------------------------------------------------
    def tool_call(self, agent: str, genome: str, tool: str, args: dict[str, Any], ok: bool, ms: float) -> None:
        self.emit("tool_call", agent, genome=genome, tool=tool, args=args, ok=ok, ms=round(ms, 1))

    def decision(self, agent: str, genome: str, subject: str, decision: str, **detail: Any) -> None:
        self.emit("decision", agent, genome=genome, subject=subject, decision=decision, **detail)

    def correction(self, agent: str, genome: str, subject: str, signature: str, **detail: Any) -> None:
        """A human changed an agent's output. This is the primary learning signal."""
        self.emit("human_correction", agent, genome=genome, subject=subject, signature=signature, **detail)

    def blocked(self, agent: str, genome: str, invariant: str, **detail: Any) -> None:
        self.emit("policy_block", agent, genome=genome, invariant=invariant, **detail)

    def sli(self, agent: str, genome: str) -> dict[str, Any]:
        """Live service-level indicators for one genome version."""
        dec = [e for e in self.events("decision", agent) if e.get("genome") == genome]
        cor = [e for e in self.events("human_correction", agent) if e.get("genome") == genome]
        blk = [e for e in self.events("policy_block", agent) if e.get("genome") == genome]
        return {"decisions": len(dec), "corrections": len(cor), "override_rate": round(len(cor) / len(dec), 3) if dec else 0.0, "policy_blocks": len(blk)}

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()
