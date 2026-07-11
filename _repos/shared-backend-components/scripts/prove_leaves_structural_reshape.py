#!/usr/bin/env python3
"""scripts.prove_leaves_structural_reshape — WORKABLE (proven + TYPED) deterministic leaf primitives for the
'structural_reshape' family.

A vocabulary string is not a capability, and a "proven" leaf that carries no canonical edge type cannot compose. This
module closes both gaps for record-reshaping primitives: it declares >=28 REAL pure deterministic leaf callables
(flatten-nested / unflatten-dotted / transpose-records / pivot-long-to-wide / wide-to-long / group-to-tree /
nest-by-key / explode-list-field and their true inverses), runs EVERY ONE through the imported, contract-locked
`run_primitive_proof` (which EXECUTES the mutator against a fixture and flips serves_truth false->true ONLY on a
passing executed proof — never a hand-set flag), keeps ONLY the passers, and TYPES every persisted row by folding its
input_edge/output_edge through the imported `canonicalize_edge`. A workable leaf is proven AND typed: it carries a
canonical edge type on both ends so it can chain.

ADD-ONLY / flexible-multi-path: this is a NEW parallel path. It IMPORTS the machinery (mutator_registry,
build_edge_type_retrofit) and plugs its extra pure mutators INTO the shared MUTATOR_REGISTRY via setdefault
(registration, not a rewrite; never overwrites). It edits none of the contract-locked files. Where a leaf has a true
inverse (flatten/unflatten, transpose/untranspose, nest/denest, dict<->pairs, index/values) the proof runs a ROUNDTRIP
so the pair is proven reversible. Deterministic + offline: no network, no LLM, no wall-clock, no RNG. serves_truth=true
here is CORRECT and required — a deliberately-wrong-expected leaf stays candidate and is never persisted.

CLI: --self-test (offline, standalone) | --write [family jsonl + manifest].
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the contract-locked machinery — never edit it (ADD-ONLY seam).
from scripts.mutator_registry import (  # noqa: E402
    INVERSE_PAIRS,
    MUTATOR_REGISTRY,
    _receipt,
    run_primitive_proof,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

FAMILY = "structural_reshape"
# Fixed literal timestamp — no wall-clock (no datetime.now / time.time). Deterministic output.
FIXED_DATE = "2026-07-03"

OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_structural_reshape.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_structural_reshape.json"


# ── PURE deterministic reshape mutators. Contract: (payload, **kwargs) -> (transformed_output, receipt_dict). ──
def reshape_flatten_nested(record: dict[str, Any], sep: str = ".") -> tuple[dict[str, Any], dict[str, Any]]:
    """Flatten a nested record into dotted (separator-joined) leaf keys. Scalar/list leaves are kept as-is."""
    out: dict[str, Any] = {}

    def _walk(node: dict[str, Any], parent: str) -> None:
        for k, v in node.items():
            key = f"{parent}{sep}{k}" if parent else str(k)
            if isinstance(v, dict) and v:
                _walk(v, key)
            else:
                out[key] = v

    _walk(record, "")
    return out, _receipt("reshape_flatten_nested", before=record, after=out, lossless=True,
                         note=f"flatten nested -> dotted keys (sep={sep!r}); unflatten restores")


def reshape_unflatten_dotted(record: dict[str, Any], sep: str = ".") -> tuple[dict[str, Any], dict[str, Any]]:
    """Expand a flat record with separator-joined keys back into a nested record."""
    out: dict[str, Any] = {}
    for k, v in record.items():
        parts = str(k).split(sep)
        cur = out
        for p in parts[:-1]:
            nxt = cur.get(p)
            if not isinstance(nxt, dict):
                nxt = {}
                cur[p] = nxt
            cur = nxt
        cur[parts[-1]] = v
    return out, _receipt("reshape_unflatten_dotted", before=record, after=out, lossless=True,
                         note=f"unflatten dotted keys -> nested (sep={sep!r})")


def reshape_transpose_records(records: list[dict[str, Any]]) -> tuple[dict[str, list[Any]], dict[str, Any]]:
    """Row-oriented list[dict] -> column-oriented dict[list] (columnar transpose). Column order from the first row."""
    out: dict[str, list[Any]] = {}
    if records:
        for k in records[0].keys():
            out[k] = [r[k] for r in records]
    return out, _receipt("reshape_transpose_records", before=records, after=out, lossless=True,
                         note="records -> columns; untranspose restores")


def reshape_untranspose_columns(columns: dict[str, list[Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Column-oriented dict[list] -> row-oriented list[dict]."""
    keys = list(columns.keys())
    n = len(columns[keys[0]]) if keys else 0
    out = [{k: columns[k][i] for k in keys} for i in range(n)]
    return out, _receipt("reshape_untranspose_columns", before=columns, after=out, lossless=True,
                         note="columns -> records")


