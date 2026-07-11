#!/usr/bin/env python3
"""scripts.prove_leaves_aggregation_reduce — WORKABLE (proven + TYPED) deterministic leaves for the
`aggregation_reduce` family.

ADD-ONLY / flexible-multi-path: this is a NEW parallel path. It IMPORTS the shared machinery
(`scripts.mutator_registry.run_primitive_proof` + `MUTATOR_REGISTRY`) and the pure edge-typing helper
(`scripts.build_edge_type_retrofit.canonicalize_edge`) — it never edits any of them, and it registers its extra
pure mutators via `MUTATOR_REGISTRY.setdefault(...)` (idempotent, never overwrite). No shared JSONL is written; this
agent owns exactly two output files under `data/dev-intel/proven_primitives/` named for this family.

The family reduces a RecordBatch (list of records / a value series) to an AggregateRecord: sum-field, count,
count-distinct, min/max-field, mean/median-field, histogram-bins, top-k-by, running-total, group-count, and more.
Every leaf is a REAL pure deterministic callable `(payload, **kwargs) -> (output, receipt)`; each is run through the
IMPORTED executed-proof runner (`run_primitive_proof`) against a concrete fixture + a hand-written expected output.
serves_truth=true is NEVER hand-set — it is set ONLY by a PASSING executed proof; a leaf that fails or carries a wrong
expected_output stays candidate and is NOT persisted (that gate is the whole point). Every persisted (proven) row is
TYPED: input_edge_type_id = canonicalize_edge(input_edge), output_edge_type_id = canonicalize_edge(output_edge) — the
fix for "proven but untyped" so a workable leaf can chain. Where a leaf has a true inverse (cumulative-sum / diff,
tally-encode / decode) the ROUNDTRIP is proven via has_inverse so the pair is proven reversible.

Deterministic + offline ONLY: no network, no LLM, no wall-clock (fixed literal timestamp), no RNG. CLI:
--self-test (offline, standalone) | --write.
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

# IMPORT the shared machinery — never edit it (ADD-ONLY / flexible-multi-path).
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402
from scripts.mutator_registry import (  # noqa: E402
    INVERSE_PAIRS,
    MUTATOR_REGISTRY,
    _receipt,
    run_primitive_proof,
)

FAMILY = "aggregation_reduce"
OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_aggregation_reduce.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_aggregation_reduce.json"
# Fixed literal timestamp — deterministic, no wall-clock (repo law: no datetime.now / time.time).
GENERATED_UTC = "2026-07-03"


# ── PURE deterministic aggregation/reduce mutators. Each: (payload, **kwargs) -> (output, receipt). ──
# Every one transforms DATA and returns a small receipt; no side effects, no I/O, no wall-clock, no RNG.
def _values(batch: list[dict[str, Any]], field: str) -> list[Any]:
    return [r[field] for r in batch if field in r]


def agg_sum_field(batch: list[dict[str, Any]], field: str) -> tuple[Any, dict[str, Any]]:
    out = sum(_values(batch, field))
    return out, _receipt("agg_sum_field", before=batch, after=out, lossless=False, note=f"sum of '{field}'")


def agg_count_records(batch: list[dict[str, Any]]) -> tuple[int, dict[str, Any]]:
    out = len(batch)
    return out, _receipt("agg_count_records", before=batch, after=out, lossless=False, note="record count")


def agg_count_nonnull_field(batch: list[dict[str, Any]], field: str) -> tuple[int, dict[str, Any]]:
    out = sum(1 for r in batch if r.get(field) is not None)
    return out, _receipt("agg_count_nonnull_field", before=batch, after=out, lossless=False, note=f"non-null count of '{field}'")


def agg_count_distinct_field(batch: list[dict[str, Any]], field: str) -> tuple[int, dict[str, Any]]:
    out = len(set(_values(batch, field)))
    return out, _receipt("agg_count_distinct_field", before=batch, after=out, lossless=False, note=f"distinct count of '{field}'")


def agg_min_field(batch: list[dict[str, Any]], field: str) -> tuple[Any, dict[str, Any]]:
    out = min(_values(batch, field))
    return out, _receipt("agg_min_field", before=batch, after=out, lossless=False, note=f"min of '{field}'")


def agg_max_field(batch: list[dict[str, Any]], field: str) -> tuple[Any, dict[str, Any]]:
    out = max(_values(batch, field))
    return out, _receipt("agg_max_field", before=batch, after=out, lossless=False, note=f"max of '{field}'")


def agg_range_field(batch: list[dict[str, Any]], field: str) -> tuple[Any, dict[str, Any]]:
    vals = _values(batch, field)
    out = max(vals) - min(vals)
    return out, _receipt("agg_range_field", before=batch, after=out, lossless=False, note=f"max-min of '{field}'")


def agg_mean_field(batch: list[dict[str, Any]], field: str) -> tuple[float, dict[str, Any]]:
    vals = _values(batch, field)
    out = sum(vals) / len(vals)
    return out, _receipt("agg_mean_field", before=batch, after=out, lossless=False, note=f"arithmetic mean of '{field}'")


def agg_median_field(batch: list[dict[str, Any]], field: str) -> tuple[float, dict[str, Any]]:
    s = sorted(_values(batch, field))
    n = len(s)
    mid = n // 2
    out = s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2
    return out, _receipt("agg_median_field", before=batch, after=out, lossless=False, note=f"median of '{field}'")


def agg_sum_of_squares_field(batch: list[dict[str, Any]], field: str) -> tuple[Any, dict[str, Any]]:
    out = sum(v * v for v in _values(batch, field))
    return out, _receipt("agg_sum_of_squares_field", before=batch, after=out, lossless=False, note=f"sum of squares of '{field}'")


def agg_product_field(batch: list[dict[str, Any]], field: str) -> tuple[Any, dict[str, Any]]:
    out = 1
    for v in _values(batch, field):
        out *= v
    return out, _receipt("agg_product_field", before=batch, after=out, lossless=False, note=f"product of '{field}'")


def agg_variance_field(batch: list[dict[str, Any]], field: str) -> tuple[float, dict[str, Any]]:
    vals = _values(batch, field)
    mean = sum(vals) / len(vals)
    out = sum((v - mean) ** 2 for v in vals) / len(vals)
    return out, _receipt("agg_variance_field", before=batch, after=out, lossless=False, note=f"population variance of '{field}'")


def agg_stddev_field(batch: list[dict[str, Any]], field: str) -> tuple[float, dict[str, Any]]:
    vals = _values(batch, field)
    mean = sum(vals) / len(vals)
    var = sum((v - mean) ** 2 for v in vals) / len(vals)
    out = var ** 0.5
    return out, _receipt("agg_stddev_field", before=batch, after=out, lossless=False, note=f"population stddev of '{field}'")


def agg_mode_field(batch: list[dict[str, Any]], field: str) -> tuple[Any, dict[str, Any]]:
    counts: dict[Any, int] = {}
    for v in _values(batch, field):
        counts[v] = counts.get(v, 0) + 1
    best = max(counts.values())
    out = sorted(k for k, c in counts.items() if c == best)[0]  # deterministic tie-break: smallest value
    return out, _receipt("agg_mode_field", before=batch, after=out, lossless=False, note=f"mode (min tie-break) of '{field}'")


def agg_percentile_field(batch: list[dict[str, Any]], field: str, p: int) -> tuple[Any, dict[str, Any]]:
    import math
    s = sorted(_values(batch, field))
    rank = max(1, math.ceil(p / 100 * len(s)))  # nearest-rank method
    out = s[rank - 1]
    return out, _receipt("agg_percentile_field", before=batch, after=out, lossless=False, note=f"p{p} (nearest-rank) of '{field}'")


def agg_weighted_mean(batch: list[dict[str, Any]], value_field: str, weight_field: str) -> tuple[float, dict[str, Any]]:
    num = sum(r[value_field] * r[weight_field] for r in batch)
    den = sum(r[weight_field] for r in batch)
    out = num / den
    return out, _receipt("agg_weighted_mean", before=batch, after=out, lossless=False, note=f"weighted mean of '{value_field}' by '{weight_field}'")


def agg_distinct_values(batch: list[dict[str, Any]], field: str) -> tuple[list[Any], dict[str, Any]]:
    out = sorted(set(_values(batch, field)))
    return out, _receipt("agg_distinct_values", before=batch, after=out, lossless=False, note=f"sorted distinct values of '{field}'")


def agg_frequency_table(batch: list[dict[str, Any]], field: str) -> tuple[dict[Any, int], dict[str, Any]]:
    counts: dict[Any, int] = {}
    for v in _values(batch, field):
        counts[v] = counts.get(v, 0) + 1
    out = {k: counts[k] for k in sorted(counts)}
    return out, _receipt("agg_frequency_table", before=batch, after=out, lossless=False, note=f"value->count table of '{field}'")


def agg_histogram_bins(batch: list[dict[str, Any]], field: str, width: int) -> tuple[dict[int, int], dict[str, Any]]:
    counts: dict[int, int] = {}
    for v in _values(batch, field):
        lo = (v // width) * width
        counts[lo] = counts.get(lo, 0) + 1
    out = {k: counts[k] for k in sorted(counts)}
    return out, _receipt("agg_histogram_bins", before=batch, after=out, lossless=False, note=f"fixed-width({width}) histogram of '{field}'")


def agg_group_count(batch: list[dict[str, Any]], key: str) -> tuple[dict[Any, int], dict[str, Any]]:
    counts: dict[Any, int] = {}
    for r in batch:
        k = r.get(key)
        counts[k] = counts.get(k, 0) + 1
    out = {k: counts[k] for k in sorted(counts)}
    return out, _receipt("agg_group_count", before=batch, after=out, lossless=False, note=f"count per '{key}' group")


def agg_group_sum(batch: list[dict[str, Any]], key: str, field: str) -> tuple[dict[Any, Any], dict[str, Any]]:
    sums: dict[Any, Any] = {}
    for r in batch:
        k = r.get(key)
        sums[k] = sums.get(k, 0) + r[field]
    out = {k: sums[k] for k in sorted(sums)}
    return out, _receipt("agg_group_sum", before=batch, after=out, lossless=False, note=f"sum of '{field}' per '{key}' group")


def agg_group_mean(batch: list[dict[str, Any]], key: str, field: str) -> tuple[dict[Any, float], dict[str, Any]]:
    sums: dict[Any, Any] = {}
    cnts: dict[Any, int] = {}
    for r in batch:
        k = r.get(key)
        sums[k] = sums.get(k, 0) + r[field]
        cnts[k] = cnts.get(k, 0) + 1
    out = {k: sums[k] / cnts[k] for k in sorted(sums)}
    return out, _receipt("agg_group_mean", before=batch, after=out, lossless=False, note=f"mean of '{field}' per '{key}' group")


def agg_top_k_by(batch: list[dict[str, Any]], field: str, k: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out = sorted(batch, key=lambda r: r[field], reverse=True)[:k]
    return out, _receipt("agg_top_k_by", before=batch, after=out, lossless=False, note=f"top {k} records by '{field}'")


def agg_bottom_k_by(batch: list[dict[str, Any]], field: str, k: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out = sorted(batch, key=lambda r: r[field])[:k]
    return out, _receipt("agg_bottom_k_by", before=batch, after=out, lossless=False, note=f"bottom {k} records by '{field}'")


def agg_argmax_field(batch: list[dict[str, Any]], field: str, id_field: str) -> tuple[Any, dict[str, Any]]:
    winner = max(batch, key=lambda r: r[field])
    out = winner[id_field]
    return out, _receipt("agg_argmax_field", before=batch, after=out, lossless=False, note=f"'{id_field}' of the max-'{field}' record")


def agg_argmin_field(batch: list[dict[str, Any]], field: str, id_field: str) -> tuple[Any, dict[str, Any]]:
    winner = min(batch, key=lambda r: r[field])
    out = winner[id_field]
    return out, _receipt("agg_argmin_field", before=batch, after=out, lossless=False, note=f"'{id_field}' of the min-'{field}' record")


def agg_first_record(batch: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = batch[0]
    return out, _receipt("agg_first_record", before=batch, after=out, lossless=False, note="first record of the batch")


def agg_last_record(batch: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = batch[-1]
    return out, _receipt("agg_last_record", before=batch, after=out, lossless=False, note="last record of the batch")


def agg_concat_field(batch: list[dict[str, Any]], field: str, sep: str = ",") -> tuple[str, dict[str, Any]]:
    out = sep.join(str(r[field]) for r in batch)
    return out, _receipt("agg_concat_field", before=batch, after=out, lossless=False, note=f"join '{field}' with '{sep}'")


def agg_count_true(batch: list[dict[str, Any]], field: str) -> tuple[int, dict[str, Any]]:
    out = sum(1 for r in batch if r.get(field) is True)
    return out, _receipt("agg_count_true", before=batch, after=out, lossless=False, note=f"count of '{field}' == True")


def agg_any_true(batch: list[dict[str, Any]], field: str) -> tuple[bool, dict[str, Any]]:
    out = any(bool(r.get(field)) for r in batch)
    return out, _receipt("agg_any_true", before=batch, after=out, lossless=False, note=f"logical OR over '{field}'")


def agg_all_true(batch: list[dict[str, Any]], field: str) -> tuple[bool, dict[str, Any]]:
    out = all(bool(r.get(field)) for r in batch)
    return out, _receipt("agg_all_true", before=batch, after=out, lossless=False, note=f"logical AND over '{field}'")


# ── reversible pairs (running-total / diff, tally-encode / decode): the ROUNDTRIP is proven via has_inverse ──
def agg_cumulative_sum(nums: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    out: list[Any] = []
    running = 0
    for x in nums:
        running += x
        out.append(running)
    return out, _receipt("agg_cumulative_sum", before=nums, after=out, lossless=True, note="running total; successive_differences restores it")


def agg_successive_differences(nums: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    out: list[Any] = []
    prev = 0
    for x in nums:
        out.append(x - prev)
        prev = x
    return out, _receipt("agg_successive_differences", before=nums, after=out, lossless=True, note="inverse of cumulative_sum")


def agg_tally_encode(items: list[Any]) -> tuple[list[list[Any]], dict[str, Any]]:
    counts: dict[Any, int] = {}
    for x in items:
        counts[x] = counts.get(x, 0) + 1
    out = [[k, counts[k]] for k in sorted(counts)]
    return out, _receipt("agg_tally_encode", before=items, after=out, lossless=True, note="run-length/tally encode of a sorted series; tally_decode restores it")


def agg_tally_decode(pairs: list[list[Any]]) -> tuple[list[Any], dict[str, Any]]:
    out: list[Any] = []
    for value, count in pairs:
        out.extend([value] * count)
    return out, _receipt("agg_tally_decode", before=pairs, after=out, lossless=True, note="inverse of tally_encode")


#: new pure mutators to plug into the shared registry (idempotent registration; never overwrites existing entries)
_NEW_MUTATORS = {
    "agg_sum_field": agg_sum_field, "agg_count_records": agg_count_records,
    "agg_count_nonnull_field": agg_count_nonnull_field, "agg_count_distinct_field": agg_count_distinct_field,
    "agg_min_field": agg_min_field, "agg_max_field": agg_max_field, "agg_range_field": agg_range_field,
    "agg_mean_field": agg_mean_field, "agg_median_field": agg_median_field,
    "agg_sum_of_squares_field": agg_sum_of_squares_field, "agg_product_field": agg_product_field,
    "agg_variance_field": agg_variance_field, "agg_stddev_field": agg_stddev_field,
    "agg_mode_field": agg_mode_field, "agg_percentile_field": agg_percentile_field,
    "agg_weighted_mean": agg_weighted_mean, "agg_distinct_values": agg_distinct_values,
    "agg_frequency_table": agg_frequency_table, "agg_histogram_bins": agg_histogram_bins,
    "agg_group_count": agg_group_count, "agg_group_sum": agg_group_sum, "agg_group_mean": agg_group_mean,
    "agg_top_k_by": agg_top_k_by, "agg_bottom_k_by": agg_bottom_k_by,
    "agg_argmax_field": agg_argmax_field, "agg_argmin_field": agg_argmin_field,
    "agg_first_record": agg_first_record, "agg_last_record": agg_last_record,
    "agg_concat_field": agg_concat_field, "agg_count_true": agg_count_true,
    "agg_any_true": agg_any_true, "agg_all_true": agg_all_true,
    "agg_cumulative_sum": agg_cumulative_sum, "agg_successive_differences": agg_successive_differences,
    "agg_tally_encode": agg_tally_encode, "agg_tally_decode": agg_tally_decode,
}
_NEW_INVERSE_PAIRS = [("agg_cumulative_sum", "agg_successive_differences"), ("agg_tally_encode", "agg_tally_decode")]


def register_new_mutators() -> None:
    """Plug the extra pure mutators into the shared MUTATOR_REGISTRY (setdefault — idempotent, never overwrite)."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)
    for pair in _NEW_INVERSE_PAIRS:
        if pair not in INVERSE_PAIRS:
            INVERSE_PAIRS.append(pair)


