"""registry.browse — the FACETED BROWSE for OpenHubForAI.io (owner 2026-06-25).

One catalog, the **record/registry is the unit**, hubs are flexible FACETS. Built OVER the federated search
(`search.search_all`) + the registry ontology — does NOT rebuild search. A registry/record may sit under MULTIPLE
categories: the rigid `maps_to_hub` becomes the PRIMARY category, plus kind / layer / cross-cutting derived tags.
serves_truth=false.

  browse(query, filters) -> {items, records, facets(counts)}
  python3 -m src.teleon.registry.browse --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import sys
from pathlib import Path

py_const_src_teleon_registry_browse__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
if str(py_const_src_teleon_registry_browse__REPO) not in sys.path:
    sys.path.insert(0, str(py_const_src_teleon_registry_browse__REPO))
py_const_src_teleon_registry_browse__ONTOLOGY = _resource("architecture") / "registry_ontology.json"

py_const_src_teleon_registry_browse__FACET_DIMS = ("category", "type", "kind", "layer", "status")
# cross-cutting derivations → a registry lands in EXTRA categories beyond its primary hub (flexible, not rigid)
py_var_src_teleon_registry_browse___CROSS = (
    ("Verification", ("verif", "test", "audit", "proof", "regression", "adversar", "drift", "qa", "formal")),
    ("Discovery", ("discovery", "crawl", "source", "feed", "scrape", "intel", "portal")),
    ("Optimization", ("optimi", "cost", "cache", "arbitrage", "determinism", "equivalence", "latency")),
    ("Execution", ("execution", "runtime", "sandbox", "scheduler", "retry", "rate_limit", "environment")),
    ("Governance", ("provenance", "compliance", "security", "trust", "approval", "redaction", "policy", "receipt")),
)


def py_function_src_teleon_registry_browse___ontology() -> dict:
    return json.loads(py_const_src_teleon_registry_browse__ONTOLOGY.read_text(encoding="utf-8"))


def py_function_src_teleon_registry_browse___kind_map(py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__kind_map__onto: dict) -> dict:
    py_local_src_teleon_registry_browse__kind_map__out: dict[int, str] = {}
    py_local_src_teleon_registry_browse__kind_map__rk = py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__kind_map__onto.get("registry_kinds", {})
    for py_local_src_teleon_registry_browse__kind_map__kind in ("static", "discovery", "meta"):
        for py_local_src_teleon_registry_browse__kind_map__n in py_local_src_teleon_registry_browse__kind_map__rk.get(py_local_src_teleon_registry_browse__kind_map__kind, {}).get("registry_ids", []):
            py_local_src_teleon_registry_browse__kind_map__out[py_local_src_teleon_registry_browse__kind_map__n] = py_local_src_teleon_registry_browse__kind_map__kind
    return py_local_src_teleon_registry_browse__kind_map__out


def py_function_src_teleon_registry_browse__hub_to_category(py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__hub_to_category__hub: str | None) -> str | None:
    if not py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__hub_to_category__hub:
        return None
    py_local_src_teleon_registry_browse__hub_to_category__c = py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__hub_to_category__hub.replace("Open", "").replace("Hub", "").strip()
    return py_local_src_teleon_registry_browse__hub_to_category__c or None


def py_function_src_teleon_registry_browse__categories(py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__categories__reg: dict, py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__categories__kind: str | None = None) -> list[str]:
    """Flexible multi-category for a registry/record. PRIMARY = its hub; plus kind, layer, and cross-cutting tags —
    a record may sit under SEVERAL (the rigid `maps_to_hub` is the primary, not the only)."""
    py_local_src_teleon_registry_browse__categories__cats: list[str] = []
    py_local_src_teleon_registry_browse__categories__primary = py_function_src_teleon_registry_browse__hub_to_category(py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__categories__reg.get("maps_to_hub"))
    if py_local_src_teleon_registry_browse__categories__primary:
        py_local_src_teleon_registry_browse__categories__cats.append(py_local_src_teleon_registry_browse__categories__primary)
    py_local_src_teleon_registry_browse__categories__blob = f"{py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__categories__reg.get('id', '')} {py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__categories__reg.get('holds', '')} {py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__categories__reg.get('stage', '')}".lower()
    for py_local_src_teleon_registry_browse__categories__label, py_local_src_teleon_registry_browse__categories__needles in py_var_src_teleon_registry_browse___CROSS:
        if any(n in py_local_src_teleon_registry_browse__categories__blob for n in py_local_src_teleon_registry_browse__categories__needles) and py_local_src_teleon_registry_browse__categories__label not in py_local_src_teleon_registry_browse__categories__cats:
            py_local_src_teleon_registry_browse__categories__cats.append(py_local_src_teleon_registry_browse__categories__label)
    return py_local_src_teleon_registry_browse__categories__cats or ["General"]


def py_function_src_teleon_registry_browse__facets() -> dict:
    """Every facet dimension + its values, computed from the RECONCILED SPINE (ontology ∪ live catalogs)."""
    from src.teleon.registry.index import py_function_src_teleon_registry_index__reconciled_index
    py_local_src_teleon_registry_browse__facets__items = py_function_src_teleon_registry_index__reconciled_index()["registries"]
    py_local_src_teleon_registry_browse__facets__vals: dict[str, set] = {d: set() for d in py_const_src_teleon_registry_browse__FACET_DIMS}
    for py_local_src_teleon_registry_browse__facets__it in py_local_src_teleon_registry_browse__facets__items:
        for py_local_src_teleon_registry_browse__facets__c in py_local_src_teleon_registry_browse__facets__it["categories"]:
            py_local_src_teleon_registry_browse__facets__vals["category"].add(py_local_src_teleon_registry_browse__facets__c)
        py_local_src_teleon_registry_browse__facets__vals["type"].add(py_local_src_teleon_registry_browse__facets__it["type"])
        if py_local_src_teleon_registry_browse__facets__it["kind"]:
            py_local_src_teleon_registry_browse__facets__vals["kind"].add(py_local_src_teleon_registry_browse__facets__it["kind"])
        py_local_src_teleon_registry_browse__facets__vals["layer"].add(py_local_src_teleon_registry_browse__facets__it["layer"])
        py_local_src_teleon_registry_browse__facets__vals["status"].add(py_local_src_teleon_registry_browse__facets__it["status"])
    return {d: sorted(v) for d, v in py_local_src_teleon_registry_browse__facets__vals.items()}


def py_function_src_teleon_registry_browse__browse(query: str = "", filters: dict | None = None, *, py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse__limit: int = 300) -> dict:
    """Faceted browse over the catalog. Filters by any of category/type/kind/layer/status (combine freely) + a
    free-text query. With a query it ALSO federates into populated records via search.search_all. Returns the
    filtered items, the federated records, and facet COUNTS. serves_truth=false."""
    filters = {py_local_src_teleon_registry_browse__browse__k: v for py_local_src_teleon_registry_browse__browse__k, v in (filters or {}).items() if v}
    from src.teleon.registry.index import py_function_src_teleon_registry_index__reconciled_index
    py_local_src_teleon_registry_browse__browse__items = py_function_src_teleon_registry_index__reconciled_index()["registries"]

    def py_function_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse__match(py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse_match__it: dict) -> bool:
        if filters.get("category") and filters["category"] not in py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse_match__it["categories"]:
            return False
        for py_local_src_teleon_registry_browse__browse_match__dim in ("type", "kind", "layer", "status"):
            if filters.get(py_local_src_teleon_registry_browse__browse_match__dim) and filters[py_local_src_teleon_registry_browse__browse_match__dim] != py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse_match__it.get(py_local_src_teleon_registry_browse__browse_match__dim):
                return False
        if query and query.lower() not in f"{py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse_match__it['id']} {py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse_match__it['holds']} {' '.join(py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse_match__it['categories'])}".lower():
            return False
        return True

    py_local_src_teleon_registry_browse__browse__filtered = [py_local_src_teleon_registry_browse__browse__it for py_local_src_teleon_registry_browse__browse__it in py_local_src_teleon_registry_browse__browse__items if py_function_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse__match(py_local_src_teleon_registry_browse__browse__it)][:py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse__limit]

    # facet counts: for each dim, count items passing ALL OTHER filters (so the count previews the result of picking it)
    py_local_src_teleon_registry_browse__browse__counts: dict[str, dict] = {}
    for py_local_src_teleon_registry_browse__browse__dim in py_const_src_teleon_registry_browse__FACET_DIMS:
        py_local_src_teleon_registry_browse__browse__others = {py_local_src_teleon_registry_browse__browse__k: v for py_local_src_teleon_registry_browse__browse__k, v in filters.items() if py_local_src_teleon_registry_browse__browse__k != py_local_src_teleon_registry_browse__browse__dim}

        def py_function_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse__m2(py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse_m2__it: dict, py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse_m2__others=py_local_src_teleon_registry_browse__browse__others) -> bool:
            if py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse_m2__others.get("category") and py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse_m2__others["category"] not in py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse_m2__it["categories"]:
                return False
            for py_local_src_teleon_registry_browse__browse_m2__d in ("type", "kind", "layer", "status"):
                if py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse_m2__others.get(py_local_src_teleon_registry_browse__browse_m2__d) and py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse_m2__others[py_local_src_teleon_registry_browse__browse_m2__d] != py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse_m2__it.get(py_local_src_teleon_registry_browse__browse_m2__d):
                    return False
            return True
        py_local_src_teleon_registry_browse__browse__c: dict[str, int] = {}
        for py_local_src_teleon_registry_browse__browse__it in py_local_src_teleon_registry_browse__browse__items:
            if not py_function_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse__m2(py_local_src_teleon_registry_browse__browse__it):
                continue
            py_local_src_teleon_registry_browse__browse__keys = py_local_src_teleon_registry_browse__browse__it["categories"] if py_local_src_teleon_registry_browse__browse__dim == "category" else [py_local_src_teleon_registry_browse__browse__it.get(py_local_src_teleon_registry_browse__browse__dim)]
            for py_local_src_teleon_registry_browse__browse__k in py_local_src_teleon_registry_browse__browse__keys:
                if py_local_src_teleon_registry_browse__browse__k:
                    py_local_src_teleon_registry_browse__browse__c[py_local_src_teleon_registry_browse__browse__k] = py_local_src_teleon_registry_browse__browse__c.get(py_local_src_teleon_registry_browse__browse__k, 0) + 1
        py_local_src_teleon_registry_browse__browse__counts[py_local_src_teleon_registry_browse__browse__dim] = dict(sorted(py_local_src_teleon_registry_browse__browse__c.items(), key=lambda py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse__kv: -py_arg_src_teleon_registry_browse__py_function_src_teleon_registry_browse__browse__kv[1]))

    py_local_src_teleon_registry_browse__browse__records: list[dict] = []
    if query:
        try:
            from .search import py_function_src_teleon_registry_search__search_all
            py_local_src_teleon_registry_browse__browse__records = py_function_src_teleon_registry_search__search_all(query)
        except Exception:  # noqa: BLE001 — browse stays useful even if a catalog is offline
            py_local_src_teleon_registry_browse__browse__records = []

    return {"query": query, "filters": filters, "count": len(py_local_src_teleon_registry_browse__browse__filtered), "items": py_local_src_teleon_registry_browse__browse__filtered,
            "records": py_local_src_teleon_registry_browse__browse__records, "facets": py_local_src_teleon_registry_browse__browse__counts, "serves_truth": False}


def py_function_src_teleon_registry_browse__self_test() -> int:
    py_local_src_teleon_registry_browse__self_test__f = py_function_src_teleon_registry_browse__facets()
    assert len(py_local_src_teleon_registry_browse__self_test__f["type"]) >= 155, f"the reconciled spine (ontology ∪ catalogs) is browsable: {len(py_local_src_teleon_registry_browse__self_test__f['type'])}"
    assert {"static", "discovery", "meta"} <= set(py_local_src_teleon_registry_browse__self_test__f["kind"]), py_local_src_teleon_registry_browse__self_test__f["kind"]
    assert len(py_local_src_teleon_registry_browse__self_test__f["category"]) >= 5, py_local_src_teleon_registry_browse__self_test__f["category"]

    # a record sits under MULTIPLE categories (flexible — the win)
    py_local_src_teleon_registry_browse__self_test__onto = py_function_src_teleon_registry_browse___ontology()
    py_local_src_teleon_registry_browse__self_test__multi = [r for r in py_local_src_teleon_registry_browse__self_test__onto["registries"] if len(py_function_src_teleon_registry_browse__categories(r)) >= 2]
    assert len(py_local_src_teleon_registry_browse__self_test__multi) >= 20, f"flexible multi-category should be common, got {len(py_local_src_teleon_registry_browse__self_test__multi)}"

    # browse default = the full catalog; filtering narrows; facet counts present
    py_local_src_teleon_registry_browse__self_test__allb = py_function_src_teleon_registry_browse__browse()
    assert py_local_src_teleon_registry_browse__self_test__allb["count"] >= 155 and py_local_src_teleon_registry_browse__self_test__allb["facets"]["kind"], py_local_src_teleon_registry_browse__self_test__allb["count"]
    py_local_src_teleon_registry_browse__self_test__disc = py_function_src_teleon_registry_browse__browse(filters={"kind": "discovery"})
    assert 0 < py_local_src_teleon_registry_browse__self_test__disc["count"] < py_local_src_teleon_registry_browse__self_test__allb["count"], f"a facet filter narrows: {py_local_src_teleon_registry_browse__self_test__disc['count']}/{py_local_src_teleon_registry_browse__self_test__allb['count']}"
    # combine two facets + a query
    py_local_src_teleon_registry_browse__self_test__combo = py_function_src_teleon_registry_browse__browse(query="cost", filters={"category": "Optimization"})
    assert all("Optimization" in it["categories"] for it in py_local_src_teleon_registry_browse__self_test__combo["items"]), "category filter holds"
    print(f"browse self-test: OK ({py_local_src_teleon_registry_browse__self_test__allb['count']} registries browsable · {len(py_local_src_teleon_registry_browse__self_test__f['category'])} categories · "
          f"{len(py_local_src_teleon_registry_browse__self_test__multi)} multi-category · facets+counts · federates records on query · serves_truth=false)")
    return 0


def main(py_arg_src_teleon_registry_browse__main__argv: list[str]) -> int:
    if "--self-test" in py_arg_src_teleon_registry_browse__main__argv:
        return py_function_src_teleon_registry_browse__self_test()
    if "--facets" in py_arg_src_teleon_registry_browse__main__argv:
        print(json.dumps(py_function_src_teleon_registry_browse__facets(), indent=2))
        return 0
    print("usage: browse --self-test | --facets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