def reshape_pivot_long_to_wide(records: list[dict[str, Any]], index: str, key: str,
                               value: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Pivot long rows (index,key,value) into wide rows: one row per index, each distinct key becomes a column."""
    groups: dict[Any, dict[str, Any]] = {}
    order: list[Any] = []
    for r in records:
        iv = r[index]
        if iv not in groups:
            groups[iv] = {index: iv}
            order.append(iv)
        groups[iv][r[key]] = r[value]
    out = [groups[iv] for iv in order]
    return out, _receipt("reshape_pivot_long_to_wide", before=records, after=out, lossless=False,
                         note=f"pivot long->wide on index={index!r} key={key!r} value={value!r}")


def reshape_wide_to_long(records: list[dict[str, Any]], index: str, var_name: str = "key",
                         value_name: str = "value") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Melt wide rows into long (index, var_name, value_name) triples — one row per non-index column."""
    out: list[dict[str, Any]] = []
    for r in records:
        iv = r[index]
        for k, v in r.items():
            if k == index:
                continue
            out.append({index: iv, var_name: k, value_name: v})
    return out, _receipt("reshape_wide_to_long", before=records, after=out, lossless=False,
                         note=f"melt wide->long on index={index!r}")


def reshape_group_to_tree(records: list[dict[str, Any]], keys: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Group records into a nested tree keyed by `keys` in order; leaves are lists of the grouped records."""
    out: dict[str, Any] = {}
    for r in records:
        cur = out
        for k in keys[:-1]:
            cur = cur.setdefault(r[k], {})
        cur.setdefault(r[keys[-1]], []).append(r)
    return out, _receipt("reshape_group_to_tree", before=records, after=out, lossless=True,
                         note=f"group -> nested tree by {keys}")


def reshape_nest_by_key(records: list[dict[str, Any]], key: str) -> tuple[dict[Any, list[dict[str, Any]]], dict[str, Any]]:
    """Bucket records into {key_value: [records...]}, preserving order. denest restores the flat list."""
    out: dict[Any, list[dict[str, Any]]] = {}
    for r in records:
        out.setdefault(r[key], []).append(r)
    return out, _receipt("reshape_nest_by_key", before=records, after=out, lossless=True,
                         note=f"nest records by {key!r}; denest restores")


def reshape_denest_by_key(mapping: dict[Any, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Flatten a {key: [records...]} bucket map back into a single ordered record list."""
    out: list[dict[str, Any]] = []
    for bucket in mapping.values():
        out.extend(bucket)
    return out, _receipt("reshape_denest_by_key", before=mapping, after=out, lossless=True,
                         note="denest bucket map -> record list")


def reshape_group_count(records: list[dict[str, Any]], key: str) -> tuple[dict[Any, int], dict[str, Any]]:
    """Count records per distinct value of `key` -> {key_value: count}."""
    out: dict[Any, int] = {}
    for r in records:
        out[r[key]] = out.get(r[key], 0) + 1
    return out, _receipt("reshape_group_count", before=records, after=out, lossless=False,
                         note=f"count records by {key!r}")


def reshape_explode_list_field(record: dict[str, Any], field: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Explode a record whose `field` is a list into one record per element (element replaces the list)."""
    out = [{**record, field: item} for item in record[field]]
    return out, _receipt("reshape_explode_list_field", before=record, after=out, lossless=True,
                         note=f"explode list field {field!r} -> one record per element")


def reshape_implode_records(records: list[dict[str, Any]], field: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Inverse of explode: collapse records identical except `field` into one record whose `field` is the list."""
    groups: dict[Any, dict[str, Any]] = {}
    order: list[Any] = []
    for r in records:
        sig = json.dumps({k: v for k, v in r.items() if k != field}, sort_keys=True, default=str)
        if sig not in groups:
            groups[sig] = {**{k: v for k, v in r.items() if k != field}, field: []}
            order.append(sig)
        groups[sig][field].append(r[field])
    out = [groups[sig] for sig in order]
    return out, _receipt("reshape_implode_records", before=records, after=out, lossless=True,
                         note=f"implode records -> list field {field!r}")


def reshape_dict_to_pairs(record: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Emit a canonical (key-sorted) list of {key,value} pairs. pairs_to_dict restores the record."""
    out = [{"key": k, "value": record[k]} for k in sorted(record)]
    return out, _receipt("reshape_dict_to_pairs", before=record, after=out, lossless=True,
                         note="record -> sorted key/value pair list")


def reshape_pairs_to_dict(pairs: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Fold a list of {key,value} pairs back into a record."""
    out = {p["key"]: p["value"] for p in pairs}
    return out, _receipt("reshape_pairs_to_dict", before=pairs, after=out, lossless=True,
                         note="pair list -> record")


def reshape_index_by_key(records: list[dict[str, Any]], key: str) -> tuple[dict[Any, dict[str, Any]], dict[str, Any]]:
    """Index records into {key_value: record} (assumes unique keys). mapping_values restores the list."""
    out = {r[key]: r for r in records}
    return out, _receipt("reshape_index_by_key", before=records, after=out, lossless=True,
                         note=f"index records by unique {key!r}")


def reshape_mapping_values(mapping: dict[Any, dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return a mapping's values as an ordered list (inverse of index_by_key)."""
    out = list(mapping.values())
    return out, _receipt("reshape_mapping_values", before=mapping, after=out, lossless=True,
                         note="mapping values -> record list")


#: new pure mutators to plug into the shared registry (idempotent setdefault registration; never overwrites)
_NEW_MUTATORS = {
    "reshape_flatten_nested": reshape_flatten_nested,
    "reshape_unflatten_dotted": reshape_unflatten_dotted,
    "reshape_transpose_records": reshape_transpose_records,
    "reshape_untranspose_columns": reshape_untranspose_columns,
    "reshape_pivot_long_to_wide": reshape_pivot_long_to_wide,
    "reshape_wide_to_long": reshape_wide_to_long,
    "reshape_group_to_tree": reshape_group_to_tree,
    "reshape_nest_by_key": reshape_nest_by_key,
    "reshape_denest_by_key": reshape_denest_by_key,
    "reshape_group_count": reshape_group_count,
    "reshape_explode_list_field": reshape_explode_list_field,
    "reshape_implode_records": reshape_implode_records,
    "reshape_dict_to_pairs": reshape_dict_to_pairs,
    "reshape_pairs_to_dict": reshape_pairs_to_dict,
    "reshape_index_by_key": reshape_index_by_key,
    "reshape_mapping_values": reshape_mapping_values,
}
_NEW_INVERSE_PAIRS = [
    ("reshape_flatten_nested", "reshape_unflatten_dotted"),
    ("reshape_transpose_records", "reshape_untranspose_columns"),
    ("reshape_nest_by_key", "reshape_denest_by_key"),
    ("reshape_dict_to_pairs", "reshape_pairs_to_dict"),
    ("reshape_index_by_key", "reshape_mapping_values"),
]


def register_new_mutators() -> None:
    """Plug the reshape mutators into the shared MUTATOR_REGISTRY (setdefault — idempotent, never a rewrite)."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)
    for pair in _NEW_INVERSE_PAIRS:
        if pair not in INVERSE_PAIRS:
            INVERSE_PAIRS.append(pair)


register_new_mutators()


# ── the leaf primitives: each a concrete fixture + expected output (+ optional inverse) + typed edges ──
# spec fields: id, capability, mutator, fixture, expected, args, inverse, input_edge, output_edge
LEAF_SPECS: list[dict[str, Any]] = [
    # flatten / unflatten (true inverse pair — roundtrip proven)
    {"id": "prim:leaf:reshape_flatten_nested", "capability": "flatten a nested record to dotted keys",
     "mutator": "reshape_flatten_nested", "fixture": {"a": {"b": 1, "c": 2}, "d": 3},
     "expected": {"a.b": 1, "a.c": 2, "d": 3}, "args": {}, "inverse": "reshape_unflatten_dotted",
     "input_edge": "NestedRecord", "output_edge": "FlatRecord"},
    {"id": "prim:leaf:reshape_unflatten_dotted", "capability": "expand dotted keys to a nested record",
     "mutator": "reshape_unflatten_dotted", "fixture": {"a.b": 1, "a.c": 2, "d": 3},
     "expected": {"a": {"b": 1, "c": 2}, "d": 3}, "args": {},
     "input_edge": "FlatRecord", "output_edge": "NestedRecord"},
    {"id": "prim:leaf:reshape_flatten_nested_deep", "capability": "flatten a 3-level nested record (roundtrips)",
     "mutator": "reshape_flatten_nested", "fixture": {"a": {"b": {"c": 1}}, "e": 2},
     "expected": {"a.b.c": 1, "e": 2}, "args": {}, "inverse": "reshape_unflatten_dotted",
     "input_edge": "NestedRecord", "output_edge": "FlatRecord"},
    {"id": "prim:leaf:reshape_unflatten_dotted_deep", "capability": "expand 3-level dotted keys to nested",
     "mutator": "reshape_unflatten_dotted", "fixture": {"a.b.c": 1, "e": 2},
     "expected": {"a": {"b": {"c": 1}}, "e": 2}, "args": {},
     "input_edge": "FlatRecord", "output_edge": "NestedRecord"},
    {"id": "prim:leaf:reshape_flatten_nested_uscore", "capability": "flatten with a '__' separator",
     "mutator": "reshape_flatten_nested", "fixture": {"a": {"b": 1}, "c": 2},
     "expected": {"a__b": 1, "c": 2}, "args": {"sep": "__"},
     "input_edge": "NestedRecord", "output_edge": "FlatRecord"},
    {"id": "prim:leaf:reshape_unflatten_dotted_uscore", "capability": "expand '__'-joined keys to nested",
     "mutator": "reshape_unflatten_dotted", "fixture": {"a__b": 1, "c": 2},
     "expected": {"a": {"b": 1}, "c": 2}, "args": {"sep": "__"},
     "input_edge": "FlatRecord", "output_edge": "NestedRecord"},

    # transpose / untranspose (true inverse pair — roundtrip proven)
    {"id": "prim:leaf:reshape_transpose_records", "capability": "transpose row records to columns (roundtrips)",
     "mutator": "reshape_transpose_records", "fixture": [{"a": 1, "b": 2}, {"a": 3, "b": 4}],
     "expected": {"a": [1, 3], "b": [2, 4]}, "args": {}, "inverse": "reshape_untranspose_columns",
     "input_edge": "RecordList", "output_edge": "ColumnMap"},
    {"id": "prim:leaf:reshape_untranspose_columns", "capability": "untranspose columns back to row records",
     "mutator": "reshape_untranspose_columns", "fixture": {"a": [1, 3], "b": [2, 4]},
     "expected": [{"a": 1, "b": 2}, {"a": 3, "b": 4}], "args": {},
     "input_edge": "ColumnMap", "output_edge": "RecordList"},
    {"id": "prim:leaf:reshape_transpose_records_three", "capability": "transpose 3 records to columns (roundtrips)",
     "mutator": "reshape_transpose_records",
     "fixture": [{"x": 1, "y": 10}, {"x": 2, "y": 20}, {"x": 3, "y": 30}],
     "expected": {"x": [1, 2, 3], "y": [10, 20, 30]}, "args": {}, "inverse": "reshape_untranspose_columns",
     "input_edge": "RecordList", "output_edge": "ColumnMap"},
    {"id": "prim:leaf:reshape_untranspose_columns_three", "capability": "untranspose 3-length columns to records",
     "mutator": "reshape_untranspose_columns", "fixture": {"x": [1, 2, 3], "y": [10, 20, 30]},
     "expected": [{"x": 1, "y": 10}, {"x": 2, "y": 20}, {"x": 3, "y": 30}], "args": {},
     "input_edge": "ColumnMap", "output_edge": "RecordList"},

    # pivot long->wide / wide->long (melt)
    {"id": "prim:leaf:reshape_pivot_long_to_wide", "capability": "pivot long rows into a wide row",
     "mutator": "reshape_pivot_long_to_wide",
     "fixture": [{"id": 1, "metric": "x", "val": 10}, {"id": 1, "metric": "y", "val": 20}],
     "expected": [{"id": 1, "x": 10, "y": 20}], "args": {"index": "id", "key": "metric", "value": "val"},
     "input_edge": "LongRecordList", "output_edge": "WideRecordList"},
    {"id": "prim:leaf:reshape_pivot_long_to_wide_multi", "capability": "pivot long rows across 2 index groups",
     "mutator": "reshape_pivot_long_to_wide",
     "fixture": [{"id": 1, "metric": "x", "val": 10}, {"id": 2, "metric": "x", "val": 30}],
     "expected": [{"id": 1, "x": 10}, {"id": 2, "x": 30}], "args": {"index": "id", "key": "metric", "value": "val"},
     "input_edge": "LongRecordList", "output_edge": "WideRecordList"},
    {"id": "prim:leaf:reshape_wide_to_long", "capability": "melt a wide row into long rows",
     "mutator": "reshape_wide_to_long", "fixture": [{"id": 1, "x": 10, "y": 20}],
     "expected": [{"id": 1, "metric": "x", "val": 10}, {"id": 1, "metric": "y", "val": 20}],
     "args": {"index": "id", "var_name": "metric", "value_name": "val"},
     "input_edge": "WideRecordList", "output_edge": "LongRecordList"},
    {"id": "prim:leaf:reshape_wide_to_long_multi", "capability": "melt 2 wide rows into long rows",
     "mutator": "reshape_wide_to_long", "fixture": [{"id": 1, "x": 10}, {"id": 2, "x": 30}],
     "expected": [{"id": 1, "metric": "x", "val": 10}, {"id": 2, "metric": "x", "val": 30}],
     "args": {"index": "id", "var_name": "metric", "value_name": "val"},
     "input_edge": "WideRecordList", "output_edge": "LongRecordList"},

    # group-to-tree
    {"id": "prim:leaf:reshape_group_to_tree_one", "capability": "group records into a 1-level tree",
     "mutator": "reshape_group_to_tree",
     "fixture": [{"region": "na", "v": 1}, {"region": "na", "v": 2}, {"region": "eu", "v": 3}],
     "expected": {"na": [{"region": "na", "v": 1}, {"region": "na", "v": 2}], "eu": [{"region": "eu", "v": 3}]},
     "args": {"keys": ["region"]}, "input_edge": "RecordList", "output_edge": "RecordTree"},
    {"id": "prim:leaf:reshape_group_to_tree_two", "capability": "group records into a 2-level tree",
     "mutator": "reshape_group_to_tree",
     "fixture": [{"region": "na", "team": "a", "v": 1}, {"region": "na", "team": "b", "v": 2},
                 {"region": "eu", "team": "a", "v": 3}],
     "expected": {"na": {"a": [{"region": "na", "team": "a", "v": 1}], "b": [{"region": "na", "team": "b", "v": 2}]},
                  "eu": {"a": [{"region": "eu", "team": "a", "v": 3}]}},
     "args": {"keys": ["region", "team"]}, "input_edge": "RecordList", "output_edge": "RecordTree"},

    # nest-by-key / denest (true inverse pair — roundtrip proven)
    {"id": "prim:leaf:reshape_nest_by_key", "capability": "bucket records by key (roundtrips)",
     "mutator": "reshape_nest_by_key",
     "fixture": [{"g": "a", "v": 1}, {"g": "a", "v": 2}, {"g": "b", "v": 3}],
     "expected": {"a": [{"g": "a", "v": 1}, {"g": "a", "v": 2}], "b": [{"g": "b", "v": 3}]},
     "args": {"key": "g"}, "inverse": "reshape_denest_by_key",
     "input_edge": "RecordList", "output_edge": "GroupMap"},
    {"id": "prim:leaf:reshape_denest_by_key", "capability": "flatten a bucket map back to a record list",
     "mutator": "reshape_denest_by_key",
     "fixture": {"a": [{"g": "a", "v": 1}, {"g": "a", "v": 2}], "b": [{"g": "b", "v": 3}]},
     "expected": [{"g": "a", "v": 1}, {"g": "a", "v": 2}, {"g": "b", "v": 3}], "args": {},
     "input_edge": "GroupMap", "output_edge": "RecordList"},
    {"id": "prim:leaf:reshape_nest_by_key_status", "capability": "bucket records by a status key (roundtrips)",
     "mutator": "reshape_nest_by_key",
     "fixture": [{"status": "open", "n": 1}, {"status": "open", "n": 3}, {"status": "closed", "n": 2}],
     "expected": {"open": [{"status": "open", "n": 1}, {"status": "open", "n": 3}],
                  "closed": [{"status": "closed", "n": 2}]},
     "args": {"key": "status"}, "inverse": "reshape_denest_by_key",
     "input_edge": "RecordList", "output_edge": "GroupMap"},
    {"id": "prim:leaf:reshape_group_count", "capability": "count records per key value",
     "mutator": "reshape_group_count",
     "fixture": [{"g": "a"}, {"g": "a"}, {"g": "b"}], "expected": {"a": 2, "b": 1},
     "args": {"key": "g"}, "input_edge": "RecordList", "output_edge": "CountMap"},

    # explode-list-field / implode
    {"id": "prim:leaf:reshape_explode_list_field", "capability": "explode a list field into one record per element",
     "mutator": "reshape_explode_list_field", "fixture": {"id": 1, "tags": ["x", "y"]},
     "expected": [{"id": 1, "tags": "x"}, {"id": 1, "tags": "y"}], "args": {"field": "tags"},
     "input_edge": "Record", "output_edge": "RecordList"},
    {"id": "prim:leaf:reshape_explode_list_field_vals", "capability": "explode a numeric list field",
     "mutator": "reshape_explode_list_field", "fixture": {"id": 2, "vals": [10, 20, 30]},
     "expected": [{"id": 2, "vals": 10}, {"id": 2, "vals": 20}, {"id": 2, "vals": 30}], "args": {"field": "vals"},
     "input_edge": "Record", "output_edge": "RecordList"},
    {"id": "prim:leaf:reshape_explode_list_field_single", "capability": "explode a single-element list field",
     "mutator": "reshape_explode_list_field", "fixture": {"id": 3, "tags": ["only"]},
     "expected": [{"id": 3, "tags": "only"}], "args": {"field": "tags"},
     "input_edge": "Record", "output_edge": "RecordList"},
    {"id": "prim:leaf:reshape_implode_records", "capability": "implode exploded records back into a list field",
     "mutator": "reshape_implode_records", "fixture": [{"id": 1, "tags": "x"}, {"id": 1, "tags": "y"}],
     "expected": [{"id": 1, "tags": ["x", "y"]}], "args": {"field": "tags"},
     "input_edge": "RecordList", "output_edge": "Record"},

    # dict<->pairs (true inverse pair — roundtrip proven)
    {"id": "prim:leaf:reshape_dict_to_pairs", "capability": "record -> sorted key/value pair list (roundtrips)",
     "mutator": "reshape_dict_to_pairs", "fixture": {"b": 2, "a": 1},
     "expected": [{"key": "a", "value": 1}, {"key": "b", "value": 2}], "args": {}, "inverse": "reshape_pairs_to_dict",
     "input_edge": "Record", "output_edge": "PairList"},
    {"id": "prim:leaf:reshape_pairs_to_dict", "capability": "pair list -> record",
     "mutator": "reshape_pairs_to_dict", "fixture": [{"key": "a", "value": 1}, {"key": "b", "value": 2}],
     "expected": {"a": 1, "b": 2}, "args": {}, "input_edge": "PairList", "output_edge": "Record"},
    {"id": "prim:leaf:reshape_dict_to_pairs_single", "capability": "single-field record -> pair list (roundtrips)",
     "mutator": "reshape_dict_to_pairs", "fixture": {"x": 10},
     "expected": [{"key": "x", "value": 10}], "args": {}, "inverse": "reshape_pairs_to_dict",
     "input_edge": "Record", "output_edge": "PairList"},

    # index-by-key / mapping-values (true inverse pair — roundtrip proven)
    {"id": "prim:leaf:reshape_index_by_key", "capability": "index records by a unique key (roundtrips)",
     "mutator": "reshape_index_by_key", "fixture": [{"id": "a", "v": 1}, {"id": "b", "v": 2}],
     "expected": {"a": {"id": "a", "v": 1}, "b": {"id": "b", "v": 2}}, "args": {"key": "id"},
     "inverse": "reshape_mapping_values", "input_edge": "RecordList", "output_edge": "RecordMap"},
    {"id": "prim:leaf:reshape_mapping_values", "capability": "mapping values -> record list",
     "mutator": "reshape_mapping_values", "fixture": {"a": {"id": "a", "v": 1}, "b": {"id": "b", "v": 2}},
     "expected": [{"id": "a", "v": 1}, {"id": "b", "v": 2}], "args": {},
     "input_edge": "RecordMap", "output_edge": "RecordList"},
    {"id": "prim:leaf:reshape_index_by_key_sku", "capability": "index records by a sku key (roundtrips)",
     "mutator": "reshape_index_by_key", "fixture": [{"sku": "s1", "p": 5}, {"sku": "s2", "p": 9}],
     "expected": {"s1": {"sku": "s1", "p": 5}, "s2": {"sku": "s2", "p": 9}}, "args": {"key": "sku"},
     "inverse": "reshape_mapping_values", "input_edge": "RecordList", "output_edge": "RecordMap"},
]

#: deliberately-wrong leaves — the executed-proof gate MUST leave these candidate (never persisted as proven)
NEGATIVE_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:reshape_WRONG_expected", "capability": "flatten with a wrong expected output",
     "mutator": "reshape_flatten_nested", "fixture": {"a": {"b": 1}}, "expected": {"WRONG": 999}, "args": {},
     "input_edge": "NestedRecord", "output_edge": "FlatRecord"},
]


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    receipt = run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )
    receipt["capability"] = spec["capability"]
    receipt["_spec"] = spec
    return receipt


def prove_all() -> list[dict[str, Any]]:
    """Run every declared leaf primitive through the imported executed-proof runner."""
    return [_prove_one(s) for s in LEAF_SPECS]


def _typed_row(receipt: dict[str, Any]) -> dict[str, Any]:
    """Build a WORKABLE row: proven (serves_truth=true) AND typed (canonical edge types on both ends)."""
    spec = receipt["_spec"]
    input_edge = spec["input_edge"]
    output_edge = spec["output_edge"]
    return {
        "record_type": "proven_reshape_leaf",
        "primitive_id": receipt["primitive_id"],
        "mutator": receipt["mutator"],
        "capability": receipt["capability"],
        "family": FAMILY,
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": input_edge,
        "output_edge": output_edge,
        "input_edge_type_id": canonicalize_edge(input_edge),
        "output_edge_type_id": canonicalize_edge(output_edge),
        "has_inverse": spec.get("inverse"),
        "roundtrip_proven": any(p["name"] == "roundtrip_test" and p["passed"] for p in receipt["proofs"]),
        "input_hash": receipt["input_hash"],
        "output_hash": receipt["output_hash"],
    }


def proven_rows() -> list[dict[str, Any]]:
    """Only leaves whose executed proof PASSED, each TYPED via canonicalize_edge. Sorted by primitive_id."""
    rows = [_typed_row(r) for r in prove_all() if r["serves_truth"] is True and r["promoted"] is True]
    rows.sort(key=lambda r: r["primitive_id"])
    return rows


def build_manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"]]
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    roundtrip_ids = sorted(r["primitive_id"] for r in rows if r["roundtrip_proven"])
    return {
        "record_type": "proven_structural_reshape_manifest",
        "pack_id": "proven-structural-reshape",
        "generator": "scripts/prove_leaves_structural_reshape.py",
        "family": FAMILY,
        "generated_utc": FIXED_DATE,
        "declared_leaf_count": len(LEAF_SPECS),
        "proven_count": len(rows),
        "typed_count": len(typed),
        "roundtrip_proven_count": len(roundtrip_ids),
        "roundtrip_proven_ids": roundtrip_ids,
        "proven_primitive_ids": sorted(r["primitive_id"] for r in rows),
        "verification_level": "L7_executed_proof",
        "row_counts": {OUT_JSONL.name: len(rows)},
        "total_rows": len(rows),
        "note": "serves_truth=true set ONLY by an executed passing proof (run_primitive_proof, imported from "
                "scripts/mutator_registry.py); every row is TYPED via canonicalize_edge (imported from "
                "scripts/build_edge_type_retrofit.py). A deliberately-wrong leaf stays candidate and is never "
                "persisted here.",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def write_pack() -> dict[str, Any]:
    rows = proven_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(rows)
    OUT_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    receipts = prove_all()
    rows = proven_rows()
    ids = [r["primitive_id"] for r in rows]

    # a deliberately-wrong-expected leaf must stay CANDIDATE (the gate is real, not a rubber stamp)
    wrong = _prove_one(NEGATIVE_SPECS[0])
    # an un-runnable fixture (missing required arg key) -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:reshape_EXEC_ERROR", "reshape_index_by_key",
                              [{"no_key": 1}], {}, mutator_args={"key": "id"})

    inverse_specs = [s for s in LEAF_SPECS if s.get("inverse")]

    checks: list[tuple[str, bool]] = [
        (">=28 leaf primitives declared", len(LEAF_SPECS) >= 28),
        ("unique primitive ids", len(set(ids)) == len(set(s["id"] for s in LEAF_SPECS)) == len(LEAF_SPECS)),
        (">=28 leaves PROVE serves_truth=true via an executed proof", len(rows) >= 28),
        ("every declared leaf proved (all promoted)",
         all(r["serves_truth"] is True and r["promoted"] is True for r in receipts)),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"])
             for r in receipts)),
        ("EVERY persisted row carries non-null input_edge_type_id + output_edge_type_id",
         all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in rows)),
        ("typed_count == proven_count (every workable leaf is typed)",
         build_manifest(rows)["typed_count"] == build_manifest(rows)["proven_count"] == len(rows)),
        ("every persisted row is serves_truth=true / candidate=false / family=structural_reshape",
         all(r["serves_truth"] is True and r["candidate"] is False and r["family"] == FAMILY for r in rows)),
        ("roundtrip-inverse pairs prove reversible (roundtrip_test passed)",
         len(inverse_specs) >= 5 and all(
             any(p["name"] == "roundtrip_test" and p["passed"]
                 for p in next(rr for rr in receipts if rr["primitive_id"] == s["id"])["proofs"])
             for s in inverse_specs)),
        ("every roundtrip leaf is flagged roundtrip_proven in its persisted row",
         all(next(r for r in rows if r["primitive_id"] == s["id"])["roundtrip_proven"] for s in inverse_specs)),
        ("deterministic: re-running yields identical rows",
         [json.dumps(r, sort_keys=True) for r in proven_rows()]
         == [json.dumps(r, sort_keys=True) for r in rows]),
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT in the persisted rows", wrong["primitive_id"] not in ids),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("reshape mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
        ("manifest proven_count matches the persisted rows", build_manifest(rows)["proven_count"] == len(rows)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_leaves_structural_reshape:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_leaves_structural_reshape: {len(rows)} WORKABLE (proven + typed) leaf primitives for the "
          f"'{FAMILY}' family — serves_truth=true via the imported executed-proof runner, every row typed via "
          f"canonicalize_edge, {build_manifest(rows)['roundtrip_proven_count']} inverse pairs proven reversible; a "
          "deliberately-wrong leaf and an un-runnable fixture correctly stay candidate.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    if args.write:
        manifest = write_pack()
        print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
