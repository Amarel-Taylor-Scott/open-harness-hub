"""src.teleon.governance.tenant_preferences — the tunable front door: a tenant's wishes compiled to the policy +
objective machinery.

A tenant declares preferences (soft objective + axis priorities), HARD constraints (blockers: MIT-only license,
vetted-only sources, no external egress, allowed runtime classes), an accuracy tolerance, and free-form
suggestions. This compiles them:
  * hard_constraints -> an OrgGuardrailPolicy (excludes disallowed providers/runners/forks BEFORE selection —
    safety beats objective; a "minimize cost" preference can never pick a GPL or unvetted provider).
  * objective_preset / weights -> a CapabilityObjective (ranks the allowed options).
  * accuracy.max_accuracy_drop -> the A/B harness tolerance (how far a descent may drop accuracy).
  * suggestions -> advisory only (surfaced, never enforced).

So HARD blocks, SOFT ranks, SUGGESTIONS advise — and it all reuses the proven policy/objective/A-B machinery.
Pure + deterministic; reads shared DATA only; Teleon-layer — never imports src.baltor; never serves truth.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.teleon.governance.org_policy import OrgGuardrailPolicy
from src.teleon.objectives import PRESETS, CapabilityObjective, ObjectiveError

_PREFS_PATH = Path(__file__).resolve().parents[3] / "architecture" / "tenant_preferences.json"


@dataclass(frozen=True)
class TenantPreferences:
    tenant_id: str
    objective_preset: str = "balanced"
    objective_weights: dict | None = None
    axis_priorities: tuple = ()
    hard_constraints: dict = field(default_factory=dict)
    max_accuracy_drop: float = 0.03
    suggestions: tuple = ()

    def to_objective(self) -> CapabilityObjective:
        """The SOFT preference -> a CapabilityObjective that ranks the allowed options."""
        if self.objective_weights:
            return CapabilityObjective(f"{self.tenant_id}-custom", dict(self.objective_weights))
        if self.objective_preset not in PRESETS:
            raise ObjectiveError(f"tenant {self.tenant_id!r} names unknown objective_preset {self.objective_preset!r}")
        return PRESETS[self.objective_preset]

    def to_org_policy(self) -> OrgGuardrailPolicy:
        """The HARD constraints -> an OrgGuardrailPolicy (the blockers). MIT-only -> allowed_licenses=[MIT];
        vetted_only -> the vetted_only methodology; max_egress=local -> no_external_egress."""
        h = self.hard_constraints or {}
        methodologies = list(h.get("required_methodologies", []) or [])
        if h.get("vetted_only"):
            methodologies.append("vetted_only")
        if h.get("max_egress") == "local":
            methodologies.append("no_external_egress")
        allowed_licenses = tuple(h.get("allowed_licenses", []) or [])
        return OrgGuardrailPolicy(
            policy_id=f"{self.tenant_id}-prefs",
            deny_by_default=bool(h.get("deny_by_default", False)),
            strict_unknown_license=bool(h.get("strict_unknown_license", bool(allowed_licenses))),
            allowed_licenses=allowed_licenses,
            denied_licenses=tuple(h.get("denied_licenses", []) or []),
            allowed_source_domains=tuple(h.get("allowed_source_domains", []) or []),
            denied_source_domains=tuple(h.get("denied_source_domains", []) or []),
            allowed_runtime_classes=tuple(h.get("allowed_runtime_classes", []) or []),
            denied_packages=tuple(h.get("denied_packages", []) or []),
            required_methodologies=tuple(dict.fromkeys(methodologies)))  # dedup, keep order

    def resolve(self) -> dict:
        """The full resolved view: the compiled policy + objective + tolerance + priorities + advisory suggestions."""
        return {"tenant_id": self.tenant_id, "objective": self.to_objective().name,
                "policy": self.to_org_policy().policy_id, "axis_priorities": list(self.axis_priorities),
                "max_accuracy_drop": self.max_accuracy_drop, "suggestions": list(self.suggestions),
                "serves_truth": False}


def _load(registry: dict | None = None) -> dict:
    return registry if registry is not None else json.loads(_PREFS_PATH.read_text(encoding="utf-8"))


def _from_dict(tenant_id: str, d: dict) -> TenantPreferences:
    return TenantPreferences(
        tenant_id=tenant_id, objective_preset=d.get("objective_preset", "balanced"),
        objective_weights=d.get("objective_weights"), axis_priorities=tuple(d.get("axis_priorities", []) or []),
        hard_constraints=dict(d.get("hard_constraints", {}) or {}),
        max_accuracy_drop=float((d.get("accuracy", {}) or {}).get("max_accuracy_drop", 0.03)),
        suggestions=tuple(d.get("suggestions", []) or []))


def preferences_for(tenant_id: str, *, registry: dict | None = None) -> TenantPreferences:
    """Resolve a tenant's tunable preferences (its own entry, else the documented default). Validation of the soft
    objective happens lazily in to_objective(); hard constraints compile in to_org_policy()."""
    reg = _load(registry)
    d = reg.get("tenants", {}).get(tenant_id) or reg.get("default", {})
    return _from_dict(tenant_id, d)


def known_tenants(*, registry: dict | None = None) -> list[str]:
    return sorted(_load(registry).get("tenants", {}))
