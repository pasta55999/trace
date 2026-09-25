"""Genome registry: immutable, versioned agent behaviour loaded at run time.

evolution/genome/<agent>/
  ACTIVE                      -> pointer file containing the active version (e.g. v0003)
  v0001/manifest.json         -> parent, eval scores, promotion state, change record
  v0001/system_prompt.en.md, system_prompt.ar.md
  v0001/routing.yaml          -> tunable parameters and learned tables (aliases, templates)
  v0001/skills/*.md           -> procedures the agent follows
  candidates/<id>/            -> proposed versions awaiting verification (gitignored)

Promotion and rollback are pointer moves; versions are never edited in place.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from evolution.policy import check_candidate_paths, check_param_bounds
from services.common import ROOT, now_iso

GENOME_ROOT = Path(os.environ.get("TRACE_GENOME_ROOT", ROOT / "evolution" / "genome"))


@dataclass
class Genome:
    agent: str
    version: str
    path: Path
    routing: dict[str, Any]
    prompts: dict[str, str]
    skills: dict[str, str]
    manifest: dict[str, Any] = field(default_factory=dict)

    def param(self, key: str, default: Any = None) -> Any:
        return self.routing.get(key, default)


class GenomeRegistry:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or GENOME_ROOT)
        self.frozen_file = self.root / "FROZEN"

    # --- read
    def agent_dir(self, agent: str) -> Path:
        return self.root / agent

    def active_version(self, agent: str) -> str:
        return (self.agent_dir(agent) / "ACTIVE").read_text(encoding="utf-8").strip()

    def versions(self, agent: str) -> list[str]:
        return sorted(p.name for p in self.agent_dir(agent).glob("v[0-9]*") if p.is_dir())

    def load(self, agent: str, version: str | None = None, path: Path | None = None) -> Genome:
        p = path or self.agent_dir(agent) / (version or self.active_version(agent))
        routing = yaml.safe_load((p / "routing.yaml").read_text(encoding="utf-8")) or {}
        prompts = {l: (p / f"system_prompt.{l}.md").read_text(encoding="utf-8") for l in ("en", "ar") if (p / f"system_prompt.{l}.md").exists()}
        skills = {s.stem: s.read_text(encoding="utf-8") for s in sorted((p / "skills").glob("*.md"))} if (p / "skills").exists() else {}
        manifest = json.loads((p / "manifest.json").read_text(encoding="utf-8")) if (p / "manifest.json").exists() else {}
        return Genome(agent=agent, version=p.name, path=p, routing=routing, prompts=prompts, skills=skills, manifest=manifest)

    def history(self, agent: str) -> list[dict[str, Any]]:
        out = []
        active = self.active_version(agent)
        for v in self.versions(agent):
            m = self.load(agent, v).manifest
            out.append({"version": v, "active": v == active, **{k: m.get(k) for k in ("parent", "created_at", "change_record", "eval", "promotion_state", "hypothesis")}})
        return out

    def is_frozen(self) -> bool:
        return self.frozen_file.exists()

    # --- write (evolver identities only; Tier A/B paths)
    def create_candidate(self, agent: str, mutate: Any, change_record: str, hypothesis: dict[str, Any] | None = None, parent: str | None = None) -> Path:
        parent = parent or self.active_version(agent)
        cid = f"cand-{now_iso().replace(':', '').replace('-', '')[:15]}-{abs(hash(change_record)) % 10000:04d}"
        dst = self.agent_dir(agent) / "candidates" / cid
        shutil.copytree(self.agent_dir(agent) / parent, dst)
        routing = yaml.safe_load((dst / "routing.yaml").read_text(encoding="utf-8")) or {}
        mutate(dst, routing)  # mutation callback edits routing/prompts/skills inside dst only
        check_param_bounds(routing)
        (dst / "routing.yaml").write_text(yaml.safe_dump(routing, allow_unicode=True, sort_keys=False), encoding="utf-8")
        manifest = {"agent": agent, "parent": parent, "created_at": now_iso(), "change_record": change_record, "hypothesis": hypothesis, "promotion_state": "candidate", "eval": None}
        (dst / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
        # the registry root *is* evolution/genome wherever it is mounted; check the logical paths
        check_candidate_paths(["evolution/genome/" + f.relative_to(self.root).as_posix() for f in dst.rglob("*") if f.is_file()])
        return dst

    def promote(self, agent: str, candidate: Path, eval_result: dict[str, Any], state: str = "full") -> str:
        if self.is_frozen():
            raise PermissionError("evolution frozen by guardian")
        nxt = f"v{int(self.versions(agent)[-1][1:]) + 1:04d}"
        dst = self.agent_dir(agent) / nxt
        shutil.copytree(candidate, dst)
        m = json.loads((dst / "manifest.json").read_text(encoding="utf-8"))
        m.update({"eval": eval_result, "promotion_state": state, "promoted_at": now_iso(), "version": nxt})
        (dst / "manifest.json").write_text(json.dumps(m, indent=1, ensure_ascii=False), encoding="utf-8")
        (self.agent_dir(agent) / "ACTIVE").write_text(nxt, encoding="utf-8")
        shutil.rmtree(candidate, ignore_errors=True)
        self._git_commit(agent, nxt, m["change_record"])
        return nxt

    def rollback(self, agent: str, reason: str) -> str | None:
        cur = self.active_version(agent)
        m = self.load(agent, cur).manifest
        parent = m.get("parent")
        if not parent or not (self.agent_dir(agent) / parent).exists():
            return None
        (self.agent_dir(agent) / "ACTIVE").write_text(parent, encoding="utf-8")
        m.update({"promotion_state": "rolled_back", "rolled_back_at": now_iso(), "rollback_reason": reason})
        (self.agent_dir(agent) / cur / "manifest.json").write_text(json.dumps(m, indent=1, ensure_ascii=False), encoding="utf-8")
        self._git_commit(agent, parent, f"rollback {cur}: {reason}")
        return parent

    def freeze(self, reason: str) -> None:
        self.frozen_file.write_text(f"{now_iso()} {reason}\n", encoding="utf-8")

    def unfreeze(self) -> None:
        if self.frozen_file.exists():
            self.frozen_file.unlink()

    def _git_commit(self, agent: str, version: str, msg: str) -> None:
        if os.environ.get("TRACE_GENOME_GIT") != "1":
            return
        try:
            subprocess.run(["git", "add", str(self.agent_dir(agent))], cwd=ROOT, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-q", "-m", f"genome({agent}): {version} - {msg}"], cwd=ROOT, check=True, capture_output=True)
        except Exception:
            pass
