"""src.teleon.objectives.tenant_binding — per-tenant objective binding.

Teleon runs the same capability for many tenants, and each prioritizes differently: a compliance tenant wants
accuracy + determinism; a high-volume tenant wants cost; an interactive tenant wants latency. This resolves a
tenant_id to the CapabilityObjective that governs its capability units, so PLACEMENT (which runtime class) and
the non-deterministic -> deterministic DESCENT follow the TENANT's priority — not a global default.

A binding (in the shared registry architecture/tenant_objective_bindings.json) is either a named preset
({"objective_preset": "minimize_cost"}) or an explicit weight policy ({"weights": {...}, "name": "custom"}).
A tenant with no binding gets the registry's documented default. Pure + deterministic (the registry can be
injected for tests); reads shared DATA only; Teleon-layer — never imports src.baltor.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.teleon.objectives.objective import PRESETS, CapabilityObjective, ObjectiveError

#: repo root: this file is src/teleon/objectives/tenant_binding.py -> parents[3] is the repository root.
_REGISTRY_PATH = Path(__file__).resolve().parents[3] / "architecture" / "tenant_objective_bindings.json"
#: the documented fallback when neither the tenant nor the registry names a default priority.
DEFAULT_OBJECTIVE_PRESET = "balanced"


def _load_registry(registry: dict | None = None) -> dict:
    return registry if registry is not None else json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))


def _objective_from_binding(tenant_id: str, binding: dict) -> CapabilityObjective:
    """Build a CapabilityObjective from one binding entry: explicit weights win; else a named preset."""
    if "weights" in binding:
        weights = binding["weights"]
        if not isinstance(weights, dict) or not weights:
            raise ObjectiveError(f"tenant {tenant_id!r} binding has empty/invalid weights")
        return CapabilityObjective(str(binding.get("name", tenant_id)), dict(weights))
    preset = binding.get("objective_preset")
    if preset not in PRESETS:
        raise ObjectiveError(f"tenant {tenant_id!r} binding names unknown objective_preset {preset!r}; "
                             f"known presets: {sorted(PRESETS)}")
    return PRESETS[preset]


def objective_for_tenant(tenant_id: str, *, registry: dict | None = None) -> CapabilityObjective:
    """Resolve the CapabilityObjective governing ``tenant_id``. An explicit binding wins; otherwise the registry's
    default_objective_preset (or the module default). Raises ObjectiveError on a malformed binding/default —
    never a silent wrong priority. Deterministic; the registry may be injected (no disk read) for tests."""
    reg = _load_registry(registry)
    bindings = reg.get("bindings", {})
    if tenant_id in bindings:
        return _objective_from_binding(tenant_id, bindings[tenant_id])
    default_preset = reg.get("default_objective_preset", DEFAULT_OBJECTIVE_PRESET)
    if default_preset not in PRESETS:
        raise ObjectiveError(f"registry default_objective_preset {default_preset!r} is not a known preset")
    return PRESETS[default_preset]


def bound_tenants(*, registry: dict | None = None) -> dict:
    """All explicitly-bound tenant_ids -> their resolved objective name (for listing/telemetry/demo)."""
    reg = _load_registry(registry)
    return {tid: objective_for_tenant(tid, registry=reg).name for tid in reg.get("bindings", {})}
