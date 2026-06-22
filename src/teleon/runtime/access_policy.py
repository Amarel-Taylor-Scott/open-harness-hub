"""src.teleon.runtime.access_policy — WHO may use a tool/key/capability (authorization over the registries).

Registries say what EXISTS; the credential plane says what's REACHABLE; THIS says who's ENTITLED. Deny-by-default for
sensitive resources (least privilege). A principal may always use a credential service they brought their OWN key for
(BYO satisfies a plan-gated KEY), but BYO never grants a restricted TOOL. Config (tiers/roles/paid_plans/grants) is
single-sourced from architecture/access_policy.json. Pure: classify() takes a resource DICT (so it's testable without
loading every registry); the caller passes the resource's governance/key_ownership/plane fields. serves_truth=false; Teleon layer.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]


@lru_cache(maxsize=1)
def _cfg() -> dict:
    return json.loads((_REPO / "architecture" / "access_policy.json").read_text(encoding="utf-8"))


@dataclass
class Principal:
    id: str = "anon"
    role: str = "anonymous"            # anonymous | user | developer | staff (or custom)
    plan: str = "free"                 # free | pro | enterprise | internal
    grants: set = field(default_factory=set)      # restricted grants held: {evasion, social_scrape, pii}
    byo_keys: set = field(default_factory=set)     # credential service ids the principal supplied their own key for

    @classmethod
    def from_role(cls, role: str, *, byo_keys=None) -> "Principal":
        r = _cfg()["roles"].get(role, {"plan": "free", "grants": []})
        return cls(id=role, role=role, plan=r["plan"], grants=set(r.get("grants", [])), byo_keys=set(byo_keys or []))


def classify(resource: dict) -> dict:
    """Resource dict (fields: internal?, governance?, plane?, key_ownership?, key_service?, keyless?, deterministic?, kind?)
    -> {tier, grant?, key_service?, reason}. Most-restrictive-wins (the precedence in access_policy.json)."""
    gov = (resource.get("governance") or "").lower()
    if resource.get("internal") or resource.get("kind") == "private_bench":
        return {"tier": "internal", "reason": "internal / private-bench resource"}
    if "evasion" in gov:
        return {"tier": "restricted", "grant": "evasion", "reason": "evasion/stealth — governed"}
    if "tos" in gov or "social" in gov or resource.get("plane") == "social_scrape":
        return {"tier": "restricted", "grant": "social_scrape", "reason": "social/ToS-sensitive — governed"}
    if "pii" in gov:
        return {"tier": "restricted", "grant": "pii", "reason": "PII-touching — governed"}
    own = resource.get("key_ownership")
    if own in ("platform", "both", "byo"):
        return {"tier": "plan_gated", "key_service": resource.get("key_service") or resource.get("id"),
                "reason": "needs a platform key (cost) or your own key (BYO)"}
    if resource.get("keyless") and resource.get("deterministic") or resource.get("kind") in ("open_hub", "public"):
        return {"tier": "public", "reason": "keyless deterministic / open"}
    return {"tier": "authenticated", "reason": "default — any signed-in principal"}


def can_access(principal: Principal, resource: dict) -> tuple[bool, str]:
    """(allowed, reason). Deny-by-default."""
    req = classify(resource)
    tier, paid = req["tier"], set(_cfg()["paid_plans"])
    if tier == "public":
        return True, "public"
    if tier == "authenticated":
        return (principal.role != "anonymous", "needs sign-in" if principal.role == "anonymous" else "authenticated")
    if tier == "plan_gated":
        ks = req.get("key_service")
        if ks and ks in principal.byo_keys:
            return True, f"via your own key ({ks}, BYO)"
        if principal.plan in paid:
            return True, f"plan '{principal.plan}'"
        return False, f"needs a paid plan or your own key for '{ks}'"
    if tier == "restricted":
        if principal.role == "anonymous":
            return False, "restricted: sign-in + a grant required"
        g = req.get("grant")
        return (g in principal.grants, f"granted '{g}'" if g in principal.grants else f"needs the '{g}' grant")
    if tier == "internal":
        ok = principal.plan == "internal" or principal.role == "staff"
        return ok, "staff/internal" if ok else "internal/staff only"
    return False, "deny-by-default"


def accessible(principal: Principal, resources: list[dict]) -> list[dict]:
    """Filter a list of resource dicts (each must carry an 'id') to those the principal may use."""
    return [r for r in resources if can_access(principal, r)[0]]


def explain(principal: Principal, resources: list[dict]) -> list[dict]:
    out = []
    for r in resources:
        ok, why = can_access(principal, r)
        out.append({"id": r.get("id"), "tier": classify(r)["tier"], "allowed": ok, "reason": why})
    return out
