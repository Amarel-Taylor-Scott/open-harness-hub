#!/usr/bin/env python3
"""scripts.prove_leaves_set_relational — WORKABLE (proven + TYPED) deterministic leaf primitives for 'set_relational'.

The set_relational family is the relational-algebra backbone of the component network: union / intersect / difference /
inner-join / left-antijoin / semijoin / dedupe-cluster / cross-pair over RecordBatch->RecordBatch. This module declares
>=28 REAL pure deterministic leaf primitives (no wall-clock / RNG / network / I/O in any body), plugs them into the
shared MUTATOR_REGISTRY (idempotent setdefault — never overwrites), runs EVERY leaf through the imported
`run_primitive_proof` (the ONLY thing that flips serves_truth false->true — via an executed passing proof), and
PERSISTS only the passers, each TYPED with canonical input/output edge type ids (`canonicalize_edge`) so a workable
leaf can chain. A deliberately-wrong-expected leaf stays candidate and is never persisted — that gate is the point.

ADD-ONLY: this is a NEW parallel path. It IMPORTS the existing machinery (mutator_registry, build_edge_type_retrofit)
and never edits it, and writes its OWN family file (no shared JSONL — avoids write races). Roundtrip-inverse pairs
(group/ungroup, index/deindex, tag/untag, jsonl-encode/decode) prove reversibility via `has_inverse`.
CLI: --self-test (offline, standalone) | --write [--date D].
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

# IMPORT the existing machinery — never edit it (ADD-ONLY).
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    _receipt,
    run_primitive_proof,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

FAMILY = "set_relational"
OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_set_relational.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_set_relational.json"

# fixed literal timestamp — NO wall-clock (deterministic + offline law).
_FIXED_DATE = "2026-07-03"


# ══ PURE deterministic set-relational leaf mutators: (payload, **kwargs) -> (output, receipt_dict) ══
# Two-batch ops carry the RIGHT batch through **kwargs (run_primitive_proof forwards mutator_args as kwargs).

def sr_union_by_key(left: list[dict[str, Any]], *, right: list[dict[str, Any]], key: str):
    seen: set = set()
    out: list = []
    for r in list(left) + list(right):
        k = r.get(key)
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out, _receipt("sr_union_by_key", before=left, after=out, lossless=False, note=f"union deduped by {key}, left precedence")


def sr_concat_batches(left: list[dict[str, Any]], *, right: list[dict[str, Any]]):
    out = list(left) + list(right)
    return out, _receipt("sr_concat_batches", before=left, after=out, lossless=False, note="concat both batches (no dedupe)")


def sr_intersect_keys(left: list[dict[str, Any]], *, right: list[dict[str, Any]], key: str):
    rk = {r.get(key) for r in right}
    seen: set = set()
    out: list = []
    for r in left:
        k = r.get(key)
        if k in rk and k not in seen:
            seen.add(k)
            out.append({key: k})
    return out, _receipt("sr_intersect_keys", before=left, after=out, lossless=False, note=f"keys present in BOTH batches on {key}")


def sr_difference_by_key(left: list[dict[str, Any]], *, right: list[dict[str, Any]], key: str):
    rk = {r.get(key) for r in right}
    out = [r for r in left if r.get(key) not in rk]
    return out, _receipt("sr_difference_by_key", before=left, after=out, lossless=False, note=f"left rows whose {key} not in right")


def sr_symmetric_difference_by_key(left: list[dict[str, Any]], *, right: list[dict[str, Any]], key: str):
    lk = {r.get(key) for r in left}
    rk = {r.get(key) for r in right}
    out = [r for r in left if r.get(key) not in rk] + [r for r in right if r.get(key) not in lk]
    return out, _receipt("sr_symmetric_difference_by_key", before=left, after=out, lossless=False, note=f"rows whose {key} in exactly one batch")


def sr_inner_join_on_key(left: list[dict[str, Any]], *, right: list[dict[str, Any]], key: str):
    ridx: dict = {}
    for r in right:
        ridx.setdefault(r.get(key), r)
    out = [{**l, **ridx[l.get(key)]} for l in left if l.get(key) in ridx]
    return out, _receipt("sr_inner_join_on_key", before=left, after=out, lossless=False, note=f"inner join merge on {key}")


def sr_left_outer_join_on_key(left: list[dict[str, Any]], *, right: list[dict[str, Any]], key: str):
    ridx: dict = {}
    for r in right:
        ridx.setdefault(r.get(key), r)
    out = [{**l, **ridx[l.get(key)]} if l.get(key) in ridx else dict(l) for l in left]
    return out, _receipt("sr_left_outer_join_on_key", before=left, after=out, lossless=False, note=f"left outer join on {key}; unmatched left kept")


def sr_left_antijoin(left: list[dict[str, Any]], *, right: list[dict[str, Any]], key: str):
    rk = {r.get(key) for r in right}
    out = [r for r in left if r.get(key) not in rk]
    return out, _receipt("sr_left_antijoin", before=left, after=out, lossless=False, note=f"left rows with NO match in right on {key}")


def sr_right_antijoin(left: list[dict[str, Any]], *, right: list[dict[str, Any]], key: str):
    lk = {r.get(key) for r in left}
    out = [r for r in right if r.get(key) not in lk]
    return out, _receipt("sr_right_antijoin", before=left, after=out, lossless=False, note=f"right rows with NO match in left on {key}")


def sr_semijoin_left(left: list[dict[str, Any]], *, right: list[dict[str, Any]], key: str):
    rk = {r.get(key) for r in right}
    out = [r for r in left if r.get(key) in rk]
    return out, _receipt("sr_semijoin_left", before=left, after=out, lossless=False, note=f"left rows that HAVE a match in right on {key} (no merge)")


def sr_cross_pair(left: list[dict[str, Any]], *, right: list[dict[str, Any]]):
    out = [{"left": l, "right": r} for l in left for r in right]
    return out, _receipt("sr_cross_pair", before=left, after=out, lossless=False, note="cross product (left-major) as {left,right} pairs")


def sr_dedupe_cluster_key(records: list[dict[str, Any]], *, key: str):
    order: list = []
    clusters: dict = {}
    for r in records:
        k = r.get(key)
        if k not in clusters:
            clusters[k] = []
            order.append(k)
        clusters[k].append(r)
    out = [{"key": k, "representative": clusters[k][0], "members": clusters[k]} for k in order]
    return out, _receipt("sr_dedupe_cluster_key", before=records, after=out, lossless=True, note=f"cluster rows by {key}; representative + members (lossless)")


def sr_dedupe_by_key_first(records: list[dict[str, Any]], *, key: str):
    seen: set = set()
    out: list = []
    for r in records:
        k = r.get(key)
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out, _receipt("sr_dedupe_by_key_first", before=records, after=out, lossless=False, note=f"keep FIRST row per {key}")


def sr_dedupe_by_key_last(records: list[dict[str, Any]], *, key: str):
    d: dict = {}
    for r in records:
        d[r.get(key)] = r
    out = list(d.values())
    return out, _receipt("sr_dedupe_by_key_last", before=records, after=out, lossless=False, note=f"keep LAST value per {key} (first-appearance position)")


def sr_group_by_key(records: list[dict[str, Any]], *, key: str):
    out: dict = {}
    for r in records:
        out.setdefault(r.get(key), []).append(r)
    return out, _receipt("sr_group_by_key", before=records, after=out, lossless=True, note=f"group rows into {{key->[rows]}} on {key}; ungroup restores")


def sr_ungroup(groups: dict[Any, list[dict[str, Any]]]):
    out: list = []
    for rows in groups.values():
        out.extend(rows)
    return out, _receipt("sr_ungroup", before=groups, after=out, lossless=True, note="flatten {key->[rows]} back to a batch")


def sr_index_by_key(records: list[dict[str, Any]], *, key: str):
    out: dict = {}
    for r in records:
        out.setdefault(r.get(key), r)
    return out, _receipt("sr_index_by_key", before=records, after=out, lossless=True, note=f"index rows by unique {key}; deindex restores")


def sr_deindex(index: dict[Any, dict[str, Any]]):
    out = list(index.values())
    return out, _receipt("sr_deindex", before=index, after=out, lossless=True, note="drop the index, return the row batch")


def sr_tag_source(records: list[dict[str, Any]], *, source: str):
    out = [{**r, "_source": source} for r in records]
    return out, _receipt("sr_tag_source", before=records, after=out, lossless=True, note="attach a _source tag to each row; untag restores")


def sr_untag_source(records: list[dict[str, Any]]):
    out = [{k: v for k, v in r.items() if k != "_source"} for r in records]
    return out, _receipt("sr_untag_source", before=records, after=out, lossless=True, note="strip the _source tag from each row")


def sr_records_to_jsonl(records: list[dict[str, Any]]):
    out = "\n".join(json.dumps(r, sort_keys=True) for r in records)
    return out, _receipt("sr_records_to_jsonl", before=records, after=out, lossless=True, note="canonical JSONL of the batch; parse restores")


def sr_jsonl_to_records(text: str):
    out = [json.loads(line) for line in text.split("\n") if line]
    return out, _receipt("sr_jsonl_to_records", before=text, after=out, lossless=True, note="parse a JSONL batch into rows")


def sr_count_by_key(records: list[dict[str, Any]], *, key: str):
    order: list = []
    counts: dict = {}
    for r in records:
        k = r.get(key)
        if k not in counts:
            counts[k] = 0
            order.append(k)
        counts[k] += 1
    out = [{"key": k, "count": counts[k]} for k in order]
    return out, _receipt("sr_count_by_key", before=records, after=out, lossless=False, note=f"multiplicity per {key}")


def sr_distinct_keys(records: list[dict[str, Any]], *, key: str):
    seen: set = set()
    out: list = []
    for r in records:
        k = r.get(key)
        if k in seen:
            continue
        seen.add(k)
        out.append(k)
    return out, _receipt("sr_distinct_keys", before=records, after=out, lossless=False, note=f"order-preserving distinct {key} values")


def sr_partition_by_predicate(records: list[dict[str, Any]], *, field: str, equals: Any):
    matched = [r for r in records if r.get(field) == equals]
    unmatched = [r for r in records if r.get(field) != equals]
    out = {"matched": matched, "unmatched": unmatched}
    return out, _receipt("sr_partition_by_predicate", before=records, after=out, lossless=True, note=f"split batch on {field}=={equals!r}")


def sr_sort_batch_by_key(records: list[dict[str, Any]], *, key: str):
    out = sorted(records, key=lambda r: r.get(key))
    return out, _receipt("sr_sort_batch_by_key", before=records, after=out, lossless=True, note=f"stable-sort batch ascending by {key}")


def sr_project_keys(records: list[dict[str, Any]], *, keep: list[str]):
    out = [{k: r[k] for k in keep if k in r} for r in records]
    return out, _receipt("sr_project_keys", before=records, after=out, lossless=False, note=f"project each row to {keep}")


def sr_filter_by_key_in(records: list[dict[str, Any]], *, key: str, allowed: list[Any]):
    allow = set(allowed)
    out = [r for r in records if r.get(key) in allow]
    return out, _receipt("sr_filter_by_key_in", before=records, after=out, lossless=False, note=f"keep rows whose {key} in allow-list")


def sr_exclude_by_key_in(records: list[dict[str, Any]], *, key: str, blocked: list[Any]):
    block = set(blocked)
    out = [r for r in records if r.get(key) not in block]
    return out, _receipt("sr_exclude_by_key_in", before=records, after=out, lossless=False, note=f"drop rows whose {key} in block-list")


def sr_coalesce_by_key(left: list[dict[str, Any]], *, right: list[dict[str, Any]], key: str):
    ridx: dict = {}
    for r in right:
        ridx.setdefault(r.get(key), r)
    seen: set = set()
    out: list = []
    for l in left:
        k = l.get(key)
        seen.add(k)
        out.append({**ridx.get(k, {}), **l})  # left precedence; right fills missing fields
    for r in right:
        if r.get(key) not in seen:
            out.append(r)
    return out, _receipt("sr_coalesce_by_key", before=left, after=out, lossless=False, note=f"union on {key}; right fills fields missing from left")


#: NEW pure mutators for the shared registry (idempotent registration; never overwrites existing entries)
_NEW_MUTATORS = {
    "sr_union_by_key": sr_union_by_key, "sr_concat_batches": sr_concat_batches,
    "sr_intersect_keys": sr_intersect_keys, "sr_difference_by_key": sr_difference_by_key,
    "sr_symmetric_difference_by_key": sr_symmetric_difference_by_key, "sr_inner_join_on_key": sr_inner_join_on_key,
    "sr_left_outer_join_on_key": sr_left_outer_join_on_key, "sr_left_antijoin": sr_left_antijoin,
    "sr_right_antijoin": sr_right_antijoin, "sr_semijoin_left": sr_semijoin_left, "sr_cross_pair": sr_cross_pair,
    "sr_dedupe_cluster_key": sr_dedupe_cluster_key, "sr_dedupe_by_key_first": sr_dedupe_by_key_first,
    "sr_dedupe_by_key_last": sr_dedupe_by_key_last, "sr_group_by_key": sr_group_by_key, "sr_ungroup": sr_ungroup,
    "sr_index_by_key": sr_index_by_key, "sr_deindex": sr_deindex, "sr_tag_source": sr_tag_source,
    "sr_untag_source": sr_untag_source, "sr_records_to_jsonl": sr_records_to_jsonl,
    "sr_jsonl_to_records": sr_jsonl_to_records, "sr_count_by_key": sr_count_by_key,
    "sr_distinct_keys": sr_distinct_keys, "sr_partition_by_predicate": sr_partition_by_predicate,
    "sr_sort_batch_by_key": sr_sort_batch_by_key, "sr_project_keys": sr_project_keys,
    "sr_filter_by_key_in": sr_filter_by_key_in, "sr_exclude_by_key_in": sr_exclude_by_key_in,
    "sr_coalesce_by_key": sr_coalesce_by_key,
}


def register_new_mutators() -> None:
    """Plug the set_relational mutators into the shared MUTATOR_REGISTRY (idempotent setdefault, never overwrite)."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# ── canonical fixtures (shared across specs; small, deterministic) ──
