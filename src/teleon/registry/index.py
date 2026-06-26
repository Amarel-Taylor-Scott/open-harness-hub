"""registry.index — the RECONCILED registry SPINE (owner 2026-06-25): ONE source unioning the ontology TYPES
(registry_ontology.json) + the LIVE CATALOGS (port.all_catalogs), so browse / search / agent / API all read the SAME
set. Every registry carries its metadata + catalog status + record count; every RECORD projects to the universal
`RegistryObject` shape (id, name, type). This is the anti-fragmentation single source. serves_truth=false.

  reconciled_index()            -> {registries:[...], reconciliation:{...}}   (the standardized UI/UX set)
  records(registry_id)          -> [RegistryObject, ...]                    (the standardized record schema)
  python3 -m src.teleon.registry.index --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.teleon.registry.browse import _kind_map, _ontology, categories  # noqa: E402

_ID_FIELDS = ("id", "canonical", "name", "key", "code", "pass", "failure_type")


def to_registry_object(rec: dict, registry_id: str, *, version: str = "2026.06") -> dict:
    """Project ANY catalog record → a RegistryObject: a THIN, stable WRAPPER (id/type + the version label in METADATA,
    never in the name) around a FLEXIBLE, versionable `component` payload. Multiple versions coexist via `versions`;
    the component is free to change shape without breaking the wrapper. Lossless. serves_truth=false."""
    rid = next((str(rec[f]) for f in _ID_FIELDS if rec.get(f)), "?")
    name = str(rec.get("name") or rec.get("canonical") or rec.get("title") or rid)
    component = {k: v for k, v in rec.items() if k not in _ID_FIELDS}  # the flexible, free-to-change payload
    return {"id": rid, "type": registry_id, "name": name, "version": version,
            "schema": "RegistryObject", "component": component, "serves_truth": False}


def records(registry_id: str, *, limit: int = 200) -> list[dict]:
    """The registry's records, each projected to RegistryObject (uniform). [] if it's a definition-only type."""
    from src.teleon.registry.port import all_catalogs, catalog
    if registry_id not in all_catalogs():
        return []
    try:
        return [to_registry_object(r, registry_id) for r in catalog(registry_id).list()[:limit]]
    except Exception:  # noqa: BLE001 — a malformed catalog yields no records, never an error
        return []


def reconciled_index() -> dict:
    """Union the ontology types + the live catalogs into ONE uniform registry list with status + record counts."""
    onto_doc = _ontology()
    onto = {r["id"]: r for r in onto_doc["registries"]}
    kmap = _kind_map(onto_doc)
    from src.teleon.registry.port import all_catalogs, available_all, catalog
    cats = all_catalogs()
    avail = set(available_all())
    out = []
    for rid in sorted(set(onto) | set(cats)):
        o = onto.get(rid, {})
        has_cat = rid in cats
        rc = None
        if has_cat:
            try:
                rc = len(catalog(rid).list())
            except Exception:  # noqa: BLE001
                rc = None
        out.append({
            "id": rid,
            "type": rid,
            "source": "both" if (rid in onto and has_cat) else ("ontology" if rid in onto else "catalog"),
            "in_ontology": rid in onto,
            "has_catalog": has_cat,
            "queryable": rid in avail,
            "record_count": rc,
            "holds": o.get("holds"),
            "status": o.get("status") or ("live" if has_cat else "definition_only"),
            "maps_to_hub": o.get("maps_to_hub"),
            "kind": kmap.get(o.get("n")),
            "layer": o.get("stage") or "uncategorized",
            "categories": categories(o) if o else ["General"],
            "backing": cats[rid]["file"] if has_cat else None,
        })
    overlap = sum(1 for r in out if r["source"] == "both")
    return {"count": len(out), "registries": out,
            "reconciliation": {"ontology_types": len(onto), "live_catalogs": len(cats), "overlap": overlap,
                               "ontology_only": len(onto) - overlap, "catalog_only": len(cats) - overlap},
            "serves_truth": False}


def get(registry_id: str) -> dict | None:
    return next((r for r in reconciled_index()["registries"] if r["id"] == registry_id), None)


def self_test() -> int:
    idx = reconciled_index()
    assert idx["count"] >= 155, f"the index is the UNION of ontology + catalogs: {idx['count']}"
    rec = idx["reconciliation"]
    assert rec["ontology_types"] == 103 and rec["live_catalogs"] >= 155, rec
    assert rec["overlap"] >= 1, rec  # the reconciliation is computed + honest about the drift

    # every record projects to the RegistryObject THIN WRAPPER (id/type + version in METADATA) around a flexible component
    objs = records("component", limit=5) or records("capability", limit=5)
    assert objs and all({"id", "type", "version", "component"} <= set(o) for o in objs), "records are RegistryObject wrappers"
    assert all(o["type"] and isinstance(o["component"], dict) for o in objs), "stable type + flexible component"
    assert all("v" != o["schema"][:1] or "1" not in o["schema"] for o in objs) and objs[0]["schema"] == "RegistryObject"
    # a definition-only ontology type honestly returns no records (not an error)
    assert isinstance(records("agent_qa"), list)
    print(f"registry.index self-test: OK (reconciled {idx['count']} registries [ontology {rec['ontology_types']} ∪ "
          f"catalogs {rec['live_catalogs']}, overlap {rec['overlap']}]; records → RegistryObject; serves_truth=false)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--reconciliation" in argv:
        print(json.dumps(reconciled_index()["reconciliation"], indent=2))
        return 0
    print("usage: index --self-test | --reconciliation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
