"""src.teleon.runtime.access_policy — WHO may use a tool/key/capability (authorization over the registries).

Registries say what EXISTS; the credential plane says what's REACHABLE; THIS says who's ENTITLED. Deny-by-default for
sensitive resources (least privilege). A principal may always use a credential service they brought their OWN key for
(BYO satisfies a plan-gated KEY), but BYO never grants a restricted TOOL. Config (tiers/roles/paid_plans/grants) is
single-sourced from _repos/shared-backend-components/architecture/access_policy.json. Pure: classify() takes a resource DICT (so it's testable without
loading every registry); the caller passes the resource's governance/key_ownership/plane fields. serves_truth=false; Teleon layer.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

py_var_src_teleon_runtime_access_policy___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])


@lru_cache(maxsize=1)
def py_function_src_teleon_runtime_access_policy___cfg() -> dict:
    return json.loads((_resource("architecture") / "access_policy.json").read_text(encoding="utf-8"))


@dataclass
class py_class_src_teleon_runtime_access_policy__Principal:
    id: str = "anon"
    role: str = "anonymous"            # anonymous | user | developer | staff (or custom)
    plan: str = "free"                 # free | pro | enterprise | internal
    grants: set = field(default_factory=set)      # restricted grants held: {evasion, social_scrape, pii}
    byo_keys: set = field(default_factory=set)     # credential service ids the principal supplied their own key for

    @classmethod
    def from_role(cls, py_arg_src_teleon_runtime_access_policy__py_class_src_teleon_runtime_access_policy__Principal_from_role__role: str, *, byo_keys=None) -> "Principal":
        py_local_src_teleon_runtime_access_policy__py_class_src_teleon_runtime_access_policy__Principal_from_role__r = py_function_src_teleon_runtime_access_policy___cfg()["roles"].get(py_arg_src_teleon_runtime_access_policy__py_class_src_teleon_runtime_access_policy__Principal_from_role__role, {"plan": "free", "grants": []})
        return cls(id=py_arg_src_teleon_runtime_access_policy__py_class_src_teleon_runtime_access_policy__Principal_from_role__role, role=py_arg_src_teleon_runtime_access_policy__py_class_src_teleon_runtime_access_policy__Principal_from_role__role, plan=py_local_src_teleon_runtime_access_policy__py_class_src_teleon_runtime_access_policy__Principal_from_role__r["plan"], grants=set(py_local_src_teleon_runtime_access_policy__py_class_src_teleon_runtime_access_policy__Principal_from_role__r.get("grants", [])), byo_keys=set(byo_keys or []))


def py_function_src_teleon_runtime_access_policy__classify(py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__classify__resource: dict) -> dict:
    """Resource dict (fields: internal?, governance?, plane?, key_ownership?, key_service?, keyless?, deterministic?, kind?)
    -> {tier, grant?, key_service?, reason}. Most-restrictive-wins (the precedence in access_policy.json)."""
    py_local_src_teleon_runtime_access_policy__classify__gov = (py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__classify__resource.get("governance") or "").lower()
    if py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__classify__resource.get("internal") or py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__classify__resource.get("kind") == "private_bench":
        return {"tier": "internal", "reason": "internal / private-bench resource"}
    if "evasion" in py_local_src_teleon_runtime_access_policy__classify__gov:
        return {"tier": "restricted", "grant": "evasion", "reason": "evasion/stealth — governed"}
    if "tos" in py_local_src_teleon_runtime_access_policy__classify__gov or "social" in py_local_src_teleon_runtime_access_policy__classify__gov or py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__classify__resource.get("plane") == "social_scrape":
        return {"tier": "restricted", "grant": "social_scrape", "reason": "social/ToS-sensitive — governed"}
    if "pii" in py_local_src_teleon_runtime_access_policy__classify__gov:
        return {"tier": "restricted", "grant": "pii", "reason": "PII-touching — governed"}
    if py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__classify__resource.get("keyless") or py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__classify__resource.get("kind") in ("open_hub", "public"):
        return {"tier": "public", "reason": "keyless (free) / open — no special entitlement"}
    py_local_src_teleon_runtime_access_policy__classify__own = py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__classify__resource.get("key_ownership")
    if py_local_src_teleon_runtime_access_policy__classify__own in ("platform", "both", "byo"):
        return {"tier": "plan_gated", "key_service": py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__classify__resource.get("key_service") or py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__classify__resource.get("id"),
                "reason": "needs a platform key (cost) or your own key (BYO)"}
    if py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__classify__resource.get("deterministic"):
        return {"tier": "public", "reason": "deterministic, no key"}
    return {"tier": "authenticated", "reason": "default — any signed-in principal"}


def py_function_src_teleon_runtime_access_policy__can_access(py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__principal: py_class_src_teleon_runtime_access_policy__Principal, py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__resource: dict) -> tuple[bool, str]:
    """(allowed, reason). Deny-by-default."""
    py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__req = py_function_src_teleon_runtime_access_policy__classify(py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__resource)
    py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__tier, py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__paid = py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__req["tier"], set(py_function_src_teleon_runtime_access_policy___cfg()["paid_plans"])
    if py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__tier == "public":
        return True, "public"
    if py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__tier == "authenticated":
        return (py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__principal.role != "anonymous", "needs sign-in" if py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__principal.role == "anonymous" else "authenticated")
    if py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__tier == "plan_gated":
        py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__ks = py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__req.get("key_service")
        if py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__ks and py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__ks in py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__principal.byo_keys:
            return True, f"via your own key ({py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__ks}, BYO)"
        if py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__principal.plan in py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__paid:
            return True, f"plan '{py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__principal.plan}'"
        return False, f"needs a paid plan or your own key for '{py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__ks}'"
    if py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__tier == "restricted":
        if py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__principal.role == "anonymous":
            return False, "restricted: sign-in + a grant required"
        py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__g = py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__req.get("grant")
        return (py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__g in py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__principal.grants, f"granted '{py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__g}'" if py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__g in py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__principal.grants else f"needs the '{py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__g}' grant")
    if py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__tier == "internal":
        py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__ok = py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__principal.plan == "internal" or py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__principal.role == "staff"
        return py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__ok, "staff/internal" if py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__can_access__ok else "internal/staff only"
    return False, "deny-by-default"


def py_function_src_teleon_runtime_access_policy__accessible(py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__accessible__principal: py_class_src_teleon_runtime_access_policy__Principal, py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__accessible__resources: list[dict]) -> list[dict]:
    """Filter a list of resource dicts (each must carry an 'id') to those the principal may use."""
    return [r for r in py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__accessible__resources if py_function_src_teleon_runtime_access_policy__can_access(py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__accessible__principal, r)[0]]


def py_function_src_teleon_runtime_access_policy__explain(py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__explain__principal: py_class_src_teleon_runtime_access_policy__Principal, py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__explain__resources: list[dict]) -> list[dict]:
    py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__explain__out = []
    for py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__explain__r in py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__explain__resources:
        py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__explain__ok, py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__explain__why = py_function_src_teleon_runtime_access_policy__can_access(py_arg_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__explain__principal, py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__explain__r)
        py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__explain__out.append({"id": py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__explain__r.get("id"), "tier": py_function_src_teleon_runtime_access_policy__classify(py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__explain__r)["tier"], "allowed": py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__explain__ok, "reason": py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__explain__why})
    return py_local_src_teleon_runtime_access_policy__py_function_src_teleon_runtime_access_policy__explain__out