_LB = [{"k": 1, "v": "a"}, {"k": 2, "v": "b"}]
_RB = [{"k": 2, "w": "x"}, {"k": 3, "w": "y"}]
_DC = [{"k": 1, "id": "a"}, {"k": 1, "id": "b"}, {"k": 2, "id": "c"}]


# ══ the leaf primitives: each a REAL relational capability with a concrete fixture + expected output (+ inverse) ══
# spec fields: id, capability, mutator, fixture, expected, args?, inverse?, input_edge, output_edge
LEAF_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:sr_union_by_key", "capability": "union two batches deduped by key (left precedence)",
     "mutator": "sr_union_by_key", "fixture": _LB, "args": {"right": _RB, "key": "k"},
     "expected": [{"k": 1, "v": "a"}, {"k": 2, "v": "b"}, {"k": 3, "w": "y"}],
     "input_edge": "RecordBatchPair", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_concat_batches", "capability": "concatenate two batches without dedupe",
     "mutator": "sr_concat_batches", "fixture": _LB, "args": {"right": _RB},
     "expected": [{"k": 1, "v": "a"}, {"k": 2, "v": "b"}, {"k": 2, "w": "x"}, {"k": 3, "w": "y"}],
     "input_edge": "RecordBatchPair", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_intersect_keys", "capability": "keys present in both batches",
     "mutator": "sr_intersect_keys", "fixture": _LB, "args": {"right": _RB, "key": "k"},
     "expected": [{"k": 2}], "input_edge": "RecordBatchPair", "output_edge": "KeyBatch"},
    {"id": "prim:leaf:sr_difference_by_key", "capability": "left rows whose key is not in right",
     "mutator": "sr_difference_by_key", "fixture": _LB, "args": {"right": _RB, "key": "k"},
     "expected": [{"k": 1, "v": "a"}], "input_edge": "RecordBatchPair", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_symmetric_difference_by_key", "capability": "rows whose key is in exactly one batch",
     "mutator": "sr_symmetric_difference_by_key", "fixture": _LB, "args": {"right": _RB, "key": "k"},
     "expected": [{"k": 1, "v": "a"}, {"k": 3, "w": "y"}],
     "input_edge": "RecordBatchPair", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_inner_join_on_key", "capability": "inner join two batches, merging matched rows",
     "mutator": "sr_inner_join_on_key", "fixture": _LB, "args": {"right": _RB, "key": "k"},
     "expected": [{"k": 2, "v": "b", "w": "x"}], "input_edge": "RecordBatchPair", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_left_outer_join_on_key", "capability": "left outer join; unmatched left rows kept",
     "mutator": "sr_left_outer_join_on_key", "fixture": _LB, "args": {"right": _RB, "key": "k"},
     "expected": [{"k": 1, "v": "a"}, {"k": 2, "v": "b", "w": "x"}],
     "input_edge": "RecordBatchPair", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_left_antijoin", "capability": "left rows with no match in right",
     "mutator": "sr_left_antijoin", "fixture": _LB, "args": {"right": _RB, "key": "k"},
     "expected": [{"k": 1, "v": "a"}], "input_edge": "RecordBatchPair", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_right_antijoin", "capability": "right rows with no match in left",
     "mutator": "sr_right_antijoin", "fixture": _LB, "args": {"right": _RB, "key": "k"},
     "expected": [{"k": 3, "w": "y"}], "input_edge": "RecordBatchPair", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_semijoin_left", "capability": "left rows that have a match in right (no merge)",
     "mutator": "sr_semijoin_left", "fixture": _LB, "args": {"right": _RB, "key": "k"},
     "expected": [{"k": 2, "v": "b"}], "input_edge": "RecordBatchPair", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_cross_pair", "capability": "cross product of two batches as {left,right} pairs",
     "mutator": "sr_cross_pair", "fixture": _LB, "args": {"right": _RB},
     "expected": [{"left": {"k": 1, "v": "a"}, "right": {"k": 2, "w": "x"}},
                  {"left": {"k": 1, "v": "a"}, "right": {"k": 3, "w": "y"}},
                  {"left": {"k": 2, "v": "b"}, "right": {"k": 2, "w": "x"}},
                  {"left": {"k": 2, "v": "b"}, "right": {"k": 3, "w": "y"}}],
     "input_edge": "RecordBatchPair", "output_edge": "RecordPairBatch"},
    {"id": "prim:leaf:sr_dedupe_cluster_key", "capability": "cluster rows by key into representative + members",
     "mutator": "sr_dedupe_cluster_key", "fixture": _DC, "args": {"key": "k"},
     "expected": [{"key": 1, "representative": {"k": 1, "id": "a"},
                   "members": [{"k": 1, "id": "a"}, {"k": 1, "id": "b"}]},
                  {"key": 2, "representative": {"k": 2, "id": "c"}, "members": [{"k": 2, "id": "c"}]}],
     "input_edge": "RecordBatch", "output_edge": "RecordClusterBatch"},
    {"id": "prim:leaf:sr_dedupe_by_key_first", "capability": "keep the first row per key",
     "mutator": "sr_dedupe_by_key_first", "fixture": _DC, "args": {"key": "k"},
     "expected": [{"k": 1, "id": "a"}, {"k": 2, "id": "c"}],
     "input_edge": "RecordBatch", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_dedupe_by_key_last", "capability": "keep the last value per key",
     "mutator": "sr_dedupe_by_key_last", "fixture": _DC, "args": {"key": "k"},
     "expected": [{"k": 1, "id": "b"}, {"k": 2, "id": "c"}],
     "input_edge": "RecordBatch", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_group_by_key", "capability": "group a batch into {key->rows} (roundtrips)",
     "mutator": "sr_group_by_key", "fixture": [{"k": 1, "v": "a"}, {"k": 1, "v": "b"}, {"k": 2, "v": "c"}],
     "args": {"key": "k"},
     "expected": {1: [{"k": 1, "v": "a"}, {"k": 1, "v": "b"}], 2: [{"k": 2, "v": "c"}]},
     "inverse": "sr_ungroup", "input_edge": "RecordBatch", "output_edge": "RecordGroups"},
    {"id": "prim:leaf:sr_ungroup", "capability": "flatten {key->rows} back into a batch",
     "mutator": "sr_ungroup", "fixture": {1: [{"k": 1, "v": "a"}], 2: [{"k": 2, "v": "c"}]},
     "expected": [{"k": 1, "v": "a"}, {"k": 2, "v": "c"}],
     "input_edge": "RecordGroups", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_index_by_key", "capability": "index rows by a unique key (roundtrips)",
     "mutator": "sr_index_by_key", "fixture": [{"id": "a", "n": 1}, {"id": "b", "n": 2}], "args": {"key": "id"},
     "expected": {"a": {"id": "a", "n": 1}, "b": {"id": "b", "n": 2}},
     "inverse": "sr_deindex", "input_edge": "RecordBatch", "output_edge": "RecordIndex"},
    {"id": "prim:leaf:sr_deindex", "capability": "drop a key index back into a batch",
     "mutator": "sr_deindex", "fixture": {"a": {"id": "a", "n": 1}, "b": {"id": "b", "n": 2}},
     "expected": [{"id": "a", "n": 1}, {"id": "b", "n": 2}],
     "input_edge": "RecordIndex", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_tag_source", "capability": "tag each row with a source (roundtrips)",
     "mutator": "sr_tag_source", "fixture": [{"k": 1}, {"k": 2}], "args": {"source": "src"},
     "expected": [{"k": 1, "_source": "src"}, {"k": 2, "_source": "src"}],
     "inverse": "sr_untag_source", "input_edge": "RecordBatch", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_untag_source", "capability": "strip the source tag from each row",
     "mutator": "sr_untag_source", "fixture": [{"k": 1, "_source": "src"}, {"k": 2, "_source": "src"}],
     "expected": [{"k": 1}, {"k": 2}], "input_edge": "RecordBatch", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_records_to_jsonl", "capability": "serialize a batch to canonical JSONL (roundtrips)",
     "mutator": "sr_records_to_jsonl", "fixture": [{"a": 1}, {"b": 2}],
     "expected": '{"a": 1}\n{"b": 2}',
     "inverse": "sr_jsonl_to_records", "input_edge": "RecordBatch", "output_edge": "JsonlText"},
    {"id": "prim:leaf:sr_jsonl_to_records", "capability": "parse a JSONL batch into rows",
     "mutator": "sr_jsonl_to_records", "fixture": '{"a": 1}\n{"b": 2}',
     "expected": [{"a": 1}, {"b": 2}], "input_edge": "JsonlText", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_count_by_key", "capability": "count multiplicity per key",
     "mutator": "sr_count_by_key", "fixture": _DC, "args": {"key": "k"},
     "expected": [{"key": 1, "count": 2}, {"key": 2, "count": 1}],
     "input_edge": "RecordBatch", "output_edge": "KeyCountBatch"},
    {"id": "prim:leaf:sr_distinct_keys", "capability": "order-preserving distinct key values",
     "mutator": "sr_distinct_keys", "fixture": _DC, "args": {"key": "k"},
     "expected": [1, 2], "input_edge": "RecordBatch", "output_edge": "KeyList"},
    {"id": "prim:leaf:sr_partition_by_predicate", "capability": "split a batch on a field-equals predicate",
     "mutator": "sr_partition_by_predicate",
     "fixture": [{"s": "ok", "n": 1}, {"s": "no", "n": 2}, {"s": "ok", "n": 3}],
     "args": {"field": "s", "equals": "ok"},
     "expected": {"matched": [{"s": "ok", "n": 1}, {"s": "ok", "n": 3}], "unmatched": [{"s": "no", "n": 2}]},
     "input_edge": "RecordBatch", "output_edge": "RecordPartition"},
    {"id": "prim:leaf:sr_sort_batch_by_key", "capability": "stable-sort a batch ascending by key",
     "mutator": "sr_sort_batch_by_key", "fixture": [{"k": 3}, {"k": 1}, {"k": 2}], "args": {"key": "k"},
     "expected": [{"k": 1}, {"k": 2}, {"k": 3}], "input_edge": "RecordBatch", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_project_keys", "capability": "relational projection onto a keep-list",
     "mutator": "sr_project_keys", "fixture": [{"a": 1, "b": 2, "c": 3}], "args": {"keep": ["a", "c"]},
     "expected": [{"a": 1, "c": 3}], "input_edge": "RecordBatch", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_filter_by_key_in", "capability": "keep rows whose key is in an allow-list",
     "mutator": "sr_filter_by_key_in", "fixture": [{"k": 1}, {"k": 2}, {"k": 3}],
     "args": {"key": "k", "allowed": [1, 3]}, "expected": [{"k": 1}, {"k": 3}],
     "input_edge": "RecordBatch", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_exclude_by_key_in", "capability": "drop rows whose key is in a block-list",
     "mutator": "sr_exclude_by_key_in", "fixture": [{"k": 1}, {"k": 2}, {"k": 3}],
     "args": {"key": "k", "blocked": [2]}, "expected": [{"k": 1}, {"k": 3}],
     "input_edge": "RecordBatch", "output_edge": "RecordBatch"},
    {"id": "prim:leaf:sr_coalesce_by_key", "capability": "union on key; right fills fields missing from left",
     "mutator": "sr_coalesce_by_key", "fixture": [{"k": 1, "v": "a"}],
     "args": {"right": [{"k": 1, "w": "x"}, {"k": 2, "w": "y"}], "key": "k"},
     "expected": [{"k": 1, "w": "x", "v": "a"}, {"k": 2, "w": "y"}],
     "input_edge": "RecordBatchPair", "output_edge": "RecordBatch"},
]

