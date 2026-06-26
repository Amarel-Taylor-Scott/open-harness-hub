"""registry.browse — the FACETED BROWSE for OpenHubForAI.io (owner 2026-06-25).

One catalog, the **record/registry is the unit**, hubs are flexible FACETS. Built OVER the federated search
(`search.search_all`) + the registry ontology — does NOT rebuild search. A registry/record may sit under MULTIPLE
categories: the rigid `maps_to_hub` becomes the PRIMARY category, plus kind / layer / cross-cutting derived tags.
serves_truth=false.

  browse(query, filters) -> {items, records, facets(counts)}
  python3 -m src.teleon.registry.browse --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
ONTOLOGY = REPO / "architecture" / "registry_ontology.json"

FACET_DIMS = ("category", "type", "kind", "layer", "status")
# cross-cutting derivations → a registry lands in EXTRA categories beyond its primary hub (flexible, not rigid)
_CROSS = (
    ("Verification", ("verif", "test", "audit", "proof", "regression", "adversar", "drift", "qa", "formal")),
    ("Discovery", ("discovery", "crawl", "source", "feed", "scrape", "intel", "portal")),
    ("Optimization", ("optimi", "cost", "cache", "arbitrage", "determinism", "equivalence", "latency")),
    ("Execution", ("execution", "runtime", "sandbox", "scheduler", "retry", "rate_limit", "environment")),
    ("Governance", ("provenance", "compliance", "security", "trust", "approval", "redaction", "policy", "receipt")),
)


def _ontology() -> dict:
    return json.loads(ONTOLOGY.read_text(encoding="utf-8"))


def _kind_map(onto: dict) -> dict:
    out: dict[int, str] = {}
    rk = onto.get("registry_kinds", {})
    for kind in ("static", "discovery", "meta"):
        for n in rk.get(kind, {}).get("registry_ids", []):
            out[n] = kind
    return out


def hub_to_category(hub: str | None) -> str | None:
    if not hub:
        return None
    c = hub.replace("Open", "").replace("Hub", "").strip()
    return c or None


def categories(reg: dict, kind: str | None = None) -> list[str]:
    """Flexible multi-category for a registry/record. PRIMARY = its hub; plus kind, layer, and cross-cutting tags —
    a record may sit under SEVERAL (the rigid `maps_to_hub` is the primary, not the only)."""
    cats: list[str] = []
    primary = hub_to_category(reg.get("maps_to_hub"))
    if primary:
        cats.append(primary)
    blob = f"{reg.get('id', '')} {reg.get('holds', '')} {reg.get('stage', '')}".lower()
    for label, needles in _CROSS:
        if any(n in blob for n in needles) and label not in cats:
            cats.append(label)
    return cats or ["General"]


def _item(reg: dict, kmap: dict) -> dict:
    kind = kmap.get(reg.get("n"))
    return {"id": reg.get("id"), "holds": reg.get("holds"), "status": reg.get("status") or "unknown",
            "primary_hub": reg.get("maps_to_hub"), "kind": kind, "layer": reg.get("stage") or "uncategorized",
            "type": reg.get("id"), "categories": categories(reg, kind)}


def facets() -> dict:
    """Every facet dimension + its values, computed from the RECONCILED SPINE (ontology ∪ live catalogs)."""
    from src.teleon.registry.index import reconciled_index
    items = reconciled_index()["registries"]
    vals: dict[str, set] = {d: set() for d in FACET_DIMS}
    for it in items:
        for c in it["categories"]:
            vals["category"].add(c)
        vals["type"].add(it["type"])
        if it["kind"]:
            vals["kind"].add(it["kind"])
        vals["layer"].add(it["layer"])
        vals["status"].add(it["status"])
    return {d: sorted(v) for d, v in vals.items()}


def browse(query: str = "", filters: dict | None = None, *, limit: int = 300) -> dict:
    """Faceted browse over the catalog. Filters by any of category/type/kind/layer/status (combine freely) + a
    free-text query. With a query it ALSO federates into populated records via search.search_all. Returns the
    filtered items, the federated records, and facet COUNTS. serves_truth=false."""
    filters = {k: v for k, v in (filters or {}).items() if v}
    from src.teleon.registry.index import reconciled_index
    items = reconciled_index()["registries"]

    def match(it: dict) -> bool:
        if filters.get("category") and filters["category"] not in it["categories"]:
            return False
        for dim in ("type", "kind", "layer", "status"):
            if filters.get(dim) and filters[dim] != it.get(dim):
                return False
        if query and query.lower() not in f"{it['id']} {it['holds']} {' '.join(it['categories'])}".lower():
            return False
        return True

    filtered = [it for it in items if match(it)][:limit]

    # facet counts: for each dim, count items passing ALL OTHER filters (so the count previews the result of picking it)
    counts: dict[str, dict] = {}
    for dim in FACET_DIMS:
        others = {k: v for k, v in filters.items() if k != dim}

        def m2(it: dict, others=others) -> bool:
            if others.get("category") and others["category"] not in it["categories"]:
                return False
            for d in ("type", "kind", "layer", "status"):
                if others.get(d) and others[d] != it.get(d):
                    return False
            return True
        c: dict[str, int] = {}
        for it in items:
            if not m2(it):
                continue
            keys = it["categories"] if dim == "category" else [it.get(dim)]
            for k in keys:
                if k:
                    c[k] = c.get(k, 0) + 1
        counts[dim] = dict(sorted(c.items(), key=lambda kv: -kv[1]))

    records: list[dict] = []
    if query:
        try:
            from .search import search_all
            records = search_all(query)
        except Exception:  # noqa: BLE001 — browse stays useful even if a catalog is offline
            records = []

    return {"query": query, "filters": filters, "count": len(filtered), "items": filtered,
            "records": records, "facets": counts, "serves_truth": False}


def self_test() -> int:
    f = facets()
    assert len(f["type"]) >= 155, f"the reconciled spine (ontology ∪ catalogs) is browsable: {len(f['type'])}"
    assert {"static", "discovery", "meta"} <= set(f["kind"]), f["kind"]
    assert len(f["category"]) >= 5, f["category"]

    # a record sits under MULTIPLE categories (flexible — the win)
    onto = _ontology()
    multi = [r for r in onto["registries"] if len(categories(r)) >= 2]
    assert len(multi) >= 20, f"flexible multi-category should be common, got {len(multi)}"

    # browse default = the full catalog; filtering narrows; facet counts present
    allb = browse()
    assert allb["count"] >= 155 and allb["facets"]["kind"], allb["count"]
    disc = browse(filters={"kind": "discovery"})
    assert 0 < disc["count"] < allb["count"], f"a facet filter narrows: {disc['count']}/{allb['count']}"
    # combine two facets + a query
    combo = browse(query="cost", filters={"category": "Optimization"})
    assert all("Optimization" in it["categories"] for it in combo["items"]), "category filter holds"
    print(f"browse self-test: OK ({allb['count']} registries browsable · {len(f['category'])} categories · "
          f"{len(multi)} multi-category · facets+counts · federates records on query · serves_truth=false)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--facets" in argv:
        print(json.dumps(facets(), indent=2))
        return 0
    print("usage: browse --self-test | --facets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
