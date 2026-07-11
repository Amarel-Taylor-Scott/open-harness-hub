#!/usr/bin/env python3
"""scripts.prove_leaves_dict_mapping — WORKABLE (proven + TYPED) deterministic leaf primitives for 'dict_mapping'.

The proven-primitive substrate (`_repos/shared-backend-components/scripts/mutator_registry.py` — real executable mutators + `run_primitive_proof()`
that flips serves_truth false->true ONLY on a PASSING executed proof) is the gate. This module is an ADD-ONLY parallel
path: it declares >=28 REAL pure deterministic Record->Record leaf primitives for the dict_mapping family
(pick/project · omit · invert · deep_get · merge-with-defaults · rename-keys · flatten-keys · unflatten-keys ·
filter-values · map-values · map-keys · prefix ops · coalesce · pairs<->items · deep_merge/deep_set · swap), plugs the
new pure mutators INTO the shared MUTATOR_REGISTRY via setdefault (registration, never a rewrite), runs EVERY leaf
through the IMPORTED `run_primitive_proof`, keeps ONLY passers, and — the fix for 'proven but untyped' — TYPES every
persisted row via `canonicalize_edge` (input_edge_type_id + output_edge_type_id) so a workable leaf can chain.

serves_truth=true here is CORRECT + required: it is set ONLY by an executed passing proof — a deliberately-wrong leaf
and an un-runnable fixture stay candidate and are never persisted. Roundtrip-inverse pairs (invert·self,
flatten<->unflatten, items_to_pairs<->pairs_to_items) are proven reversible via has_inverse. Offline + deterministic:
no network, no LLM, no wall-clock (fixed literal timestamp), no RNG. CLI: --self-test | --write.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the existing machinery — never edit it (ADD-ONLY / contract-locked files stay untouched).
from scripts.mutator_registry import (  # noqa: E402
    INVERSE_PAIRS,
    MUTATOR_REGISTRY,
    _receipt,
    run_primitive_proof,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

FAMILY = "dict_mapping"
# fixed literal timestamp — NO wall-clock (repo law: deterministic + offline).
GENERATED_UTC = "2026-07-03T00:00:00Z"

OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_dict_mapping.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_dict_mapping.json"


# ── PURE deterministic dict_mapping mutators. Each: (payload, **kwargs) -> (transformed_output, receipt_dict). ──
def dm_pick(record: dict[str, Any], keep: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {k: record[k] for k in keep if k in record}
    return out, _receipt("dm_pick", before=record, after=out, lossless=False, note=f"project to {keep}")


def dm_omit(record: dict[str, Any], drop: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {k: v for k, v in record.items() if k not in set(drop)}
    return out, _receipt("dm_omit", before=record, after=out, lossless=False, note=f"omit {drop}")


def dm_invert(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {v: k for k, v in record.items()}
    return out, _receipt("dm_invert", before=record, after=out, lossless=True, note="swap keys/values (self-inverse when bijective)")


def dm_deep_get(record: dict[str, Any], path: str, default: Any = None, sep: str = ".") -> tuple[Any, dict[str, Any]]:
    node: Any = record
    for part in str(path).split(sep):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            node = default
            break
    return node, _receipt("dm_deep_get", before=record, after=node, lossless=False, note=f"deep get {path!r}")


def dm_deep_set(record: dict[str, Any], path: str, value: Any, sep: str = ".") -> tuple[dict[str, Any], dict[str, Any]]:
    parts = str(path).split(sep)
    out = json.loads(json.dumps(record))  # deep copy of JSON-shaped data (deterministic)
    node = out
    for part in parts[:-1]:
        nxt = node.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            node[part] = nxt
        node = nxt
    node[parts[-1]] = value
    return out, _receipt("dm_deep_set", before=record, after=out, lossless=False, note=f"deep set {path!r}")


def dm_merge_defaults(record: dict[str, Any], defaults: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {**defaults, **record}
    return out, _receipt("dm_merge_defaults", before=record, after=out, lossless=True, note="fill missing keys from defaults")


def dm_deep_merge(record: dict[str, Any], other: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    def _merge(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
        out = dict(a)
        for k, v in b.items():
            if isinstance(out.get(k), dict) and isinstance(v, dict):
                out[k] = _merge(out[k], v)
            else:
                out[k] = v
        return out
    out = _merge(record, other)
    return out, _receipt("dm_deep_merge", before=record, after=out, lossless=True, note="recursive merge (other wins on leaf conflict)")


def dm_rename_keys(record: dict[str, Any], mapping: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {mapping.get(k, k): v for k, v in record.items()}
    return out, _receipt("dm_rename_keys", before=record, after=out, lossless=False, note=f"rename {list(mapping)}")


def dm_flatten_keys(record: dict[str, Any], sep: str = ".") -> tuple[dict[str, Any], dict[str, Any]]:
    def _flat(d: dict[str, Any], prefix: str) -> dict[str, Any]:
        items: dict[str, Any] = {}
        for k, v in d.items():
            nk = f"{prefix}{sep}{k}" if prefix else str(k)
            if isinstance(v, dict) and v:
                items.update(_flat(v, nk))
            else:
                items[nk] = v
        return items
    out = _flat(record, "")
    return out, _receipt("dm_flatten_keys", before=record, after=out, lossless=True, note="nested->dotted flat keys; dm_unflatten_keys restores")


def dm_unflatten_keys(record: dict[str, Any], sep: str = ".") -> tuple[dict[str, Any], dict[str, Any]]:
    out: dict[str, Any] = {}
    for k, v in record.items():
        parts = str(k).split(sep)
        node = out
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = v
    return out, _receipt("dm_unflatten_keys", before=record, after=out, lossless=True, note="dotted flat->nested keys")


def dm_filter_values(record: dict[str, Any], mode: str = "drop_none") -> tuple[dict[str, Any], dict[str, Any]]:
    if mode == "drop_none":
        out = {k: v for k, v in record.items() if v is not None}
    elif mode == "drop_falsy":
        out = {k: v for k, v in record.items() if v}
    else:
        raise ValueError(f"unknown filter mode: {mode}")
    return out, _receipt("dm_filter_values", before=record, after=out, lossless=False, note=f"filter values ({mode})")


def dm_map_values(record: dict[str, Any], op: str = "str") -> tuple[dict[str, Any], dict[str, Any]]:
    ops = {"str": str, "int": int, "upper": lambda x: x.upper(), "lower": lambda x: x.lower(),
           "negate": lambda x: -x}
    fn = ops[op]
    out = {k: fn(v) for k, v in record.items()}
    return out, _receipt("dm_map_values", before=record, after=out, lossless=False, note=f"map values ({op})")


def dm_map_keys(record: dict[str, Any], op: str = "upper") -> tuple[dict[str, Any], dict[str, Any]]:
    ops = {"upper": str.upper, "lower": str.lower}
    fn = ops[op]
    out = {fn(str(k)): v for k, v in record.items()}
    return out, _receipt("dm_map_keys", before=record, after=out, lossless=False, note=f"map keys ({op})")


def dm_filter_keys(record: dict[str, Any], prefix: str = "") -> tuple[dict[str, Any], dict[str, Any]]:
    out = {k: v for k, v in record.items() if str(k).startswith(prefix)}
    return out, _receipt("dm_filter_keys", before=record, after=out, lossless=False, note=f"keep keys with prefix {prefix!r}")


def dm_add_prefix(record: dict[str, Any], prefix: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {f"{prefix}{k}": v for k, v in record.items()}
    return out, _receipt("dm_add_prefix", before=record, after=out, lossless=True, note=f"prefix keys with {prefix!r}")


def dm_strip_prefix(record: dict[str, Any], prefix: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {(k[len(prefix):] if str(k).startswith(prefix) else k): v for k, v in record.items()}
    return out, _receipt("dm_strip_prefix", before=record, after=out, lossless=False, note=f"strip key prefix {prefix!r}")


def dm_sort_by_key(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {k: record[k] for k in sorted(record)}
    return out, _receipt("dm_sort_by_key", before=record, after=out, lossless=True, note="canonical key-sorted record")


def dm_items_to_pairs(record: dict[str, Any]) -> tuple[list[list[Any]], dict[str, Any]]:
    out = [[k, record[k]] for k in sorted(record)]
    return out, _receipt("dm_items_to_pairs", before=record, after=out, lossless=True, note="dict->sorted [k,v] pairs; dm_pairs_to_items restores")


def dm_pairs_to_items(pairs: list[list[Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {k: v for k, v in pairs}
    return out, _receipt("dm_pairs_to_items", before=pairs, after=out, lossless=True, note="[k,v] pairs->dict")


def dm_coalesce(record: dict[str, Any], keys: list[str]) -> tuple[Any, dict[str, Any]]:
    val: Any = None
    for k in keys:
        if record.get(k) is not None:
            val = record[k]
            break
    return val, _receipt("dm_coalesce", before=record, after=val, lossless=False, note=f"first non-null of {keys}")


def dm_keys_list(record: dict[str, Any]) -> tuple[list[Any], dict[str, Any]]:
    out = sorted(record.keys())
    return out, _receipt("dm_keys_list", before=record, after=out, lossless=False, note="sorted key list")


def dm_values_list(record: dict[str, Any]) -> tuple[list[Any], dict[str, Any]]:
    out = [record[k] for k in sorted(record)]
    return out, _receipt("dm_values_list", before=record, after=out, lossless=False, note="values ordered by sorted key")


def dm_count_keys(record: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    out = len(record)
    return out, _receipt("dm_count_keys", before=record, after=out, lossless=False, note="key count")


def dm_select_rename(record: dict[str, Any], keep: list[str], mapping: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    projected = {k: record[k] for k in keep if k in record}
    out = {mapping.get(k, k): v for k, v in projected.items()}
    return out, _receipt("dm_select_rename", before=record, after=out, lossless=False, note=f"project {keep} then rename {list(mapping)}")


def dm_defaults_strip_none(record: dict[str, Any], defaults: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    merged = {**defaults, **record}
    out = {k: v for k, v in merged.items() if v is not None}
    return out, _receipt("dm_defaults_strip_none", before=record, after=out, lossless=False, note="merge defaults then drop nulls")


def dm_swap_keys(record: dict[str, Any], a: str, b: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = dict(record)
    if a in out and b in out:
        out[a], out[b] = out[b], out[a]
    return out, _receipt("dm_swap_keys", before=record, after=out, lossless=True, note=f"swap values of {a!r} and {b!r}")


#: new pure mutators to plug into the shared registry (idempotent setdefault registration; never overwrites existing).
_NEW_MUTATORS = {
    "dm_pick": dm_pick, "dm_omit": dm_omit, "dm_invert": dm_invert, "dm_deep_get": dm_deep_get,
    "dm_deep_set": dm_deep_set, "dm_merge_defaults": dm_merge_defaults, "dm_deep_merge": dm_deep_merge,
    "dm_rename_keys": dm_rename_keys, "dm_flatten_keys": dm_flatten_keys, "dm_unflatten_keys": dm_unflatten_keys,
    "dm_filter_values": dm_filter_values, "dm_map_values": dm_map_values, "dm_map_keys": dm_map_keys,
    "dm_filter_keys": dm_filter_keys, "dm_add_prefix": dm_add_prefix, "dm_strip_prefix": dm_strip_prefix,
    "dm_sort_by_key": dm_sort_by_key, "dm_items_to_pairs": dm_items_to_pairs, "dm_pairs_to_items": dm_pairs_to_items,
    "dm_coalesce": dm_coalesce, "dm_keys_list": dm_keys_list, "dm_values_list": dm_values_list,
    "dm_count_keys": dm_count_keys, "dm_select_rename": dm_select_rename,
    "dm_defaults_strip_none": dm_defaults_strip_none, "dm_swap_keys": dm_swap_keys,
}
_NEW_INVERSE_PAIRS = [
    ("dm_invert", "dm_invert"),
    ("dm_flatten_keys", "dm_unflatten_keys"),
    ("dm_items_to_pairs", "dm_pairs_to_items"),
]


def register_new_mutators() -> None:
    """Plug the dict_mapping mutators into the shared MUTATOR_REGISTRY (registration, not a rewrite). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)
    for pair in _NEW_INVERSE_PAIRS:
        if pair not in INVERSE_PAIRS:
            INVERSE_PAIRS.append(pair)


