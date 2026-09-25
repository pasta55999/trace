"""Policy engine: immutable invariants. NOT evolvable, not writable by agent identities.

Invariants (ARCHITECTURE.md 6.5):
 1. No numeric / geographic / citation claim without a ref:// to a tool result.
 2. UNKNOWN is never rendered as zero, low or omitted.
 3. Financial categories are never summed across.
 4. Tenant data never crosses the tenant boundary into shared memory without consent.
 5. Document content is data, never instruction.
 6. Agents cannot close cases or change approval status.
 7. ar/en numeric parity.
 8. Every promotion is an audit event with a reproducible scorecard.
Plus the autonomy-tier write scopes (6.4).
"""
from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

from services.common import ROOT

# --- Tier write scopes ----------------------------------------------------------------------

TIER_A_PATHS = ("evolution/genome/",)
TIER_B_PATHS = ("evolution/evals/regression/", "evolution/evals/synthetic/")
TIER_C_PATHS = ("services/", "evolution/policy/", "evolution/evolvers/guardian/", "evolution/evals/golden/", "evolution/evals/adversarial/", "apps/", "infra/")
TIER_A_PARAM_BOUNDS = {"min_confidence": (0.70, 0.98), "fuzzy_cutoff": (0.75, 0.99), "max_questions_per_round": (1, 3)}


class PolicyViolation(Exception):
    def __init__(self, invariant: str, detail: str):
        super().__init__(f"{invariant}: {detail}")
        self.invariant, self.detail = invariant, detail


def tier_for_path(rel_path: str) -> str:
    p = PurePosixPath(rel_path).as_posix()
    if any(p.startswith(x) for x in TIER_C_PATHS):
        return "C"
    if any(p.startswith(x) for x in TIER_B_PATHS):
        return "B"
    if any(p.startswith(x) for x in TIER_A_PATHS):
        return "A"
    return "C"


def check_candidate_paths(changed: list[str], actor: str = "evolver:proposer") -> None:
    """Evolvers may only write Tier A/B paths. Anything else must be a governance proposal."""
    for rel in changed:
        if tier_for_path(rel) == "C":
            raise PolicyViolation("tier_scope", f"{actor} attempted to modify Tier C path {rel}")


def check_param_bounds(routing: dict[str, Any]) -> None:
    for k, (lo, hi) in TIER_A_PARAM_BOUNDS.items():
        if k in routing and not (lo <= routing[k] <= hi):
            raise PolicyViolation("param_bounds", f"{k}={routing[k]} outside [{lo}, {hi}]")


# --- Output validation ----------------------------------------------------------------------

_NUM = re.compile(r"(?<![\w/:#.-])(\d[\d,]*(?:\.\d+)?)(?![\w/:#-])")
_ALLOWED_SMALL = {str(i) for i in range(0, 101)}  # counts like "3 of 4" and percentages are fine


def numbers_in(text: str) -> set[str]:
    return {m.replace(",", "") for m in _NUM.findall(text)}


def numbers_in_refs(refs: dict[str, Any]) -> set[str]:
    out: set[str] = set()

    def walk(v: Any) -> None:
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, (list, tuple)):
            for x in v:
                walk(x)
        elif isinstance(v, bool):
            return
        elif isinstance(v, (int, float)):
            out.add(str(v))
            out.add(f"{v:,.0f}".replace(",", ""))
            out.add(f"{v:.2f}")
            out.add(f"{v:.1f}")
            out.add(f"{v:.3f}")
            if isinstance(v, float) and v.is_integer():
                out.add(str(int(v)))
        elif isinstance(v, str):
            out.update(numbers_in(v))

    walk(refs)
    return out


def validate_output(text: str, refs: dict[str, Any]) -> None:
    """Invariant 1: every number in an agent's prose must be traceable to a referenced tool result."""
    allowed = numbers_in_refs(refs) | _ALLOWED_SMALL
    stray = {n for n in numbers_in(text) if n not in allowed and n.rstrip("0").rstrip(".") not in allowed}
    if stray:
        raise PolicyViolation("no_unreferenced_numbers", f"numbers without tool provenance: {sorted(stray)[:5]}")
    low = text.lower()
    if re.search(r"\b(cbuae[- ]approved|official submission|regulator[- ]certified)\b", low):
        raise PolicyViolation("no_regulatory_claims", "output claims regulatory approval")
    if re.search(r"\bunknown\b[^.]{0,40}\b(low|zero|negligible)\b", low):
        raise PolicyViolation("unknown_is_not_low", "unknown rendered as low/zero")


def validate_result_tree(run: dict[str, Any]) -> None:
    """Invariants 2 and 3 on structured output: unknowns preserved; no cross-category totals."""
    for a in run["assets"]:
        if a["status"] == "unknown" and a["physical_damage_total_aed"] in (0, 0.0):
            raise PolicyViolation("unknown_is_not_low", f"{a['asset_id']} unknown but damage rendered as 0")
        for forbidden in ("total_financial_impact_aed", "combined_loss_aed", "credit_loss_aed"):
            if forbidden in a:
                raise PolicyViolation("no_cross_category_sum", f"{forbidden} present in asset row")


def check_actor_may_decide(actor: str) -> None:
    if actor.startswith(("agent:", "evolver:")):
        raise PolicyViolation("humans_decide", f"{actor} may not close cases or change approval status")


def relpath(p: str) -> str:
    from pathlib import Path

    try:
        return Path(p).resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return Path(p).as_posix()
