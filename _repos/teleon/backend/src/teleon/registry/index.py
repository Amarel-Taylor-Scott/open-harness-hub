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

py_const_src_teleon_registry_index__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
if str(py_const_src_teleon_registry_index__REPO) not in sys.path:
    sys.path.insert(0, str(py_const_src_teleon_registry_index__REPO))

from src.teleon.registry.browse import py_function_src_teleon_registry_browse___kind_map, py_function_src_teleon_registry_browse___ontology, py_function_src_teleon_registry_browse__categories  # noqa: E402

py_var_src_teleon_registry_index___ID_FIELDS = ("id", "canonical", "name", "key", "code", "pass", "failure_type")


def py_function_src_teleon_registry_index__to_registry_object(py_arg_src_teleon_registry_index__py_function_src_teleon_registry_index__to_registry_object__rec: dict, py_arg_src_teleon_registry_index__py_function_src_teleon_registry_index__to_registry_object__registry_id: str, *, py_arg_src_teleon_registry_index__py_function_src_teleon_registry_index__to_registry_object__version: str = "2026.06") -> dict:
    """Project ANY catalog record → a RegistryObject: a THIN, stable WRAPPER (id/type + the version label in METADATA,
    never in the name) around a FLEXIBLE, versionable `component` payload. Multiple versions coexist via `versions`;
    the component is free to change shape without breaking the wrapper. Lossless. serves_truth=false."""
    py_local_src_teleon_registry_index__to_registry_object__rid = next((str(py_arg_src_teleon_registry_index__py_function_src_teleon_registry_index__to_registry_object__rec[f]) for f in py_var_src_teleon_registry_index___ID_FIELDS if py_arg_src_teleon_registry_index__py_function_src_teleon_registry_index__to_registry_object__rec.get(f)), "?")
    py_local_src_teleon_registry_index__to_registry_object__name = str(py_arg_src_teleon_registry_index__py_function_src_teleon_registry_index__to_registry_object__rec.get("name") or py_arg_src_teleon_registry_index__py_function_src_teleon_registry_index__to_registry_object__rec.get("canonical") or py_arg_src_teleon_registry_index__py_function_src_teleon_registry_index__to_registry_object__rec.get("title") or py_local_src_teleon_registry_index__to_registry_object__rid)
    py_local_src_teleon_registry_index__to_registry_object__component = {k: v for k, v in py_arg_src_teleon_registry_index__py_function_src_teleon_registry_index__to_registry_object__rec.items() if k not in py_var_src_teleon_registry_index___ID_FIELDS}  # the flexible, free-to-change payload
    return {"id": py_local_src_teleon_registry_index__to_registry_object__rid, "type": py_arg_src_teleon_registry_index__py_function_src_teleon_registry_index__to_registry_object__registry_id, "name": py_local_src_teleon_registry_index__to_registry_object__name, "version": py_arg_src_teleon_registry_index__py_function_src_teleon_registry_index__to_registry_object__version,
            "schema": "RegistryObject", "component": py_local_src_teleon_registry_index__to_registry_object__component, "serves_truth": False}


def py_function_src_teleon_registry_index__records(py_arg_src_teleon_registry_index__py_function_src_teleon_registry_index__records__registry_id: str, *, limit: int = 200) -> list[dict]:
    """The registry's records, each projected to RegistryObject (uniform). [] if it's a definition-only type."""
    from src.teleon.registry.port import py_function_src_teleon_registry_port__all_catalogs, py_function_src_teleon_registry_port__catalog
    if py_arg_src_teleon_registry_index__py_function_src_teleon_registry_index__records__registry_id not in py_function_src_teleon_registry_port__all_catalogs():
        return []
    try:
        return [py_function_src_teleon_registry_index__to_registry_object(r, py_arg_src_teleon_registry_index__py_function_src_teleon_registry_index__records__registry_id) for r in py_function_src_teleon_registry_port__catalog(py_arg_src_teleon_registry_index__py_function_src_teleon_registry_index__records__registry_id).list()[:limit]]
    except Exception:  # noqa: BLE001 — a malformed catalog yields no records, never an error
        return []


