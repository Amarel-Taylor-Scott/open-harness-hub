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

from .port import py_function_src_teleon_registry_port__all_catalogs, py_function_src_teleon_registry_port__available_all, py_function_src_teleon_registry_port__catalog

# the registries each workflow consults (ontology ids). Queried when on the menu; else surfaced as 'relevant'.
py_var_src_teleon_registry_search___TROUBLESHOOT = ["failure", "failure_recovery", "drift", "agent_qa", "vulnerability_sources", "observability"]
py_var_src_teleon_registry_search___IMPROVE = ["optimization_pass", "equivalence", "economic_opportunity", "determinism", "provider_arbitrage", "cache"]
py_var_src_teleon_registry_search___PER_CATALOG = 5


def py_function_src_teleon_registry_search___label(py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__label__rec: dict) -> str:
    for py_local_src_teleon_registry_search__label__k in ("name", "id", "canonical", "pass", "failure_type"):
        if py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__label__rec.get(py_local_src_teleon_registry_search__label__k):
            return str(py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__label__rec[py_local_src_teleon_registry_search__label__k])
    return next((v for v in py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__label__rec.values() if isinstance(v, str) and v), "?")


def py_function_src_teleon_registry_search__search_all(py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__search_all__query: str, *, py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__search_all__per_catalog: int = py_var_src_teleon_registry_search___PER_CATALOG) -> list[dict]:
    """One query across EVERY catalog on the menu -> registry-tagged hits (the federated search)."""
    py_local_src_teleon_registry_search__search_all__out = []
    for py_local_src_teleon_registry_search__search_all__name in py_function_src_teleon_registry_port__available_all():
        for py_local_src_teleon_registry_search__search_all__rec in py_function_src_teleon_registry_port__catalog(py_local_src_teleon_registry_search__search_all__name).search(py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__search_all__query, limit=py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__search_all__per_catalog):
            py_local_src_teleon_registry_search__search_all__out.append({"registry": py_local_src_teleon_registry_search__search_all__name, "name": py_function_src_teleon_registry_search___label(py_local_src_teleon_registry_search__search_all__rec)})
    return py_local_src_teleon_registry_search__search_all__out


def py_function_src_teleon_registry_search___facet(py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__facet__query: str, py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__facet__registry_ids: list[str], py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__facet__workflow: str) -> dict:
    """Query the on-menu registries for a workflow; honestly surface the relevant ones not yet on the menu."""
    py_local_src_teleon_registry_search__facet__found: dict[str, list[str]] = {}
    py_local_src_teleon_registry_search__facet__relevant_offmenu: list[str] = []
    py_local_src_teleon_registry_search__facet__cats = py_function_src_teleon_registry_port__all_catalogs()
    for py_local_src_teleon_registry_search__facet__rid in py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__facet__registry_ids:
        if py_local_src_teleon_registry_search__facet__rid in py_local_src_teleon_registry_search__facet__cats:
            py_local_src_teleon_registry_search__facet__hits = [py_function_src_teleon_registry_search___label(rec) for rec in py_function_src_teleon_registry_port__catalog(py_local_src_teleon_registry_search__facet__rid).search(py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__facet__query, limit=py_var_src_teleon_registry_search___PER_CATALOG)]
            if py_local_src_teleon_registry_search__facet__hits:
                py_local_src_teleon_registry_search__facet__found[py_local_src_teleon_registry_search__facet__rid] = py_local_src_teleon_registry_search__facet__hits
        else:
            py_local_src_teleon_registry_search__facet__relevant_offmenu.append(py_local_src_teleon_registry_search__facet__rid)
    return {"workflow": py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__facet__workflow, "query": py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__facet__query, "found": py_local_src_teleon_registry_search__facet__found,
            "relevant_not_yet_on_menu": py_local_src_teleon_registry_search__facet__relevant_offmenu, "serves_truth": False}


def py_function_src_teleon_registry_search__build_capability(py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__build_capability__intent: str) -> dict:
    """BUILD: ingredients across every registry, grouped by registry, ready to compose into a DAG."""
    py_local_src_teleon_registry_search__build_capability__by_reg: dict[str, list[str]] = {}
    for py_local_src_teleon_registry_search__build_capability__h in py_function_src_teleon_registry_search__search_all(py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__build_capability__intent):
        py_local_src_teleon_registry_search__build_capability__by_reg.setdefault(py_local_src_teleon_registry_search__build_capability__h["registry"], []).append(py_local_src_teleon_registry_search__build_capability__h["name"])
    return {"workflow": "build", "intent": py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__build_capability__intent, "ingredients_by_registry": py_local_src_teleon_registry_search__build_capability__by_reg,
            "candidate_dag": True, "serves_truth": False}


def py_function_src_teleon_registry_search__troubleshoot(py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__troubleshoot__symptom: str) -> dict:
    """TROUBLESHOOT: search the diagnostic registries for a symptom / error."""
    return py_function_src_teleon_registry_search___facet(py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__troubleshoot__symptom, py_var_src_teleon_registry_search___TROUBLESHOOT, "troubleshoot")


def py_function_src_teleon_registry_search__improve(py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__improve__capability: str) -> dict:
    """IMPROVE: search the improvement registries for cheaper / faster / more-deterministic alternatives."""
    return py_function_src_teleon_registry_search___facet(py_arg_src_teleon_registry_search__py_function_src_teleon_registry_search__improve__capability, py_var_src_teleon_registry_search___IMPROVE, "improve")
