"""src.teleon.config.medium_resolver — resolve the MEDIUMS (compute / llm / search) for a (tenant, function).

UI-configurable: a client connects their preferred mediums and can set DIFFERENT mediums for DIFFERENT functions
(architecture/medium_config.json). This resolves the effective mediums by merging, most-specific-first:
``tenant.per_function[function]`` -> ``tenant.per_function['default']`` -> global ``defaults``. The available choices
(the UI dropdowns) are computed from the LIVE registries (no-magic-values), so adding a backend/lane/provider there
makes it selectable in the UI automatically. Pure + deterministic; reads shared DATA only; Teleon-layer — never imports
src.baltor. A medium selection is a routing decision, never truth (serves_truth False).
"""
from __future__ import annotations

import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_CONFIG = _REPO / "architecture" / "medium_config.json"
_A = _REPO / "architecture"


def load_config(*, config: dict | None = None) -> dict:
    return config if config is not None else json.loads(_CONFIG.read_text(encoding="utf-8"))


def available_mediums() -> dict:
    """The selectable mediums per kind — COMPUTED from the live registries so the UI is always in sync."""
    out: dict = {"compute": [], "llm": [], "search": []}
    try:
        m = json.loads((_A / "execution_backend_policy_matrix.json").read_text())
        out["compute"] = [b.split("@")[0] for b in m.get("backends_enum", [])]
        out["compute_ownership"] = list(m.get("compute_ownership", {}).get("modes", {}))
    except Exception:
        pass
    try:
        lc = json.loads((_A / "lowcost_llm_endpoint_registry.json").read_text())
        out["llm"] = sorted({e["provider_id"] for e in lc.get("entries", [])} | {"ollama", "openrouter"})
    except Exception:
        out["llm"] = ["ollama", "cloudflare_workers_ai", "openrouter"]
    try:
        s = json.loads((_A / "search_provider_registry.json").read_text())
        out["search"] = [p["provider_id"] for p in s.get("providers", [])]
    except Exception:
        pass
    return out


def resolve_mediums(tenant: str, function: str, *, config: dict | None = None, validate: bool = True) -> dict:
    """The effective mediums for (tenant, function): per-function override -> tenant default -> global default.
    Returns {compute, compute_ownership, llm, search, fallbacks, secrets, tenant, function, sources, valid, serves_truth}.
    ``sources`` records which layer each medium came from (traceable); ``valid`` flags any unknown medium id."""
    cfg = load_config(config=config)
    defaults = dict(cfg.get("defaults", {}))
    t = cfg.get("tenants", {}).get(tenant, {})
    pf = t.get("per_function", {})
    layers = [("default", defaults), ("tenant_default", pf.get("default", {})), ("function", pf.get(function, {}))]
    resolved: dict = {}
    sources: dict = {}
    for layer_name, layer in layers:
        for k, v in layer.items():
            resolved[k] = v
            sources[k] = layer_name
    avail = available_mediums()
    valid = {}
    if validate:
        for kind in ("compute", "llm", "search"):
            v = resolved.get(kind)
            valid[kind] = (v in avail.get(kind, [])) if v is not None else True
    return {
        "tenant": tenant, "function": function,
        "compute": resolved.get("compute"), "compute_ownership": resolved.get("compute_ownership"),
        "llm": resolved.get("llm"), "search": resolved.get("search"),
        "fallback_compute": resolved.get("fallback_compute"), "fallback_llm": resolved.get("fallback_llm"),
        "secrets": t.get("secrets", {}), "sources": sources, "valid": valid,
        "all_valid": all(valid.values()) if validate else None, "serves_truth": False,
    }


def configured_functions(tenant: str, *, config: dict | None = None) -> list[str]:
    cfg = load_config(config=config)
    return sorted(cfg.get("tenants", {}).get(tenant, {}).get("per_function", {}))
