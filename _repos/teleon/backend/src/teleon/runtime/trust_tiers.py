"""trust_tiers — the trust-agnostic seam: a component's trust tier gates its EXECUTION environment (which sandbox) and
WHAT DATA may flow to it (data class). Deny-by-default: an unknown/missing tier is treated as the most restrictive. This
is the operational form of `discovery ≠ trust` — a discovered component may be in the registry but may only run in a hard
sandbox on synthetic inputs until it earns a higher tier. serves_truth=false.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from functools import lru_cache
from pathlib import Path

py_var_src_teleon_runtime_trust_tiers___POLICY = _resource("architecture") / "trust_tiers.json"


@lru_cache(maxsize=1)
def py_function_src_teleon_runtime_trust_tiers___policy() -> dict:
    return json.loads(py_var_src_teleon_runtime_trust_tiers___POLICY.read_text())


@lru_cache(maxsize=1)
def py_function_src_teleon_runtime_trust_tiers___tiers() -> dict:
    return {t["tier"]: t for t in py_function_src_teleon_runtime_trust_tiers___policy()["tiers"]}


def py_function_src_teleon_runtime_trust_tiers___sensitivity(py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__sensitivity__data_class: str) -> int:
    py_local_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__sensitivity__order = py_function_src_teleon_runtime_trust_tiers___policy()["data_classes_by_sensitivity"]
    return py_local_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__sensitivity__order.index(py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__sensitivity__data_class) if py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__sensitivity__data_class in py_local_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__sensitivity__order else len(py_local_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__sensitivity__order)   # unknown class = most sensitive


def py_function_src_teleon_runtime_trust_tiers__tier_of(py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__tier_of__component: dict) -> str:
    """A component's trust tier, defaulting to the most restrictive ('experimental') when unset — deny-by-default."""
    py_local_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__tier_of__t = (py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__tier_of__component or {}).get("trust_tier")
    return py_local_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__tier_of__t if py_local_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__tier_of__t in py_function_src_teleon_runtime_trust_tiers___tiers() else "experimental"


def py_function_src_teleon_runtime_trust_tiers__required_sandbox(py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__required_sandbox__tier: str) -> str:
    """The sandbox level this tier MUST run in ('hard' for an unknown tier)."""
    return py_function_src_teleon_runtime_trust_tiers___tiers().get(py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__required_sandbox__tier, {}).get("sandbox", "hard")


def py_function_src_teleon_runtime_trust_tiers__can_execute(py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__tier: str, py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__data_class: str) -> dict:
    """May a component of `tier` execute on data of `data_class`? Allowed only if the data is no more sensitive than the
    tier's max_data_class. Returns {allowed, tier, required_sandbox, max_data_class, reason}. Deny-by-default."""
    py_local_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__spec = py_function_src_teleon_runtime_trust_tiers___tiers().get(py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__tier)
    if py_local_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__spec is None:
        return {"allowed": False, "tier": py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__tier, "required_sandbox": "hard", "max_data_class": "synthetic",
                "reason": f"unknown trust tier {py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__tier!r} — denied by default", "serves_truth": False}
    py_local_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__allowed = py_function_src_teleon_runtime_trust_tiers___sensitivity(py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__data_class) <= py_function_src_teleon_runtime_trust_tiers___sensitivity(py_local_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__spec["max_data_class"])
    return {"allowed": py_local_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__allowed, "tier": py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__tier, "required_sandbox": py_local_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__spec["sandbox"], "max_data_class": py_local_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__spec["max_data_class"],
            "reason": ("ok" if py_local_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__allowed else f"{py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__tier} may not run on {py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__data_class!r} data (max {py_local_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__can_execute__spec['max_data_class']!r})"),
            "serves_truth": False}


def py_function_src_teleon_runtime_trust_tiers__gate_component(py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__gate_component__component: dict, py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__gate_component__data_class: str) -> dict:
    """Convenience: resolve a component's tier and decide if it may run on this data class."""
    return py_function_src_teleon_runtime_trust_tiers__can_execute(py_function_src_teleon_runtime_trust_tiers__tier_of(py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__gate_component__component), py_arg_src_teleon_runtime_trust_tiers__py_function_src_teleon_runtime_trust_tiers__gate_component__data_class)