register_new_mutators()


# ── the leaf primitives: each a REAL Record-mapping capability with a concrete fixture + expected output ──
# spec fields: id, capability, mutator, fixture, expected, args, inverse, input_edge, output_edge
LEAF_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:dm_pick", "capability": "project a record down to a keep-list", "mutator": "dm_pick",
     "fixture": {"a": 1, "b": 2, "c": 3}, "expected": {"a": 1, "c": 3}, "args": {"keep": ["a", "c"]},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_omit", "capability": "drop a set of keys from a record", "mutator": "dm_omit",
     "fixture": {"a": 1, "b": 2, "c": 3}, "expected": {"a": 1, "c": 3}, "args": {"drop": ["b"]},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_invert", "capability": "invert a bijective record (roundtrips via itself)", "mutator": "dm_invert",
     "fixture": {"a": "x", "b": "y"}, "expected": {"x": "a", "y": "b"}, "args": {}, "inverse": "dm_invert",
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_deep_get", "capability": "read a nested value by dotted path", "mutator": "dm_deep_get",
     "fixture": {"a": {"b": {"c": 7}}}, "expected": 7, "args": {"path": "a.b.c"},
     "input_edge": "Record", "output_edge": "Scalar"},
    {"id": "prim:leaf:dm_deep_get_default", "capability": "deep get returns default on a missing path", "mutator": "dm_deep_get",
     "fixture": {"a": {"b": 1}}, "expected": 0, "args": {"path": "a.z", "default": 0},
     "input_edge": "Record", "output_edge": "Scalar"},
    {"id": "prim:leaf:dm_deep_set", "capability": "set a nested value by dotted path", "mutator": "dm_deep_set",
     "fixture": {"a": {"b": 1}}, "expected": {"a": {"b": 1, "c": 9}}, "args": {"path": "a.c", "value": 9},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_merge_defaults", "capability": "fill missing fields from defaults", "mutator": "dm_merge_defaults",
     "fixture": {"a": 1}, "expected": {"a": 1, "b": 2}, "args": {"defaults": {"a": 0, "b": 2}},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_deep_merge", "capability": "recursively merge two nested records", "mutator": "dm_deep_merge",
     "fixture": {"a": {"b": 1}, "x": 1}, "expected": {"a": {"b": 1, "c": 2}, "x": 1, "y": 2},
     "args": {"other": {"a": {"c": 2}, "y": 2}}, "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_rename_keys", "capability": "rename record keys by mapping", "mutator": "dm_rename_keys",
     "fixture": {"a": 1, "b": 2}, "expected": {"x": 1, "b": 2}, "args": {"mapping": {"a": "x"}},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_flatten_keys", "capability": "flatten nested keys to dotted keys (roundtrips)", "mutator": "dm_flatten_keys",
     "fixture": {"a": {"b": 1, "c": 2}, "d": 3}, "expected": {"a.b": 1, "a.c": 2, "d": 3}, "args": {},
     "inverse": "dm_unflatten_keys", "input_edge": "NestedRecord", "output_edge": "FlatRecord"},
    {"id": "prim:leaf:dm_unflatten_keys", "capability": "rebuild nested keys from dotted keys", "mutator": "dm_unflatten_keys",
     "fixture": {"a.b": 1, "a.c": 2, "d": 3}, "expected": {"a": {"b": 1, "c": 2}, "d": 3}, "args": {},
     "input_edge": "FlatRecord", "output_edge": "NestedRecord"},
    {"id": "prim:leaf:dm_filter_values_drop_none", "capability": "drop null-valued entries", "mutator": "dm_filter_values",
     "fixture": {"a": 1, "b": None, "c": 3}, "expected": {"a": 1, "c": 3}, "args": {"mode": "drop_none"},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_filter_values_drop_falsy", "capability": "drop falsy-valued entries", "mutator": "dm_filter_values",
     "fixture": {"a": 1, "b": 0, "c": "", "d": "x"}, "expected": {"a": 1, "d": "x"}, "args": {"mode": "drop_falsy"},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_map_values_str", "capability": "stringify every value", "mutator": "dm_map_values",
     "fixture": {"a": 1, "b": 2}, "expected": {"a": "1", "b": "2"}, "args": {"op": "str"},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_map_values_upper", "capability": "uppercase every string value", "mutator": "dm_map_values",
     "fixture": {"a": "x", "b": "y"}, "expected": {"a": "X", "b": "Y"}, "args": {"op": "upper"},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_map_values_negate", "capability": "negate every numeric value", "mutator": "dm_map_values",
     "fixture": {"a": 1, "b": -2}, "expected": {"a": -1, "b": 2}, "args": {"op": "negate"},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_map_keys_upper", "capability": "uppercase every key", "mutator": "dm_map_keys",
     "fixture": {"a": 1, "b": 2}, "expected": {"A": 1, "B": 2}, "args": {"op": "upper"},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_map_keys_lower", "capability": "lowercase every key", "mutator": "dm_map_keys",
     "fixture": {"A": 1, "B": 2}, "expected": {"a": 1, "b": 2}, "args": {"op": "lower"},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_filter_keys_prefix", "capability": "keep only keys with a prefix", "mutator": "dm_filter_keys",
     "fixture": {"x_a": 1, "x_b": 2, "y_c": 3}, "expected": {"x_a": 1, "x_b": 2}, "args": {"prefix": "x_"},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_add_prefix", "capability": "prefix every key", "mutator": "dm_add_prefix",
     "fixture": {"a": 1, "b": 2}, "expected": {"p_a": 1, "p_b": 2}, "args": {"prefix": "p_"},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_strip_prefix", "capability": "strip a prefix from every key", "mutator": "dm_strip_prefix",
     "fixture": {"p_a": 1, "p_b": 2}, "expected": {"a": 1, "b": 2}, "args": {"prefix": "p_"},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_sort_by_key", "capability": "canonicalize a record to key-sorted order", "mutator": "dm_sort_by_key",
     "fixture": {"b": 2, "a": 1, "c": 3}, "expected": {"a": 1, "b": 2, "c": 3}, "args": {},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_items_to_pairs", "capability": "explode a record to sorted [k,v] pairs (roundtrips)", "mutator": "dm_items_to_pairs",
     "fixture": {"b": 2, "a": 1}, "expected": [["a", 1], ["b", 2]], "args": {}, "inverse": "dm_pairs_to_items",
     "input_edge": "Record", "output_edge": "PairList"},
    {"id": "prim:leaf:dm_pairs_to_items", "capability": "collapse [k,v] pairs into a record", "mutator": "dm_pairs_to_items",
     "fixture": [["x", 9], ["y", 8]], "expected": {"x": 9, "y": 8}, "args": {},
     "input_edge": "PairList", "output_edge": "Record"},
    {"id": "prim:leaf:dm_coalesce", "capability": "first non-null value across candidate keys", "mutator": "dm_coalesce",
     "fixture": {"a": None, "b": None, "c": 5}, "expected": 5, "args": {"keys": ["a", "b", "c"]},
     "input_edge": "Record", "output_edge": "Scalar"},
    {"id": "prim:leaf:dm_keys_list", "capability": "extract sorted keys", "mutator": "dm_keys_list",
     "fixture": {"b": 2, "a": 1}, "expected": ["a", "b"], "args": {},
     "input_edge": "Record", "output_edge": "KeyList"},
    {"id": "prim:leaf:dm_values_list", "capability": "extract values ordered by sorted key", "mutator": "dm_values_list",
     "fixture": {"b": 2, "a": 1}, "expected": [1, 2], "args": {},
     "input_edge": "Record", "output_edge": "ValueList"},
    {"id": "prim:leaf:dm_count_keys", "capability": "count keys in a record", "mutator": "dm_count_keys",
     "fixture": {"a": 1, "b": 2, "c": 3}, "expected": 3, "args": {},
     "input_edge": "Record", "output_edge": "Integer"},
    {"id": "prim:leaf:dm_select_rename", "capability": "project to a keep-list then rename keys", "mutator": "dm_select_rename",
     "fixture": {"a": 1, "b": 2, "c": 3}, "expected": {"x": 1, "b": 2}, "args": {"keep": ["a", "b"], "mapping": {"a": "x"}},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_defaults_strip_none", "capability": "fill defaults then drop nulls", "mutator": "dm_defaults_strip_none",
     "fixture": {"a": 1, "b": None}, "expected": {"a": 1, "c": 3}, "args": {"defaults": {"a": 0, "b": 2, "c": 3}},
     "input_edge": "Record", "output_edge": "Record"},
    {"id": "prim:leaf:dm_swap_keys", "capability": "swap the values of two keys", "mutator": "dm_swap_keys",
     "fixture": {"a": 1, "b": 2, "c": 3}, "expected": {"a": 2, "b": 1, "c": 3}, "args": {"a": "a", "b": "b"},
     "input_edge": "Record", "output_edge": "Record"},
]

