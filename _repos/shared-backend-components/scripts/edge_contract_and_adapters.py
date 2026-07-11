#!/usr/bin/env python3
"""edge_contract_and_adapters — a minimal PortContract + the restricted, PROVED adapter DSL (review Phase 1).

The compatibility lattice grades edge names; the external review's Phase 1 says a name is not a contract —
compatibility must be decided over STRUCTURE (fields, types, units, required/optional), and an "adapter" must
be a first-class, directional, CLASSIFIED transform proved like any implementation. This is the bounded seed of
that: a `PortContract` (a set of typed, optionally unit-bearing, required/optional fields) + a restricted
deterministic adapter DSL whose operators are each classified so that only TOTAL + LOSSLESS adapters may
auto-authorize a join; partial ones return a typed error, lossy ones require explicit opt-in, and a missing
REQUIRED value is NEVER fabricated to satisfy a schema.

Structural compatibility is directional WIDTH subtyping: a producer contract P satisfies a consumer contract C
iff P guarantees every field C requires, with a compatible (equal-or-widening) type + matching unit. Extra
producer fields are fine (width); a missing required field is INCOMPATIBLE, never defaulted.

    PYTHONPATH=. python3 scripts/edge_contract_and_adapters.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  the ONE id authority (data plane law)
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"edge_contract_and_adapters requires canonical_id; import failed: {exc}")

ADAPTER_ID_PREFIX = "padpt"
#: type widening lattice: value on the left is accepted where the right is required (int fits where float is
#: wanted; a narrower numeric fits a wider one). Directional — never the reverse (float does NOT fit int).
_WIDENS_TO: dict[str, set[str]] = {"int": {"int", "float", "number"}, "float": {"float", "number"},
                                   "number": {"number"}, "str": {"str"}, "bool": {"bool", "int", "number"}}
#: adapter operator classifications (review §5.5). Only `total_lossless` may auto-authorize.
ADAPTER_CLASSES = ("total_lossless", "total_lossy", "partial_guarded", "stateful")


def _widens(src_type: str, dst_type: str) -> bool:
    return dst_type in _WIDENS_TO.get(src_type, {src_type}) or src_type == dst_type


def structural_compatible(producer: dict[str, Any], consumer: dict[str, Any]) -> dict[str, Any]:
    """Directional WIDTH subtyping: does `producer` guarantee everything `consumer` requires (compatible type +
    unit)? Returns {compatible, grade, missing, type_mismatches, unit_mismatches, extra}. A missing REQUIRED
    field or a type/unit mismatch is INCOMPATIBLE — never defaulted."""
    p_fields = producer.get("fields", {})
    c_fields = consumer.get("fields", {})
    missing, type_bad, unit_bad = [], [], []
    for name, spec in c_fields.items():
        if not spec.get("required", True):
            continue   # consumer optional field — producer need not supply it
        if name not in p_fields:
            missing.append(name)
            continue
        p_spec = p_fields[name]
        if not _widens(str(p_spec.get("type", "any")), str(spec.get("type", "any"))):
            type_bad.append({"field": name, "producer": p_spec.get("type"), "consumer": spec.get("type")})
        if spec.get("unit") and p_spec.get("unit") != spec.get("unit"):
            unit_bad.append({"field": name, "producer": p_spec.get("unit"), "consumer": spec.get("unit")})
    extra = sorted(set(p_fields) - set(c_fields))
    compatible = not (missing or type_bad or unit_bad)
    if compatible:
        grade = "SAFE_STRUCTURAL" if extra else "IDENTICAL_SHAPE"
    else:
        grade = "INCOMPATIBLE"
    return {"compatible": compatible, "grade": grade, "missing_required": sorted(missing),
            "type_mismatches": type_bad, "unit_mismatches": unit_bad, "extra_producer_fields": extra,
            "direction": "producer->consumer", "candidate": True, "serves_truth": False}


# ── the restricted adapter DSL. Each op declares its classification; the adapter's class is the WORST op. ─────
def _op_rename(payload: dict, params: dict) -> dict:
    out = dict(payload)
    for old, new in params.get("map", {}).items():
        if old in out:
            out[new] = out.pop(old)
    return out


def _op_project(payload: dict, params: dict) -> dict:
    keep = set(params.get("keep", []))
    return {k: v for k, v in payload.items() if k in keep}


def _op_widen(payload: dict, params: dict) -> dict:
    out = dict(payload)
    for field, target in params.get("to", {}).items():
        if field in out and target in ("float", "number") and isinstance(out[field], int):
            out[field] = float(out[field])
    return out


def _op_unit_convert(payload: dict, params: dict) -> dict:
    out = dict(payload)
    for field, factor in params.get("factor", {}).items():
        if field in out and isinstance(out[field], (int, float)):
            out[field] = out[field] * factor
    return out


def _op_enum_map(payload: dict, params: dict) -> tuple[dict, bool]:
    """Total ONLY if the mapping covers every observed value; otherwise a partial (guarded) failure — an
    unmapped value is a typed error, never silently passed or defaulted."""
    out = dict(payload)
    field, mapping = params.get("field"), params.get("map", {})
    ok = True
    if field in out:
        if out[field] in mapping:
            out[field] = mapping[out[field]]
        else:
            ok = False
    return out, ok


#: op registry: name -> (apply, class). `project` is total_lossy (drops fields); `enum_map` is partial_guarded.
_OPS: dict[str, dict[str, Any]] = {
    "rename": {"apply": _op_rename, "class": "total_lossless"},
    "widen": {"apply": _op_widen, "class": "total_lossless"},
    "unit_convert": {"apply": _op_unit_convert, "class": "total_lossless"},
    "project": {"apply": _op_project, "class": "total_lossy"},
    "enum_map": {"apply": _op_enum_map, "class": "partial_guarded"},
}
_CLASS_RANK = {"total_lossless": 0, "total_lossy": 1, "partial_guarded": 2, "stateful": 3}


def build_adapter(source_edge: str, target_edge: str, ops: list[dict[str, Any]]) -> dict[str, Any]:
    """A directional adapter = an ordered op list. Its class is the WORST op's class. Only total_lossless
    adapters may auto-authorize (they map VERIFIED_ADAPTER in the lattice); worse classes are policy-gated."""
    for op in ops:
        if op.get("op") not in _OPS:
            raise ValueError(f"unknown adapter op {op.get('op')!r}; known: {sorted(_OPS)}")
    worst = max((_OPS[op["op"]]["class"] for op in ops), key=lambda c: _CLASS_RANK[c], default="total_lossless")
    return {"adapter_id": canonical_id(ADAPTER_ID_PREFIX, source_edge, target_edge, json.dumps(ops, sort_keys=True)),
            "record_type": "edge_adapter", "source_edge": source_edge, "target_edge": target_edge,
            "ops": ops, "classification": worst,
            "auto_authorizes": worst == "total_lossless",
            "note": "only total_lossless adapters auto-authorize (VERIFIED_ADAPTER); partial ops return a typed "
                    "error; lossy ops require explicit opt-in; a missing required value is never fabricated",
            "candidate": True, "serves_truth": False}


def apply_adapter(adapter: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Run the adapter deterministically. Returns {ok, result, error}. A partial op that cannot map a value
    fails with a typed error (never a fabricated or silently-dropped value)."""
    out = dict(payload)
    for op in adapter["ops"]:
        spec = _OPS[op["op"]]
        if op["op"] == "enum_map":
            out, ok = spec["apply"](out, op)
            if not ok:
                return {"ok": False, "result": None,
                        "error": {"type": "unmapped_enum_value", "op": op, "field": op.get("field")},
                        "candidate": True, "serves_truth": False}
        else:
            out = spec["apply"](out, op)
    return {"ok": True, "result": out, "candidate": True, "serves_truth": False}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    # (1) WIDTH SUBTYPING: a producer with an EXTRA field still satisfies a consumer -> SAFE_STRUCTURAL.
    producer = {"fields": {"name": {"type": "str"}, "age": {"type": "int"}, "extra": {"type": "str"}}}
    consumer = {"fields": {"name": {"type": "str", "required": True}, "age": {"type": "int", "required": True}}}
    sub = structural_compatible(producer, consumer)
    checks.append(("width subtyping: producer with an extra field satisfies the consumer (SAFE_STRUCTURAL); "
                   "extra fields are fine, missing required ones are not",
                   sub["compatible"] and sub["grade"] == "SAFE_STRUCTURAL" and sub["extra_producer_fields"] == ["extra"],
                   json.dumps(sub)[:120]))

    # (2) a MISSING REQUIRED field is INCOMPATIBLE — never defaulted.
    missing = structural_compatible({"fields": {"name": {"type": "str"}}}, consumer)
    checks.append(("a missing REQUIRED field is INCOMPATIBLE (never fabricated to satisfy the schema)",
                   not missing["compatible"] and missing["grade"] == "INCOMPATIBLE"
                   and missing["missing_required"] == ["age"], ""))

    # (3) NUMERIC WIDENING is directional: int fits where float is wanted, not the reverse.
    int_to_float = structural_compatible({"fields": {"x": {"type": "int"}}},
                                         {"fields": {"x": {"type": "float", "required": True}}})
    float_to_int = structural_compatible({"fields": {"x": {"type": "float"}}},
                                         {"fields": {"x": {"type": "int", "required": True}}})
    checks.append(("numeric widening is directional: int->float compatible; float->int is NOT",
                   int_to_float["compatible"] and not float_to_int["compatible"], ""))

    # (4) UNIT MISMATCH is caught: same type, different unit -> INCOMPATIBLE (the same-shape-different-unit trap).
    unit_bad = structural_compatible({"fields": {"d": {"type": "float", "unit": "miles"}}},
                                     {"fields": {"d": {"type": "float", "unit": "km", "required": True}}})
    checks.append(("a UNIT mismatch (miles vs km) is INCOMPATIBLE even with matching type — the "
                   "same-shape-different-unit adversarial case",
                   not unit_bad["compatible"] and unit_bad["unit_mismatches"], ""))

    # (5) adapter DSL: rename + widen is TOTAL_LOSSLESS -> auto-authorizes; applies deterministically.
    adapter = build_adapter("SrcRowBatch", "DstRowBatch",
                            [{"op": "rename", "map": {"full_name": "name"}}, {"op": "widen", "to": {"age": "float"}}])
    applied = apply_adapter(adapter, {"full_name": "Ada", "age": 37})
    checks.append(("adapter DSL: rename+widen is total_lossless (auto-authorizes) and applies deterministically",
                   adapter["classification"] == "total_lossless" and adapter["auto_authorizes"] is True
                   and applied["ok"] and applied["result"] == {"name": "Ada", "age": 37.0}, ""))

    # (6) a PROJECT adapter (drops a field) is total_LOSSY -> does NOT auto-authorize (opt-in required).
    lossy = build_adapter("A", "B", [{"op": "project", "keep": ["name"]}])
    checks.append(("a projecting adapter is total_lossy and does NOT auto-authorize (dropping info needs opt-in)",
                   lossy["classification"] == "total_lossy" and lossy["auto_authorizes"] is False, ""))

    # (7) a PARTIAL enum_map returns a TYPED ERROR on an unmapped value — never a fabricated/silent result.
    enum_adapter = build_adapter("A", "B", [{"op": "enum_map", "field": "status", "map": {"A": "active"}}])
    ok_case = apply_adapter(enum_adapter, {"status": "A"})
    bad_case = apply_adapter(enum_adapter, {"status": "Z"})
    checks.append(("a partial enum_map maps a covered value but returns a TYPED ERROR on an uncovered one "
                   "(never fabricates); adapter classified partial_guarded",
                   enum_adapter["classification"] == "partial_guarded"
                   and ok_case["ok"] and ok_case["result"]["status"] == "active"
                   and bad_case["ok"] is False and bad_case["error"]["type"] == "unmapped_enum_value", ""))

    # (8) unit conversion adapter is total_lossless with a declared factor (deterministic).
    conv = build_adapter("A", "B", [{"op": "unit_convert", "factor": {"d": 1.60934}}])
    conv_applied = apply_adapter(conv, {"d": 10})
    checks.append(("unit_convert is total_lossless with a declared factor; deterministic value transform",
                   conv["auto_authorizes"] and abs(conv_applied["result"]["d"] - 16.0934) < 1e-6, ""))

    # (9) determinism + candidate-only.
    a = json.dumps(build_adapter("A", "B", [{"op": "rename", "map": {"x": "y"}}]), sort_keys=True)
    b = json.dumps(build_adapter("A", "B", [{"op": "rename", "map": {"x": "y"}}]), sort_keys=True)
    checks.append(("deterministic adapter ids + candidate-only", a == b and adapter["serves_truth"] is False, ""))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - edge_contract_and_adapters: PortContract width-subtyping + a restricted "
          f"PROVED adapter DSL (review Phase 1) — structural compatibility is directional (int->float yes, "
          f"float->int no; unit mismatch caught; missing-required never defaulted); only total_lossless adapters "
          f"auto-authorize, partial ops return typed errors, lossy ops need opt-in. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PortContract width-subtyping + the restricted adapter DSL.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
