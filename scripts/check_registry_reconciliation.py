#!/usr/bin/env python3
"""scripts.check_registry_reconciliation — the ANTI-FRAGMENTATION contract (owner 2026-06-25).

The registry SPINE (`src/teleon/registry/index.reconciled_index`) unions the ontology TYPES + the live CATALOGS into
ONE set, and every record projects to `RegistryObject` — so the visual browse, the search, the agentic RegistryPort,
and the REST API all read the SAME registries with the SAME record shape. This proves the spine computes + the
projection conforms; `--check` prints the ontology↔catalog drift so it can never silently diverge. serves_truth=false.

  --self-test
  --check
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def self_test() -> int:
    from src.teleon.registry.index import records, reconciled_index, to_registry_object
    idx = reconciled_index()
    assert idx["count"] >= 155, idx["count"]
    r = idx["reconciliation"]
    assert r["ontology_types"] == 103 and r["live_catalogs"] >= 155 and r["overlap"] >= 1, r
    # RegistryObject = thin WRAPPER (id/type, version in METADATA, no v-in-name) + flexible `component` (lossless)
    o = to_registry_object({"id": "x", "name": "X", "foo": 1}, "demo")
    assert {"id", "type", "version", "component"} <= set(o) and o["type"] == "demo" and o["component"]["foo"] == 1
    assert o["schema"] == "RegistryObject", "no version in the schema name (version is metadata)"
    objs = records("component", limit=3) or records("capability", limit=3)
    assert objs and all({"id", "type", "component"} <= set(x) for x in objs), "records are RegistryObject wrappers"
    assert isinstance(records("agent_qa"), list)   # a definition-only type → honest [] (not an error)
    print(f"check_registry_reconciliation: OK (ONE spine of {idx['count']} registries [ontology {r['ontology_types']} ∪ "
          f"catalogs {r['live_catalogs']}, overlap {r['overlap']}]; records → RegistryObject; serves_truth=false)")
    return 0


def check() -> int:
    from src.teleon.registry.index import reconciled_index
    idx = reconciled_index()
    r = idx["reconciliation"]
    print(f"registry reconciliation — ONE spine of {idx['count']} registries:")
    print(f"  ontology types {r['ontology_types']}  ·  live catalogs {r['live_catalogs']}  ·  overlap {r['overlap']}")
    print(f"  ontology-only (definition, no live catalog): {r['ontology_only']}")
    print(f"  catalog-only  (queryable, not yet in the ontology): {r['catalog_only']}")
    print("  → close the gap over time: map each live catalog to an ontology type (or add the type).")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--check" in argv:
        return check()
    print("usage: check_registry_reconciliation.py --self-test | --check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
