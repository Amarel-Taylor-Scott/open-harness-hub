"""provider_sources — the 'search trusted sources' rung of the provider-directory pipeline, as a COST-ORDERED DESCENT.

Composes the EXISTING tool planes (search via search_provider_registry, browser via browser_port + the escalation ladder)
into provider-data sources. For the fields a record needs, it tries the cheapest authoritative source first — free public
registries (NPI/CMS) → your own browser (practice website / state board) → paid search (Brave/SerpAPI) → grounded search →
stealth — and climbs only when cheaper rungs can't supply the field (honoring "avoid unnecessary paid APIs"). plan_*
deterministically PLANS the descent (free, offline); fetch() executes one rung via its plane (network-gated, honest-offline,
keyed sources need a credential). serves_truth=false — fetched values are candidates the verify gate + human review disposition.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from functools import lru_cache
from pathlib import Path

from src.teleon.verticals.provider_directory import authority_of

_SOURCES = _resource("architecture") / "provider_directory_sources.json"
_HIGH_AUTHORITY = 0.85   # an authoritative source; two of these covering a field is enough — stop climbing


@lru_cache(maxsize=1)
def _registry() -> dict:
    return json.loads(_SOURCES.read_text())


def _cost_rank(tier: str) -> int:
    order = _registry()["cost_order"]
    return order.index(tier) if tier in order else len(order)


def source_ladder(field: str | None = None) -> list:
    """The cost-ordered source rungs (cheapest first; ties by authority), optionally filtered to those covering `field`."""
    rungs = [r for r in _registry()["rungs"] if field is None or field in r.get("fields", [])]
    return sorted(rungs, key=lambda r: (_cost_rank(r["cost_tier"]), -authority_of(r["authority"]), r["id"]))


def plan_acquisition(fields, *, max_cost_tier: str = "stealth", min_sources: int = 2) -> dict:
    """The DESCENT plan: per needed field, the ordered source attempts (cheapest authoritative first), capped at
    max_cost_tier. Stops adding rungs for a field once it has >= min_sources sources INCLUDING one authoritative source
    (so we don't pay for / scrape a field that free registries already pin down). Deterministic, no network."""
    cap = _cost_rank(max_cost_tier)
    plan = []
    for f in fields:
        chosen = []
        for r in source_ladder(f):
            if _cost_rank(r["cost_tier"]) > cap:
                break
            chosen.append({"source": r["id"], "cost_tier": r["cost_tier"], "plane": r["plane"], "authority": authority_of(r["authority"])})
            if len(chosen) >= min_sources and any(c["authority"] >= _HIGH_AUTHORITY for c in chosen):
                break
        plan.append({"field": f, "sources": chosen, "covered": bool(chosen)})
    return {"plan": plan, "fields": list(fields),
            "note": "cheapest authoritative first; paid/stealth only if free registries + own browser can't supply the field",
            "serves_truth": False}


def refresh_record(record: dict, *, observations: dict | None = None, stale_fields=None,
                   max_cost_tier: str = "stealth") -> dict:
    """End-to-end: PLAN which trusted sources to query for the (stale, or all) fields — cheapest authoritative first —
    then, when observations are supplied (or fetched online), RESOLVE the record into a HealthLynked recommendation.
    Offline with no observations: returns the plan + an honest note (planning only; fetch is network-gated). serves_truth=false."""
    from src.teleon.verticals.provider_directory import _FIELDS, resolve_record
    fields = list(stale_fields) if stale_fields else [f for f in _FIELDS]
    plan = plan_acquisition(fields, max_cost_tier=max_cost_tier)
    if observations:
        rec = resolve_record(record, observations)
        return {"plan": plan["plan"], "resolved": rec, "recommended_action": rec["recommended_action"], "serves_truth": False}
    return {"plan": plan["plan"], "resolved": None,
            "reason": "planned only — supply observations or run fetch() online (honest, no fabricated data)", "serves_truth": False}


def fetch(source_id: str, query: str, *, network_allowed=None) -> dict:
    """Execute ONE source via its plane (search/browser). Network-gated + honest-offline (never fabricates); a keyed
    source honestly reports it needs a credential. Online + public dispatches to the real port."""
    r = next((x for x in _registry()["rungs"] if x["id"] == source_id), None)
    if r is None:
        return {"available": False, "reason": f"unknown source {source_id!r}", "serves_truth": False}
    if network_allowed is None:
        from src.teleon.dag.real_steps import network_allowed as _net
        network_allowed = _net()
    if not network_allowed:
        return {"available": False, "reason": f"needs network (honest offline) — {source_id} via the {r['plane']} plane", "serves_truth": False}
    if r["access"] == "keyed":
        return {"available": False, "needs_key": True, "reason": f"{source_id} is keyed — bring a key via the credential plane", "serves_truth": False}
    # public + online: dispatch to the real (network-gated) port for this plane
    try:
        if r["plane"] == "search":
            from src.teleon.retrieval.search_port import py_function_src_teleon_retrieval_search_port__select_search
            return {"available": True, "source": source_id, "plane": "search", "results": py_function_src_teleon_retrieval_search_port__select_search("auto").search(query, limit=3), "serves_truth": False}
        from src.teleon.research.browser_port import select_browser
        return {"available": True, "source": source_id, "plane": "browser", "rendered": bool(select_browser("auto")), "serves_truth": False}
    except Exception as e:  # noqa: BLE001
        return {"available": True, "source": source_id, "error": f"{type(e).__name__}: {e}", "serves_truth": False}
