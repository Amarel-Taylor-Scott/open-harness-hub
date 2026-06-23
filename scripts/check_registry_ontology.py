"""check_registry_ontology — grounding + ANTI-FRAGMENTATION proof for architecture/registry_ontology.json.

The registry ontology is the registry-of-registries. Two load-bearing invariants:
  1. GROUNDING — a live/partial registry must name backing paths that actually exist on disk (an architecture
     map can never claim a module we don't have). A gap names NO backing.
  2. ANTI-FRAGMENTATION (owner's #1 risk) — with 55+ registries, the shapes must NOT drift apart. So:
       - every entry conforms to ONE rigid schema (schemas/registry/RegistryOntologyEntry.v1.schema.json),
         which is the SINGLE SOURCE for the entry shape — this check reads its `required`/`enum`/`pattern`
         and enforces them (add a field/value = edit the schema, not this check);
       - the universal object shape is a real JSON Schema file (single source for the cross-registry object);
       - the 4 universes form a clean PARTITION over every registry id (each id in exactly one universe).

Also: status/stage from the schema; maps_to_hub (when set) is a real hub in hub_profiles.json; serves_truth=false.
Counts computed, never hand-typed. Deterministic, offline, stdlib only (a tiny JSON-Schema-subset validator).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_ONT = _REPO / "architecture" / "registry_ontology.json"
_PROFILES = _REPO / "architecture" / "hub_profiles.json"

# JSON-Schema-subset type map (stdlib; bool excluded from int/number on purpose).
_TYPES = {"string": str, "integer": int, "number": (int, float), "array": list, "object": dict, "null": type(None)}


def _type_ok(value, spec_type) -> bool:
    types = spec_type if isinstance(spec_type, list) else [spec_type]
    for t in types:
        py = _TYPES.get(t)
        if py is None:
            return True  # unknown type keyword -> don't block
        if t in ("integer", "number") and isinstance(value, bool):
            continue  # bool is not a number here
        if isinstance(value, py):
            return True
    return False


def _validate_against_schema(obj: dict, schema: dict, label: str) -> list[str]:
    """Validate a flat object against the subset of JSON Schema we use: required, additionalProperties,
    properties[*].{type,enum,pattern}. The schema file is the single source of truth for the shape."""
    errs: list[str] = []
    props = schema.get("properties", {})
    for req in schema.get("required", []):
        if req not in obj:
            errs.append(f"{label}: missing required '{req}'")
    if schema.get("additionalProperties") is False:
        for k in obj:
            if k not in props:
                errs.append(f"{label}: unexpected key '{k}' (not in schema)")
    for key, spec in props.items():
        if key not in obj:
            continue
        val = obj[key]
        if "type" in spec and not _type_ok(val, spec["type"]):
            errs.append(f"{label}: '{key}'={val!r} not of type {spec['type']}")
        if "enum" in spec and val not in spec["enum"]:
            errs.append(f"{label}: '{key}'={val!r} not in {spec['enum']}")
        if "pattern" in spec and isinstance(val, str) and not re.search(spec["pattern"], val):
            errs.append(f"{label}: '{key}'={val!r} fails pattern {spec['pattern']}")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true", help="print every failure; exit nonzero on any failure")
    args = ap.parse_args()

    doc = json.loads(_ONT.read_text())
    hubs = set(json.loads(_PROFILES.read_text()).get("profiles", {}))

    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
        if args.self_test and not ok:
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    ck("serves_truth is false", doc.get("serves_truth") is False)
    ck("universal_interface declares verbs", len(doc.get("universal_interface", {}).get("verbs", {})) >= 8)
    ui_contract = doc.get("universal_interface", {}).get("contract", "")
    ck("universal_interface.contract points at a real file (the menu is realized)",
       bool(ui_contract) and (_REPO / ui_contract).exists(), str(ui_contract))
    ck("universal_object declares fields", len(doc.get("universal_object", {}).get("fields", [])) >= 8)

    # the BUFFET / consumption model (demand side): agents pick from registries to build value-add DAGs.
    cm = doc.get("consumption_model", {})
    ck("consumption_model declares a >=4-step flow", len(cm.get("flow", [])) >= 4, str(len(cm.get("flow", []))))
    for p in cm.get("backing", []):
        ck(f"consumption_model backing exists '{p}'", (_REPO / p).exists())

    # the three super-systems (Discovery / Compiler / Intelligence engine) — grounded backing
    for p in doc.get("engines", {}).get("backing", []):
        ck(f"engines backing exists '{p}'", (_REPO / p).exists())

    # ---- anti-fragmentation: the rigid schemas must exist (single sources of truth) ----
    obj_schema_path = doc.get("universal_object", {}).get("schema", "")
    ck("universal_object.schema points at a real file", bool(obj_schema_path) and (_REPO / obj_schema_path).exists(),
       str(obj_schema_path))
    entry_schema_path = doc.get("entry_schema", "")
    ck("entry_schema points at a real file", bool(entry_schema_path) and (_REPO / entry_schema_path).exists(),
       str(entry_schema_path))
    entry_schema = json.loads((_REPO / entry_schema_path).read_text()) if entry_schema_path and (_REPO / entry_schema_path).exists() else {}

    regs = doc.get("registries", [])
    ck(">=30 registries indexed", len(regs) >= 30, str(len(regs)))

    ids: set[str] = set()
    ns: list[int] = []
    for r in regs:
        rid = r.get("id", "?")
        # 1) every entry conforms to the rigid entry schema (single source for the shape)
        for e in _validate_against_schema(r, entry_schema, f"reg#{r.get('n', '?')} '{rid}'"):
            ck(e, False)
        ck(f"{rid}: unique id", rid not in ids, "duplicate")
        ids.add(rid)
        if isinstance(r.get("n"), int):
            ns.append(r["n"])

        # 2) cross-file: maps_to_hub is a real hub (not expressible in the entry schema)
        hub = r.get("maps_to_hub")
        ck(f"{rid}: maps_to_hub is a real hub or null", hub is None or hub in hubs, str(hub))

        # 3) grounding: backing existence depends on status (cross-field, not in the schema)
        backing = r.get("backing", [])
        status = r.get("status")
        if status in {"live", "partial"}:
            ck(f"{rid}: live/partial names >=1 backing path", len(backing) >= 1)
            for p in backing:
                ck(f"{rid}: backing path exists '{p}'", (_REPO / p).exists())
        elif status == "gap":
            ck(f"{rid}: gap names NO backing (stay honest)", len(backing) == 0, str(backing))
        if status in {"partial", "gap"}:
            ck(f"{rid}: partial/gap carries gap_to_close", bool(r.get("gap_to_close")))

    # ---- anti-fragmentation: universes AND kinds must EACH partition every registry by n ----
    def _partition(block: dict) -> list[int]:
        out: list[int] = []
        for v in block.values():
            if isinstance(v, dict) and "registry_ids" in v:
                out.extend(v["registry_ids"])
        return out

    universes = doc.get("universes", {})
    layer_keys = [k for k in universes if k.startswith("layer")]
    ck(">=4 universes declared", len(layer_keys) >= 4, str(layer_keys))
    for blockname, block in (("universes", universes), ("registry_kinds", doc.get("registry_kinds", {}))):
        membership = _partition(block)
        ck(f"{blockname}: membership has no duplicates (disjoint)", len(membership) == len(set(membership)),
           f"{len(membership)} listed, {len(set(membership))} unique")
        ck(f"{blockname}: clean partition over every registry id", set(membership) == set(ns),
           f"missing={sorted(set(ns) - set(membership))} extra={sorted(set(membership) - set(ns))}")

    n_live = sum(1 for r in regs if r.get("status") == "live")
    n_partial = sum(1 for r in regs if r.get("status") == "partial")
    n_gap = sum(1 for r in regs if r.get("status") == "gap")

    if fails:
        print(f"\nFAIL - check_registry_ontology: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_registry_ontology: {len(regs)} registries, schema-conformant + grounded on disk "
          f"({n_live} live + {n_partial} partial + {n_gap} gap), {len(layer_keys)} universes + kinds partition cleanly; "
          f"{checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
