"""registry.search — FEDERATED search across ALL registries (how a DAG/pipeline builder uses the buffet).

The menu (port.py) searches ONE catalog; this searches them ALL at once and tags each hit with its registry, so a
builder can do the three core jobs from one query:

  - BUILD a capability:        build_capability(intent)  -> ranked ingredients across every registry, grouped, to compose a DAG
  - TROUBLESHOOT a capability:  troubleshoot(symptom)    -> the DIAGNOSTIC registries (failure / recovery / drift / vuln / observability)
  - IMPROVE a capability:       improve(capability)       -> the IMPROVEMENT registries (optimization / equivalence / arbitrage / determinism / cache)

Each facet QUERIES the registries that are reachable on the menu and HONESTLY lists the relevant ones that aren't
queryable yet (policy/runtime registries, until they join the universal interface). serves_truth=false.
"""
from __future__ import annotations

from .port import CATALOGS, available, catalog

# the registries each workflow consults (ontology ids). Queried when on the menu; else surfaced as 'relevant'.
_TROUBLESHOOT = ["failure", "failure_recovery", "drift", "agent_qa", "vulnerability_sources", "observability"]
_IMPROVE = ["optimization_pass", "equivalence", "economic_opportunity", "determinism", "provider_arbitrage", "cache"]
_PER_CATALOG = 5


def _label(rec: dict) -> str:
    return rec.get("name") or rec.get("id") or rec.get("canonical") or "?"


def search_all(query: str, *, per_catalog: int = _PER_CATALOG) -> list[dict]:
    """One query across EVERY catalog on the menu -> registry-tagged hits (the federated search)."""
    out = []
    for name in available():
        for rec in catalog(name).search(query, limit=per_catalog):
            out.append({"registry": name, "name": _label(rec)})
    return out


def _facet(query: str, registry_ids: list[str], workflow: str) -> dict:
    """Query the on-menu registries for a workflow; honestly surface the relevant ones not yet on the menu."""
    found: dict[str, list[str]] = {}
    relevant_offmenu: list[str] = []
    for rid in registry_ids:
        if rid in CATALOGS:
            hits = [_label(rec) for rec in catalog(rid).search(query, limit=_PER_CATALOG)]
            if hits:
                found[rid] = hits
        else:
            relevant_offmenu.append(rid)
    return {"workflow": workflow, "query": query, "found": found,
            "relevant_not_yet_on_menu": relevant_offmenu, "serves_truth": False}


def build_capability(intent: str) -> dict:
    """BUILD: ingredients across every registry, grouped by registry, ready to compose into a DAG."""
    by_reg: dict[str, list[str]] = {}
    for h in search_all(intent):
        by_reg.setdefault(h["registry"], []).append(h["name"])
    return {"workflow": "build", "intent": intent, "ingredients_by_registry": by_reg,
            "candidate_dag": True, "serves_truth": False}


def troubleshoot(symptom: str) -> dict:
    """TROUBLESHOOT: search the diagnostic registries for a symptom / error."""
    return _facet(symptom, _TROUBLESHOOT, "troubleshoot")


def improve(capability: str) -> dict:
    """IMPROVE: search the improvement registries for cheaper / faster / more-deterministic alternatives."""
    return _facet(capability, _IMPROVE, "improve")