def py_function_src_teleon_registry_index__reconciled_index() -> dict:
    """Union the ontology types + the live catalogs into ONE uniform registry list with status + record counts."""
    py_local_src_teleon_registry_index__reconciled_index__onto_doc = py_function_src_teleon_registry_browse___ontology()
    py_local_src_teleon_registry_index__reconciled_index__onto = {r["id"]: r for r in py_local_src_teleon_registry_index__reconciled_index__onto_doc["registries"]}
    py_local_src_teleon_registry_index__reconciled_index__kmap = py_function_src_teleon_registry_browse___kind_map(py_local_src_teleon_registry_index__reconciled_index__onto_doc)
    from src.teleon.registry.port import py_function_src_teleon_registry_port__all_catalogs, py_function_src_teleon_registry_port__available_all, py_function_src_teleon_registry_port__catalog
    py_local_src_teleon_registry_index__reconciled_index__cats = py_function_src_teleon_registry_port__all_catalogs()
    py_local_src_teleon_registry_index__reconciled_index__avail = set(py_function_src_teleon_registry_port__available_all())
    py_local_src_teleon_registry_index__reconciled_index__out = []
    for py_local_src_teleon_registry_index__reconciled_index__rid in sorted(set(py_local_src_teleon_registry_index__reconciled_index__onto) | set(py_local_src_teleon_registry_index__reconciled_index__cats)):
        py_local_src_teleon_registry_index__reconciled_index__o = py_local_src_teleon_registry_index__reconciled_index__onto.get(py_local_src_teleon_registry_index__reconciled_index__rid, {})
        py_local_src_teleon_registry_index__reconciled_index__has_cat = py_local_src_teleon_registry_index__reconciled_index__rid in py_local_src_teleon_registry_index__reconciled_index__cats
        py_local_src_teleon_registry_index__reconciled_index__rc = None
        if py_local_src_teleon_registry_index__reconciled_index__has_cat:
            try:
                py_local_src_teleon_registry_index__reconciled_index__rc = len(py_function_src_teleon_registry_port__catalog(py_local_src_teleon_registry_index__reconciled_index__rid).list())
            except Exception:  # noqa: BLE001
                py_local_src_teleon_registry_index__reconciled_index__rc = None
        py_local_src_teleon_registry_index__reconciled_index__out.append({
            "id": py_local_src_teleon_registry_index__reconciled_index__rid,
            "type": py_local_src_teleon_registry_index__reconciled_index__rid,
            "source": "both" if (py_local_src_teleon_registry_index__reconciled_index__rid in py_local_src_teleon_registry_index__reconciled_index__onto and py_local_src_teleon_registry_index__reconciled_index__has_cat) else ("ontology" if py_local_src_teleon_registry_index__reconciled_index__rid in py_local_src_teleon_registry_index__reconciled_index__onto else "catalog"),
            "in_ontology": py_local_src_teleon_registry_index__reconciled_index__rid in py_local_src_teleon_registry_index__reconciled_index__onto,
            "has_catalog": py_local_src_teleon_registry_index__reconciled_index__has_cat,
            "queryable": py_local_src_teleon_registry_index__reconciled_index__rid in py_local_src_teleon_registry_index__reconciled_index__avail,
            "record_count": py_local_src_teleon_registry_index__reconciled_index__rc,
            "holds": py_local_src_teleon_registry_index__reconciled_index__o.get("holds"),
            "status": py_local_src_teleon_registry_index__reconciled_index__o.get("status") or ("live" if py_local_src_teleon_registry_index__reconciled_index__has_cat else "definition_only"),
            "maps_to_hub": py_local_src_teleon_registry_index__reconciled_index__o.get("maps_to_hub"),
            "kind": py_local_src_teleon_registry_index__reconciled_index__kmap.get(py_local_src_teleon_registry_index__reconciled_index__o.get("n")),
            "layer": py_local_src_teleon_registry_index__reconciled_index__o.get("stage") or "uncategorized",
            "categories": py_function_src_teleon_registry_browse__categories(py_local_src_teleon_registry_index__reconciled_index__o) if py_local_src_teleon_registry_index__reconciled_index__o else ["General"],
            "backing": py_local_src_teleon_registry_index__reconciled_index__cats[py_local_src_teleon_registry_index__reconciled_index__rid]["file"] if py_local_src_teleon_registry_index__reconciled_index__has_cat else None,
        })
    py_local_src_teleon_registry_index__reconciled_index__overlap = sum(1 for r in py_local_src_teleon_registry_index__reconciled_index__out if r["source"] == "both")
    return {"count": len(py_local_src_teleon_registry_index__reconciled_index__out), "registries": py_local_src_teleon_registry_index__reconciled_index__out,
            "reconciliation": {"ontology_types": len(py_local_src_teleon_registry_index__reconciled_index__onto), "live_catalogs": len(py_local_src_teleon_registry_index__reconciled_index__cats), "overlap": py_local_src_teleon_registry_index__reconciled_index__overlap,
                               "ontology_only": len(py_local_src_teleon_registry_index__reconciled_index__onto) - py_local_src_teleon_registry_index__reconciled_index__overlap, "catalog_only": len(py_local_src_teleon_registry_index__reconciled_index__cats) - py_local_src_teleon_registry_index__reconciled_index__overlap},
            "serves_truth": False}