#: deliberately-wrong leaves — the proof gate MUST leave these candidate (never persisted as proven).
NEGATIVE_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:WRONG_dm_pick", "capability": "dm_pick with a wrong expected output", "mutator": "dm_pick",
     "fixture": {"a": 1, "b": 2}, "expected": {"WRONG": 999}, "args": {"keep": ["a"]},
     "input_edge": "Record", "output_edge": "Record"},
]


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    receipt = run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )
    receipt["capability"] = spec["capability"]
    return receipt


def prove_all() -> list[dict[str, Any]]:
    """Run every declared leaf primitive through the imported executed-proof runner."""
    return [_prove_one(s) for s in LEAF_SPECS]


def build_typed_rows() -> list[dict[str, Any]]:
    """Prove each leaf; keep ONLY passers; TYPE every kept row via canonicalize_edge so it can chain."""
    rows: list[dict[str, Any]] = []
    for spec in LEAF_SPECS:
        receipt = _prove_one(spec)
        if receipt["serves_truth"] is not True:
            continue  # a leaf that fails stays candidate and is NOT persisted (the gate is the whole point)
        rows.append({
            "record_type": "proven_leaf_primitive",
            "primitive_id": receipt["primitive_id"],
            "mutator": receipt["mutator"],
            "family": FAMILY,
            "capability": spec["capability"],
            "serves_truth": True,
            "candidate": False,
            "verification_level": "L7_executed_proof",
            "input_edge": spec["input_edge"],
            "output_edge": spec["output_edge"],
            "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
            "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
            "has_inverse": spec.get("inverse"),
            "proofs": receipt["proofs"],
            "all_passed": receipt["all_passed"],
            "input_hash": receipt["input_hash"],
            "output_hash": receipt["output_hash"],
        })
    return rows