register_new_mutators()


# ── canonical fixtures (deterministic; shared where it keeps expected outputs obvious) ──
# stats batch: sorted values [2,4,4,4,5,5,7,9] -> mean 5.0, median 4.5, var 4.0, stddev 2.0, mode 4, sum 40, ss 232
SB = [{"v": 2}, {"v": 4}, {"v": 4}, {"v": 4}, {"v": 5}, {"v": 5}, {"v": 7}, {"v": 9}]
# small numeric batch: v in {10,20,30,20}
NB = [{"v": 10}, {"v": 20}, {"v": 30}, {"v": 20}]
# grouped batch
GB = [{"g": "a", "x": 10}, {"g": "b", "x": 5}, {"g": "a", "x": 20}, {"g": "b", "x": 5}]
# boolean batch
BB = [{"ok": True}, {"ok": False}, {"ok": True}, {"ok": True}]
# scored batch (top-k / arg*)
TB = [{"id": "x", "score": 5}, {"id": "y", "score": 9}, {"id": "z", "score": 1}]


# spec fields: (id, capability, mutator, fixture, expected, args, inverse, input_edge, output_edge)
LEAF_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:agg_sum_field", "capability": "sum a numeric field across a record batch",
     "mutator": "agg_sum_field", "fixture": SB, "expected": 40, "args": {"field": "v"},
     "input_edge": "RecordBatch", "output_edge": "ScalarAggregate"},
    {"id": "prim:leaf:agg_count_records", "capability": "count records in a batch",
     "mutator": "agg_count_records", "fixture": SB, "expected": 8, "args": {},
     "input_edge": "RecordBatch", "output_edge": "Count"},
    {"id": "prim:leaf:agg_count_nonnull_field", "capability": "count records with a non-null field",
     "mutator": "agg_count_nonnull_field", "fixture": [{"v": 1}, {"v": None}, {"v": 3}], "expected": 2,
     "args": {"field": "v"}, "input_edge": "RecordBatch", "output_edge": "Count"},
    {"id": "prim:leaf:agg_count_distinct_field", "capability": "count distinct values of a field",
     "mutator": "agg_count_distinct_field", "fixture": NB, "expected": 3, "args": {"field": "v"},
     "input_edge": "RecordBatch", "output_edge": "Count"},
    {"id": "prim:leaf:agg_min_field", "capability": "minimum of a field",
     "mutator": "agg_min_field", "fixture": SB, "expected": 2, "args": {"field": "v"},
     "input_edge": "RecordBatch", "output_edge": "ScalarAggregate"},
    {"id": "prim:leaf:agg_max_field", "capability": "maximum of a field",
     "mutator": "agg_max_field", "fixture": SB, "expected": 9, "args": {"field": "v"},
     "input_edge": "RecordBatch", "output_edge": "ScalarAggregate"},
    {"id": "prim:leaf:agg_range_field", "capability": "range (max-min) of a field",
     "mutator": "agg_range_field", "fixture": SB, "expected": 7, "args": {"field": "v"},
     "input_edge": "RecordBatch", "output_edge": "ScalarAggregate"},
    {"id": "prim:leaf:agg_mean_field", "capability": "arithmetic mean of a field",
     "mutator": "agg_mean_field", "fixture": SB, "expected": 5.0, "args": {"field": "v"},
     "input_edge": "RecordBatch", "output_edge": "ScalarAggregate"},
    {"id": "prim:leaf:agg_median_field", "capability": "median of a field",
     "mutator": "agg_median_field", "fixture": SB, "expected": 4.5, "args": {"field": "v"},
     "input_edge": "RecordBatch", "output_edge": "ScalarAggregate"},
    {"id": "prim:leaf:agg_sum_of_squares_field", "capability": "sum of squares of a field",
     "mutator": "agg_sum_of_squares_field", "fixture": SB, "expected": 232, "args": {"field": "v"},
     "input_edge": "RecordBatch", "output_edge": "ScalarAggregate"},
    {"id": "prim:leaf:agg_product_field", "capability": "product of a field",
     "mutator": "agg_product_field", "fixture": [{"v": 2}, {"v": 3}, {"v": 4}], "expected": 24, "args": {"field": "v"},
     "input_edge": "RecordBatch", "output_edge": "ScalarAggregate"},
    {"id": "prim:leaf:agg_variance_field", "capability": "population variance of a field",
     "mutator": "agg_variance_field", "fixture": SB, "expected": 4.0, "args": {"field": "v"},
     "input_edge": "RecordBatch", "output_edge": "ScalarAggregate"},
    {"id": "prim:leaf:agg_stddev_field", "capability": "population standard deviation of a field",
     "mutator": "agg_stddev_field", "fixture": SB, "expected": 2.0, "args": {"field": "v"},
     "input_edge": "RecordBatch", "output_edge": "ScalarAggregate"},
    {"id": "prim:leaf:agg_mode_field", "capability": "mode (min tie-break) of a field",
     "mutator": "agg_mode_field", "fixture": SB, "expected": 4, "args": {"field": "v"},
     "input_edge": "RecordBatch", "output_edge": "ScalarAggregate"},
    {"id": "prim:leaf:agg_percentile_field", "capability": "nearest-rank percentile of a field",
     "mutator": "agg_percentile_field", "fixture": SB, "expected": 9, "args": {"field": "v", "p": 90},
     "input_edge": "RecordBatch", "output_edge": "ScalarAggregate"},
    {"id": "prim:leaf:agg_weighted_mean", "capability": "weighted mean of a field by a weight field",
     "mutator": "agg_weighted_mean", "fixture": [{"v": 10, "w": 1}, {"v": 20, "w": 3}], "expected": 17.5,
     "args": {"value_field": "v", "weight_field": "w"}, "input_edge": "RecordBatch", "output_edge": "ScalarAggregate"},
    {"id": "prim:leaf:agg_distinct_values", "capability": "sorted distinct values of a field",
     "mutator": "agg_distinct_values", "fixture": NB, "expected": [10, 20, 30], "args": {"field": "v"},
     "input_edge": "RecordBatch", "output_edge": "DistinctValueSet"},
    {"id": "prim:leaf:agg_frequency_table", "capability": "value->count frequency table of a field",
     "mutator": "agg_frequency_table", "fixture": NB, "expected": {10: 1, 20: 2, 30: 1}, "args": {"field": "v"},
     "input_edge": "RecordBatch", "output_edge": "FrequencyTable"},
    {"id": "prim:leaf:agg_histogram_bins", "capability": "fixed-width histogram of a field",
     "mutator": "agg_histogram_bins", "fixture": [{"v": 1}, {"v": 3}, {"v": 5}, {"v": 7}, {"v": 9}],
     "expected": {0: 2, 4: 2, 8: 1}, "args": {"field": "v", "width": 4},
     "input_edge": "RecordBatch", "output_edge": "Histogram"},
    {"id": "prim:leaf:agg_group_count", "capability": "count records per group key",
     "mutator": "agg_group_count", "fixture": GB, "expected": {"a": 2, "b": 2}, "args": {"key": "g"},
     "input_edge": "RecordBatch", "output_edge": "GroupCountMap"},
    {"id": "prim:leaf:agg_group_sum", "capability": "sum a field per group key",
     "mutator": "agg_group_sum", "fixture": GB, "expected": {"a": 30, "b": 10}, "args": {"key": "g", "field": "x"},
     "input_edge": "RecordBatch", "output_edge": "GroupAggregateMap"},
    {"id": "prim:leaf:agg_group_mean", "capability": "mean of a field per group key",
     "mutator": "agg_group_mean", "fixture": GB, "expected": {"a": 15.0, "b": 5.0}, "args": {"key": "g", "field": "x"},
     "input_edge": "RecordBatch", "output_edge": "GroupAggregateMap"},
    {"id": "prim:leaf:agg_top_k_by", "capability": "top-k records by a field",
     "mutator": "agg_top_k_by", "fixture": TB, "expected": [{"id": "y", "score": 9}, {"id": "x", "score": 5}],
     "args": {"field": "score", "k": 2}, "input_edge": "RecordBatch", "output_edge": "RankedRecordBatch"},
    {"id": "prim:leaf:agg_bottom_k_by", "capability": "bottom-k records by a field",
     "mutator": "agg_bottom_k_by", "fixture": TB, "expected": [{"id": "z", "score": 1}, {"id": "x", "score": 5}],
     "args": {"field": "score", "k": 2}, "input_edge": "RecordBatch", "output_edge": "RankedRecordBatch"},
    {"id": "prim:leaf:agg_argmax_field", "capability": "id of the record maximizing a field",
     "mutator": "agg_argmax_field", "fixture": TB, "expected": "y", "args": {"field": "score", "id_field": "id"},
     "input_edge": "RecordBatch", "output_edge": "ScalarAggregate"},
    {"id": "prim:leaf:agg_argmin_field", "capability": "id of the record minimizing a field",
     "mutator": "agg_argmin_field", "fixture": TB, "expected": "z", "args": {"field": "score", "id_field": "id"},
     "input_edge": "RecordBatch", "output_edge": "ScalarAggregate"},
    {"id": "prim:leaf:agg_first_record", "capability": "first record of a batch",
     "mutator": "agg_first_record", "fixture": NB, "expected": {"v": 10}, "args": {},
     "input_edge": "RecordBatch", "output_edge": "AggregateRecord"},
    {"id": "prim:leaf:agg_last_record", "capability": "last record of a batch",
     "mutator": "agg_last_record", "fixture": NB, "expected": {"v": 20}, "args": {},
     "input_edge": "RecordBatch", "output_edge": "AggregateRecord"},
    {"id": "prim:leaf:agg_concat_field", "capability": "concatenate a string field across records",
     "mutator": "agg_concat_field", "fixture": [{"s": "a"}, {"s": "b"}, {"s": "c"}], "expected": "a,b,c",
     "args": {"field": "s", "sep": ","}, "input_edge": "RecordBatch", "output_edge": "Text"},
    {"id": "prim:leaf:agg_count_true", "capability": "count records where a field is True",
     "mutator": "agg_count_true", "fixture": BB, "expected": 3, "args": {"field": "ok"},
     "input_edge": "RecordBatch", "output_edge": "Count"},
    {"id": "prim:leaf:agg_any_true", "capability": "logical OR over a boolean field",
     "mutator": "agg_any_true", "fixture": BB, "expected": True, "args": {"field": "ok"},
     "input_edge": "RecordBatch", "output_edge": "Boolean"},
    {"id": "prim:leaf:agg_all_true", "capability": "logical AND over a boolean field",
     "mutator": "agg_all_true", "fixture": BB, "expected": False, "args": {"field": "ok"},
     "input_edge": "RecordBatch", "output_edge": "Boolean"},
    # reversible pairs — the ROUNDTRIP is proven via has_inverse
    {"id": "prim:leaf:agg_cumulative_sum", "capability": "running total of a number series (roundtrips)",
     "mutator": "agg_cumulative_sum", "fixture": [1, 2, 3], "expected": [1, 3, 6], "args": {},
     "inverse": "agg_successive_differences", "input_edge": "NumberSeries", "output_edge": "CumulativeSeries"},
    {"id": "prim:leaf:agg_successive_differences", "capability": "successive differences (inverse of running total)",
     "mutator": "agg_successive_differences", "fixture": [1, 3, 6], "expected": [1, 2, 3], "args": {},
     "input_edge": "CumulativeSeries", "output_edge": "NumberSeries"},
    {"id": "prim:leaf:agg_tally_encode", "capability": "tally/run-length encode a sorted series (roundtrips)",
     "mutator": "agg_tally_encode", "fixture": [1, 1, 2, 3, 3, 3], "expected": [[1, 2], [2, 1], [3, 3]], "args": {},
     "inverse": "agg_tally_decode", "input_edge": "NumberSeries", "output_edge": "TallyTable"},
    {"id": "prim:leaf:agg_tally_decode", "capability": "expand a tally table back to a series (inverse of tally-encode)",
     "mutator": "agg_tally_decode", "fixture": [[1, 2], [2, 1]], "expected": [1, 1, 2], "args": {},
     "input_edge": "TallyTable", "output_edge": "NumberSeries"},
]