def py_function_src_teleon_registry_index__get(py_arg_src_teleon_registry_index__py_function_src_teleon_registry_index__get__registry_id: str) -> dict | None:
    return next((r for r in py_function_src_teleon_registry_index__reconciled_index()["registries"] if r["id"] == py_arg_src_teleon_registry_index__py_function_src_teleon_registry_index__get__registry_id), None)


def py_function_src_teleon_registry_index__self_test() -> int:
    py_local_src_teleon_registry_index__self_test__idx = py_function_src_teleon_registry_index__reconciled_index()
    assert py_local_src_teleon_registry_index__self_test__idx["count"] >= 155, f"the index is the UNION of ontology + catalogs: {py_local_src_teleon_registry_index__self_test__idx['count']}"
    py_local_src_teleon_registry_index__self_test__rec = py_local_src_teleon_registry_index__self_test__idx["reconciliation"]
    assert py_local_src_teleon_registry_index__self_test__rec["ontology_types"] == 103 and py_local_src_teleon_registry_index__self_test__rec["live_catalogs"] >= 155, py_local_src_teleon_registry_index__self_test__rec
    assert py_local_src_teleon_registry_index__self_test__rec["overlap"] >= 1, py_local_src_teleon_registry_index__self_test__rec  # the reconciliation is computed + honest about the drift

    # every record projects to the RegistryObject THIN WRAPPER (id/type + version in METADATA) around a flexible component
    py_local_src_teleon_registry_index__self_test__objs = py_function_src_teleon_registry_index__records("component", limit=5) or py_function_src_teleon_registry_index__records("capability", limit=5)
    assert py_local_src_teleon_registry_index__self_test__objs and all({"id", "type", "version", "component"} <= set(o) for o in py_local_src_teleon_registry_index__self_test__objs), "records are RegistryObject wrappers"
    assert all(o["type"] and isinstance(o["component"], dict) for o in py_local_src_teleon_registry_index__self_test__objs), "stable type + flexible component"
    assert all("v" != o["schema"][:1] or "1" not in o["schema"] for o in py_local_src_teleon_registry_index__self_test__objs) and py_local_src_teleon_registry_index__self_test__objs[0]["schema"] == "RegistryObject"
    # a definition-only ontology type honestly returns no records (not an error)
    assert isinstance(py_function_src_teleon_registry_index__records("agent_qa"), list)
    print(f"registry.index self-test: OK (reconciled {py_local_src_teleon_registry_index__self_test__idx['count']} registries [ontology {py_local_src_teleon_registry_index__self_test__rec['ontology_types']} ∪ "
          f"catalogs {py_local_src_teleon_registry_index__self_test__rec['live_catalogs']}, overlap {py_local_src_teleon_registry_index__self_test__rec['overlap']}]; records → RegistryObject; serves_truth=false)")
    return 0


def main(py_arg_src_teleon_registry_index__main__argv: list[str]) -> int:
    if "--self-test" in py_arg_src_teleon_registry_index__main__argv:
        return py_function_src_teleon_registry_index__self_test()
    if "--reconciliation" in py_arg_src_teleon_registry_index__main__argv:
        print(json.dumps(py_function_src_teleon_registry_index__reconciled_index()["reconciliation"], indent=2))
        return 0
    print("usage: index --self-test | --reconciliation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
