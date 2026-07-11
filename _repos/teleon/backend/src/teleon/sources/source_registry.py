"""source_registry — query the OpenSourceHub source registry (_repos/shared-backend-components/architecture/source_registry.json). Find authoritative
sources by industry / entity / field, and order them as a COST-ORDERED DESCENT (free public registries first → your own
browser → paid search → grounded → stealth) so a freshness pipeline tries the cheapest authoritative source first. Every
source is a CANDIDATE (discovery != trust); its authority is recorded, not asserted — the verify gate + human review
disposition. Generalizes the healthcare-specific provider_directory_sources across all industries. serves_truth=false.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from functools import lru_cache
from pathlib import Path

_REGISTRY = _resource("architecture") / "source_registry.json"


@lru_cache(maxsize=1)
def _registry() -> dict:
    return json.loads(_REGISTRY.read_text())


def _cost_rank(tier: str) -> int:
    order = _registry()["cost_order"]
    return order.index(tier) if tier in order else len(order)


def sources() -> list:
    return sorted(_registry()["sources"])


def source(source_id: str) -> dict | None:
    return _registry()["sources"].get(source_id)


def _matches(rec: dict, industry, entity, field) -> bool:
    inds = rec.get("industries", [])
    if industry and not (industry in inds or "all" in inds):
        return False
    if entity and not (entity in rec.get("entities", []) or "any" in rec.get("entities", [])):
        return False
    if field and field not in rec.get("fields", []):
        return False
    return True


def sources_for(*, industry: str | None = None, entity: str | None = None, field: str | None = None) -> list:
    """The source ids covering the given industry / entity / field (any subset). 'all'/'any' wildcards match."""
    return sorted(sid for sid, rec in _registry()["sources"].items() if _matches(rec, industry, entity, field))


def descent(*, industry: str | None = None, entity: str | None = None, field: str | None = None) -> list:
    """The matching sources as a cost-ordered descent: free public registries first, then own browser, then paid search,
    then grounded, then stealth (ties by recorded authority). Returns [{source, cost_tier, plane, authority, access}]."""
    recs = [(sid, _registry()["sources"][sid]) for sid in sources_for(industry=industry, entity=entity, field=field)]
    recs.sort(key=lambda sr: (_cost_rank(sr[1]["cost_tier"]), -sr[1].get("authority", 0.0), sr[0]))
    return [{"source": sid, "cost_tier": r["cost_tier"], "plane": r["plane"], "authority": r.get("authority"),
             "access": r["access"], "kind": r.get("kind")} for sid, r in recs]