#: deliberately-wrong leaves — the executed-proof gate MUST leave these candidate (never persisted as proven)
NEGATIVE_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:WRONG_sum", "capability": "agg_sum_field with a wrong expected output (must stay candidate)",
     "mutator": "agg_sum_field", "fixture": SB, "expected": 999, "args": {"field": "v"},
     "input_edge": "RecordBatch", "output_edge": "ScalarAggregate"},
]


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    receipt = run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )
    receipt["capability"] = spec["capability"]
    receipt["input_edge"] = spec["input_edge"]
    receipt["output_edge"] = spec["output_edge"]
    return receipt


def prove_all() -> list[dict[str, Any]]:
    """Run every declared leaf primitive through the IMPORTED executed-proof runner."""
    return [_prove_one(s) for s in LEAF_SPECS]


def _typed_row(receipt: dict[str, Any]) -> dict[str, Any]:
    """A persisted WORKABLE row: proven (serves_truth=true) AND typed (canonical edge type ids)."""
    return {
        "record_type": "proven_primitive",
        "primitive_id": receipt["primitive_id"],
        "mutator": receipt["mutator"],
        "capability": receipt["capability"],
        "family": FAMILY,
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": receipt["input_edge"],
        "output_edge": receipt["output_edge"],
        "input_edge_type_id": canonicalize_edge(receipt["input_edge"]),
        "output_edge_type_id": canonicalize_edge(receipt["output_edge"]),
        "proofs": receipt["proofs"],
        "input_hash": receipt["input_hash"],
        "output_hash": receipt["output_hash"],
    }