def build_manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    import hashlib
    typed = [r for r in rows if r.get("input_edge_type_id") and r.get("output_edge_type_id")]
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    return {
        "record_type": "proven_dict_mapping_manifest",
        "family": FAMILY,
        "pack_id": "proven-dict-mapping-leaves",
        "generator": "scripts/prove_leaves_dict_mapping.py",
        "generated_utc": GENERATED_UTC,
        "declared_leaf_count": len(LEAF_SPECS),
        "proven_count": len(rows),
        "typed_count": len(typed),
        "proven_primitive_ids": sorted(r["primitive_id"] for r in rows),
        "roundtrip_pairs": _NEW_INVERSE_PAIRS,
        "verification_level": "L7_executed_proof",
        "row_counts": {OUT_JSONL.name: len(rows)},
        "total_rows": len(rows),
        "note": "serves_truth=true is set ONLY by an executed passing proof (run_primitive_proof, imported from "
                "scripts/mutator_registry.py). Every persisted row is TYPED (input_edge_type_id + output_edge_type_id "
                "via canonicalize_edge) so a workable leaf can chain. A deliberately-wrong leaf stays candidate.",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def write_pack() -> dict[str, Any]:
    rows = build_typed_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(rows)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


MIN_PROVEN = 28


def self_test() -> int:
    receipts = prove_all()
    rows = build_typed_rows()
    ids = [r["primitive_id"] for r in receipts]
    proven_ids = {r["primitive_id"] for r in rows}
    # a deliberately-wrong leaf must stay candidate (the gate is real, not a rubber stamp)
    wrong = _prove_one(NEGATIVE_SPECS[0])
    # a second wrong path: pass a fixture the mutator cannot handle -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:EXEC_ERROR", "dm_deep_get", 12345, "irrelevant", mutator_args={"path": "a.b"})

    roundtrip_specs = [s for s in LEAF_SPECS if s.get("inverse")]

    checks: list[tuple[str, bool]] = [
        (f">={MIN_PROVEN} leaf primitives declared", len(LEAF_SPECS) >= MIN_PROVEN),
        ("unique primitive ids", len(set(ids)) == len(ids)),
        ("EVERY declared leaf PROVES serves_truth=true via an executed proof",
         all(r["serves_truth"] is True and r["promoted"] is True for r in receipts)),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"]) for r in receipts)),
        (f">={MIN_PROVEN} leaves in the proven+persisted set", len(rows) >= MIN_PROVEN),
        ("EVERY persisted row carries non-null input+output edge type ids",
         all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in rows)),
        ("typed_count == proven_count (every workable leaf is typed)",
         len([r for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"]]) == len(rows)),
        (">=3 roundtrip-inverse leaves declared", len(roundtrip_specs) >= 3),
        ("roundtrip leaves actually ran a passing roundtrip proof", all(
            any(p["name"] == "roundtrip_test" and p["passed"] for p in _prove_one(s)["proofs"])
            for s in roundtrip_specs)),
        ("deterministic: re-running yields identical rows",
         [json.dumps(r, sort_keys=True) for r in build_typed_rows()] == [json.dumps(r, sort_keys=True) for r in rows]),
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT in the persisted proven set", wrong["primitive_id"] not in proven_ids),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("manifest proven_count + typed_count agree with the rows",
         build_manifest(rows)["proven_count"] == len(rows) and build_manifest(rows)["typed_count"] == len(rows)),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_leaves_dict_mapping:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_leaves_dict_mapping: {len(rows)} WORKABLE dict_mapping leaf primitives PROVEN end-to-end "
          f"(serves_truth=true, L7_executed_proof) AND TYPED (typed_count={len(rows)}=proven_count) via "
          f"canonicalize_edge; {len(roundtrip_specs)} roundtrip-inverse pairs proven reversible; a deliberately-wrong "
          "leaf and an un-runnable fixture correctly stay candidate. Proven + typed = chainable.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_pack()
    print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
