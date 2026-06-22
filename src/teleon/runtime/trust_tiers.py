"""trust_tiers — the trust-agnostic seam: a component's trust tier gates its EXECUTION environment (which sandbox) and
WHAT DATA may flow to it (data class). Deny-by-default: an unknown/missing tier is treated as the most restrictive. This
is the operational form of `discovery ≠ trust` — a discovered component may be in the registry but may only run in a hard
sandbox on synthetic inputs until it earns a higher tier. serves_truth=false.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_POLICY = Path(__file__).resolve().parents[3] / "architecture" / "trust_tiers.json"


@lru_cache(maxsize=1)
def _policy() -> dict:
    return json.loads(_POLICY.read_text())


@lru_cache(maxsize=1)
def _tiers() -> dict:
    return {t["tier"]: t for t in _policy()["tiers"]}


def _sensitivity(data_class: str) -> int:
    order = _policy()["data_classes_by_sensitivity"]
    return order.index(data_class) if data_class in order else len(order)   # unknown class = most sensitive


def tier_of(component: dict) -> str:
    """A component's trust tier, defaulting to the most restrictive ('experimental') when unset — deny-by-default."""
    t = (component or {}).get("trust_tier")
    return t if t in _tiers() else "experimental"


def required_sandbox(tier: str) -> str:
    """The sandbox level this tier MUST run in ('hard' for an unknown tier)."""
    return _tiers().get(tier, {}).get("sandbox", "hard")


def can_execute(tier: str, data_class: str) -> dict:
    """May a component of `tier` execute on data of `data_class`? Allowed only if the data is no more sensitive than the
    tier's max_data_class. Returns {allowed, tier, required_sandbox, max_data_class, reason}. Deny-by-default."""
    spec = _tiers().get(tier)
    if spec is None:
        return {"allowed": False, "tier": tier, "required_sandbox": "hard", "max_data_class": "synthetic",
                "reason": f"unknown trust tier {tier!r} — denied by default", "serves_truth": False}
    allowed = _sensitivity(data_class) <= _sensitivity(spec["max_data_class"])
    return {"allowed": allowed, "tier": tier, "required_sandbox": spec["sandbox"], "max_data_class": spec["max_data_class"],
            "reason": ("ok" if allowed else f"{tier} may not run on {data_class!r} data (max {spec['max_data_class']!r})"),
            "serves_truth": False}


def gate_component(component: dict, data_class: str) -> dict:
    """Convenience: resolve a component's tier and decide if it may run on this data class."""
    return can_execute(tier_of(component), data_class)