def build_rows() -> list[dict[str, Any]]:
    """Prove every leaf; keep ONLY passers (serves_truth=true); TYPE each surviving row via canonicalize_edge."""
    rows = [_typed_row(r) for r in prove_all() if r["serves_truth"] is True and r.get("promoted") is True]
    return sorted(rows, key=lambda r: r["primitive_id"])


def build_manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"]]
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    return {
        "record_type": "proven_primitives_manifest",
        "family": FAMILY,
        "pack_id": f"proven-{FAMILY}",
        "generator": "scripts/prove_leaves_aggregation_reduce.py",
        "generated_utc": GENERATED_UTC,
        "declared_leaf_count": len(LEAF_SPECS),
        "proven_count": len(rows),
        "typed_count": len(typed),
        "verification_level": "L7_executed_proof",
        "proven_primitive_ids": [r["primitive_id"] for r in rows],
        "edge_type_ids": sorted({r["input_edge_type_id"] for r in rows} | {r["output_edge_type_id"] for r in rows}),
        "note": "serves_truth=true is set ONLY by a PASSING executed proof (run_primitive_proof, imported from "
                "scripts/mutator_registry.py); a wrong-expected leaf stays candidate and is never persisted here. "
                "Every persisted row is TYPED (canonicalize_edge) so the workable leaf can chain.",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def write_pack() -> dict[str, Any]:
    rows = build_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(rows)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    receipts = prove_all()
    rows = build_rows()
    ids = [r["primitive_id"] for r in receipts]
    proven = [r for r in receipts if r["serves_truth"] is True and r.get("promoted") is True]

    # a deliberately-wrong leaf must stay candidate (the gate is real, not a rubber stamp)
    wrong = _prove_one(NEGATIVE_SPECS[0])
    persisted_ids = {r["primitive_id"] for r in rows}
    # a second wrong path: pass a fixture the mutator cannot handle -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:EXEC_ERROR", "agg_sum_field", object(), "irrelevant", mutator_args={"field": "v"})
    # roundtrip inverse pairs must actually prove reversible
    rt_specs = [s for s in LEAF_SPECS if s.get("inverse")]
    proven_by_id = {r["primitive_id"]: r for r in proven}

    checks: list[tuple[str, bool]] = [
        (">=28 leaf primitives declared", len(LEAF_SPECS) >= 28),
        ("unique primitive ids", len(set(ids)) == len(ids)),
        (">=28 leaves PROVE serves_truth=true via an executed proof", len(proven) >= 28),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"]) for r in proven)),
        ("proven_count == number of persisted rows", len(proven) == len(rows)),
        ("EVERY persisted row carries a non-null input_edge_type_id",
         all(bool(r["input_edge_type_id"]) for r in rows)),
        ("EVERY persisted row carries a non-null output_edge_type_id",
         all(bool(r["output_edge_type_id"]) for r in rows)),
        ("typed_count == proven_count (every workable leaf is typed)",
         build_manifest(rows)["typed_count"] == build_manifest(rows)["proven_count"] == len(rows)),
        ("input_edge_type_id canonicalizes RecordBatch correctly", canonicalize_edge("RecordBatch") == "RecordBatch"),
        ("roundtrip leaves actually ran a passing roundtrip proof", len(rt_specs) >= 2 and all(
            any(p["name"] == "roundtrip_test" and p["passed"] for p in proven_by_id[s["id"]]["proofs"])
            for s in rt_specs)),
        ("deterministic: re-running yields identical persisted rows",
         [json.dumps(r, sort_keys=True) for r in build_rows()] == [json.dumps(r, sort_keys=True) for r in rows]),
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT persisted", wrong["primitive_id"] not in persisted_ids),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_leaves_aggregation_reduce:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_leaves_aggregation_reduce: {len(proven)} WORKABLE (proven + TYPED) leaf primitives for the "
          f"'{FAMILY}' family — serves_truth=true set ONLY by an executed passing proof; every persisted row carries "
          f"canonical input/output edge type ids; {len(rt_specs)} roundtrip-inverse pairs proven reversible; a "
          "wrong-expected leaf and an un-runnable fixture correctly stay candidate.")
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