#: deliberately-wrong leaf — the proof gate MUST leave it candidate (never persisted as proven)
NEGATIVE_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:sr_WRONG_expected", "capability": "union_by_key with a wrong expected output",
     "mutator": "sr_union_by_key", "fixture": _LB, "args": {"right": _RB, "key": "k"},
     "expected": [{"WRONG": 999}], "input_edge": "RecordBatchPair", "output_edge": "RecordBatch"},
]


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    receipt = run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )
    receipt["capability"] = spec["capability"]
    receipt["family"] = FAMILY
    receipt["input_edge"] = spec["input_edge"]
    receipt["output_edge"] = spec["output_edge"]
    return receipt


def prove_all() -> list[dict[str, Any]]:
    """Run every declared set_relational leaf through the imported executed-proof runner."""
    return [_prove_one(s) for s in LEAF_SPECS]


def _persist_row(spec: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    """A WORKABLE row: proven (serves_truth=true) AND TYPED (canonical input/output edge type ids)."""
    return {
        "primitive_id": receipt["primitive_id"],
        "mutator": receipt["mutator"],
        "capability": spec["capability"],
        "family": FAMILY,
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": spec["input_edge"],
        "output_edge": spec["output_edge"],
        "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
        "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
    }


def proven_rows() -> list[dict[str, Any]]:
    """Persisted rows for leaves whose executed proof PASSED — proven AND typed, sorted by primitive_id."""
    by_id = {s["id"]: s for s in LEAF_SPECS}
    rows: list[dict[str, Any]] = []
    for r in prove_all():
        if r["serves_truth"] is True and r.get("promoted") is True:
            rows.append(_persist_row(by_id[r["primitive_id"]], r))
    return sorted(rows, key=lambda x: x["primitive_id"])


def build_manifest(rows: list[dict[str, Any]], *, date: str) -> dict[str, Any]:
    typed = [r for r in rows if r.get("input_edge_type_id") and r.get("output_edge_type_id")]
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    import hashlib
    return {
        "record_type": "proven_set_relational_manifest",
        "pack_id": "proven-set-relational", "family": FAMILY,
        "generator": "scripts/prove_leaves_set_relational.py",
        "generated_utc": date,
        "declared_leaf_count": len(LEAF_SPECS),
        "proven_count": len(rows),
        "typed_count": len(typed),
        "proven_primitive_ids": [r["primitive_id"] for r in rows],
        "verification_level": "L7_executed_proof",
        "row_counts": {OUT_JSONL.name: len(rows)},
        "total_rows": len(rows),
        "note": "serves_truth=true is set ONLY by an executed passing proof (run_primitive_proof, imported from "
                "scripts/mutator_registry.py). Every persisted row is proven AND typed with canonical edge type ids "
                "so it can chain. A deliberately-wrong leaf stays candidate and is never persisted here.",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def write_pack(*, date: str) -> dict[str, Any]:
    rows = proven_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(rows, date=date)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    receipts = prove_all()
    rows = proven_rows()
    ids = [r["primitive_id"] for r in receipts]
    proven_ids = {r["primitive_id"] for r in rows}

    # a deliberately-wrong leaf MUST stay candidate (the gate is real, not a rubber stamp)
    wrong = _prove_one(NEGATIVE_SPECS[0])
    # a second failure path: un-runnable fixture -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:sr_EXEC_ERROR", "sr_union_by_key", object(), "irrelevant")

    inverse_specs = [s for s in LEAF_SPECS if s.get("inverse")]
    rt_by_id = {r["primitive_id"]: r for r in receipts}

    checks: list[tuple[str, bool]] = [
        (">=28 leaf primitives declared", len(LEAF_SPECS) >= 28),
        ("unique primitive ids", len(set(ids)) == len(ids)),
        ("EVERY declared leaf PROVES serves_truth=true via an executed proof",
         all(r["serves_truth"] is True and r["promoted"] is True for r in receipts)),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"]) for r in receipts)),
        (">=28 proven+persisted rows", len(rows) >= 28),
        ("proven_count == typed_count (every workable leaf is TYPED)",
         len(rows) == len([r for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"]])),
        ("EVERY persisted row carries non-null input+output edge type ids",
         all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in rows)),
        ("every persisted row is serves_truth=true / L7", all(r["serves_truth"] is True and r["verification_level"] == "L7_executed_proof" for r in rows)),
        (">=4 roundtrip-inverse pairs declared", len(inverse_specs) >= 4),
        ("roundtrip-inverse pairs PROVE reversible (roundtrip_test passed)",
         all(any(p["name"] == "roundtrip_test" and p["passed"] for p in rt_by_id[s["id"]]["proofs"]) for s in inverse_specs)),
        ("deterministic: re-running yields identical proven rows",
         [json.dumps(r, sort_keys=True) for r in proven_rows()] == [json.dumps(r, sort_keys=True) for r in rows]),
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT persisted", wrong["primitive_id"] not in proven_ids),
        ("an un-runnable fixture fails the proof, does not promote", err["serves_truth"] is False and err["promoted"] is False),
        ("manifest proven_count/typed_count match", (
            build_manifest(rows, date="X")["proven_count"] == len(rows)
            and build_manifest(rows, date="X")["typed_count"] == len(rows))),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_leaves_set_relational:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_leaves_set_relational: {len(rows)} WORKABLE set_relational leaf primitives PROVEN end-to-end "
          f"via the imported executed-proof runner (serves_truth=true, L7_executed_proof) AND TYPED with canonical "
          f"edge type ids (typed_count == proven_count == {len(rows)}); {len(inverse_specs)} roundtrip-inverse pairs "
          "prove reversible; a deliberately-wrong leaf and an un-runnable fixture correctly stay candidate.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default=None)
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_pack(date=args.date or _FIXED_DATE)
    print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
