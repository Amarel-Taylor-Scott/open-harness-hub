"""src.teleon.purpose_tasks.adaptation_ladder — classify a PurposeTask change by the risk-tiered ADAPTATION
LADDER (L0..L5) and decide whether it may auto-promote or must be human-approved.

Reads architecture/capability_adaptation_ladder.json (single source). DENY-BY-DEFAULT: an unknown change type
is treated as L5 (human-gated) — never auto. Enforces the CORE INVARIANT: a task may adapt its MEANS (L0-L3,
auto if the gate passes) but may NEVER autonomously change its ENDS (L5, always human) or make a
`forbidden_autonomous` change (weaken criteria / remove evals / disable observability / drop source handles).
Pure + deterministic; control logic uses the numeric LEVEL, not change-name strings.
"""
from __future__ import annotations

import json
from pathlib import Path

_LADDER_PATH = Path(__file__).resolve().parents[3] / "architecture" / "capability_adaptation_ladder.json"
_UNKNOWN_LEVEL = 5  # deny-by-default: unrecognized change → highest tier, human-gated
_cache: dict | None = None


def _ladder() -> dict:
    global _cache
    if _cache is None:
        _cache = json.loads(_LADDER_PATH.read_text(encoding="utf-8"))
    return _cache


def _index() -> dict[str, dict]:
    """change_type → its level record."""
    out: dict[str, dict] = {}
    for lv in _ladder().get("levels", []):
        for ct in lv.get("change_types", []):
            out[ct] = lv
    return out


def classify(change_type: str) -> dict:
    """Return {level, name, gate, requires_human, known} for a change type. Unknown → L5/human (deny-by-default)."""
    lv = _index().get(change_type)
    if lv is None:
        return {"level": _UNKNOWN_LEVEL, "name": "unknown_boundary", "gate": "human_approval",
                "requires_human": True, "known": False}
    return {"level": lv["level"], "name": lv["name"], "gate": lv["gate"],
            "requires_human": bool(lv["requires_human"]), "known": True}


def is_forbidden_autonomous(change_type: str) -> bool:
    """True if the change may NEVER be an autonomous candidate adaptation (weakens the contract / hides truth)."""
    return change_type in set(_ladder().get("forbidden_autonomous", []))


def is_ends_change(change_type: str) -> bool:
    """True if the change touches the task's ENDS (purpose/permissions/criteria/systems/risk) — human-gated."""
    return change_type in set(_ladder().get("ends_change_types", []))


def may_auto_promote(change_type: str) -> bool:
    """A change may auto-promote ONLY if it is a known MEANS change (L0-L3), not human-gated, and not forbidden.
    Unknown / ends / forbidden / L4-L5 → False (deny-by-default)."""
    if is_forbidden_autonomous(change_type) or is_ends_change(change_type):
        return False
    c = classify(change_type)
    return c["known"] and not c["requires_human"] and c["level"] <= 3


def required_gate(change_type: str) -> str:
    """The gate a change must clear. Forbidden changes report 'forbidden_autonomous'."""
    if is_forbidden_autonomous(change_type):
        return "forbidden_autonomous"
    return classify(change_type)["gate"]


__all__ = ["classify", "may_auto_promote", "required_gate", "is_forbidden_autonomous", "is_ends_change"]
