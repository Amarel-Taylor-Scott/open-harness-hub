#!/usr/bin/env python3
"""scripts.prove_leaves_numeric_math — WORKABLE (proven + TYPED) deterministic leaf primitives for 'numeric_math'.

Vocabulary is not capability, and a proven leaf that carries no canonical edge type cannot CHAIN. This module is the
fix for the numeric_math family: it declares >=28 REAL pure deterministic leaf primitives (clamp, round-half-up,
scale/normalize-to-01, min-max-normalize, gcd/lcm, bucketize, safe-divide, percent, sign, cumulative-sum, running
extrema, mean/median/sum/product, dot, negate/reciprocal, int<->str), runs EVERY ONE through the imported
`run_primitive_proof` (which EXECUTES the mutator against a fixture and flips serves_truth false->true ONLY on a
passing executed proof), keeps ONLY the passers, and — critically — TYPES every persisted row via the imported
`canonicalize_edge` so each workable leaf carries a canonical input_edge_type_id + output_edge_type_id and can compose.

ADD-ONLY / flexible-multi-path: this is a NEW parallel path. It IMPORTS the shared machinery
(`scripts.mutator_registry`, `scripts.build_edge_type_retrofit`) and never edits it; it plugs a family of new PURE
numeric mutators into the shared MUTATOR_REGISTRY via `setdefault` (registration, not a rewrite; idempotent). Where a
leaf has a true inverse (negate/negate, reciprocal/reciprocal, int->str / str->int) the ROUNDTRIP is proven via
has_inverse so the pair is proven reversible. serves_truth=true here is CORRECT and required — set ONLY by an
executed passing proof; a deliberately-wrong-expected leaf stays candidate and is NEVER persisted. Offline +
deterministic (no wall-clock/RNG/network in bodies; fixed literal timestamp). CLI: --self-test | --write [--date D].
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import math
import sys
from decimal import ROUND_HALF_UP, Decimal
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

OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_numeric_math.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_numeric_math.json"
FAMILY = "numeric_math"
# Fixed literal timestamp — no wall-clock (deterministic, offline).
DEFAULT_DATE = "2026-07-03"

# The (script_path, module_name) tuple the parent workflow must register in flywheel_proof_modules.py.
REGISTER_TUPLE = ("scripts/prove_leaves_numeric_math.py", "scripts.prove_leaves_numeric_math")


# ── PURE deterministic numeric mutators: each (transformed_output, receipt). No I/O, no side effects. ──
def _r(name: str, before: Any, after: Any, note: str, *, lossless: bool = False) -> dict[str, Any]:
    return _receipt(name, before=before, after=after, lossless=lossless, note=note)


def numeric_clamp(value: float, lo: float, hi: float) -> tuple[float, dict[str, Any]]:
    out = max(lo, min(hi, value))
    return out, _r("numeric_clamp", value, out, f"clamp to [{lo},{hi}]")


def numeric_clamp_unit(value: float) -> tuple[float, dict[str, Any]]:
    out = max(0.0, min(1.0, float(value)))
    return out, _r("numeric_clamp_unit", value, out, "clamp to the unit interval [0,1]")


def numeric_round_half_up(value: float, ndigits: int = 0) -> tuple[float, dict[str, Any]]:
    # Decimal ROUND_HALF_UP: ties go away from zero (2.5->3, -2.5->-3), unlike Python's banker's round().
    q = Decimal(f"1e-{ndigits}") if ndigits > 0 else Decimal(1)
    out = float(Decimal(str(value)).quantize(q, rounding=ROUND_HALF_UP))
    return out, _r("numeric_round_half_up", value, out, f"round half-up to {ndigits} places")


def numeric_scale_to_01(value: float, lo: float, hi: float) -> tuple[float, dict[str, Any]]:
    out = 0.0 if hi == lo else (value - lo) / (hi - lo)
    return out, _r("numeric_scale_to_01", value, out, f"linear scale of value from [{lo},{hi}] to [0,1]")


def numeric_minmax_normalize(items: list[float]) -> tuple[list[float], dict[str, Any]]:
    lo, hi = min(items), max(items)
    span = hi - lo
    out = [0.0 for _ in items] if span == 0 else [(x - lo) / span for x in items]
    return out, _r("numeric_minmax_normalize", items, out, "min-max normalize a list into [0,1]")


def numeric_gcd(pair: list[int]) -> tuple[int, dict[str, Any]]:
    out = math.gcd(int(pair[0]), int(pair[1]))
    return out, _r("numeric_gcd", pair, out, "greatest common divisor of a pair")


def numeric_lcm(pair: list[int]) -> tuple[int, dict[str, Any]]:
    a, b = int(pair[0]), int(pair[1])
    g = math.gcd(a, b)
    out = 0 if g == 0 else abs(a * b) // g
    return out, _r("numeric_lcm", pair, out, "least common multiple of a pair")


def numeric_gcd_list(items: list[int]) -> tuple[int, dict[str, Any]]:
    out = 0
    for x in items:
        out = math.gcd(out, int(x))
    return out, _r("numeric_gcd_list", items, out, "gcd reduced over a list")


def numeric_lcm_list(items: list[int]) -> tuple[int, dict[str, Any]]:
    out = 1
    for x in items:
        x = int(x)
        g = math.gcd(out, x)
        out = 0 if g == 0 else abs(out * x) // g
    return out, _r("numeric_lcm_list", items, out, "lcm reduced over a list")


def numeric_bucketize(value: float, boundaries: list[float]) -> tuple[int, dict[str, Any]]:
    # Bucket index = count of ascending boundaries that value meets/exceeds (right-open bins).
    out = sum(1 for b in boundaries if b <= value)
    return out, _r("numeric_bucketize", value, out, f"bucket index into boundaries {boundaries}")


def numeric_safe_divide(pair: list[float], default: float = 0.0) -> tuple[float, dict[str, Any]]:
    a, b = pair[0], pair[1]
    out = default if b == 0 else a / b
    return out, _r("numeric_safe_divide", pair, out, "a/b with divide-by-zero -> default")


def numeric_percent(pair: list[float]) -> tuple[float, dict[str, Any]]:
    part, whole = pair[0], pair[1]
    out = 0.0 if whole == 0 else part / whole * 100.0
    return out, _r("numeric_percent", pair, out, "part/whole as a percentage")


def numeric_percent_of(pair: list[float]) -> tuple[float, dict[str, Any]]:
    base, pct = pair[0], pair[1]
    out = base * pct / 100.0
    return out, _r("numeric_percent_of", pair, out, "pct percent of base")


def numeric_sign(value: float) -> tuple[int, dict[str, Any]]:
    out = (value > 0) - (value < 0)
    return out, _r("numeric_sign", value, out, "sign: -1 / 0 / 1")


def numeric_cumulative_sum(items: list[float]) -> tuple[list[float], dict[str, Any]]:
    out: list[float] = []
    acc = 0
    for x in items:
        acc += x
        out.append(acc)
    return out, _r("numeric_cumulative_sum", items, out, "running cumulative sum")


def numeric_running_max(items: list[float]) -> tuple[list[float], dict[str, Any]]:
    out: list[float] = []
    cur = None
    for x in items:
        cur = x if cur is None else max(cur, x)
        out.append(cur)
    return out, _r("numeric_running_max", items, out, "running maximum")


def numeric_running_min(items: list[float]) -> tuple[list[float], dict[str, Any]]:
    out: list[float] = []
    cur = None
    for x in items:
        cur = x if cur is None else min(cur, x)
        out.append(cur)
    return out, _r("numeric_running_min", items, out, "running minimum")


def numeric_abs(value: float) -> tuple[float, dict[str, Any]]:
    out = abs(value)
    return out, _r("numeric_abs", value, out, "absolute value")


def numeric_scale(value: float, factor: float) -> tuple[float, dict[str, Any]]:
    out = value * factor
    return out, _r("numeric_scale", value, out, f"multiply by {factor}")


def numeric_ceil(value: float) -> tuple[int, dict[str, Any]]:
    out = math.ceil(value)
    return out, _r("numeric_ceil", value, out, "ceiling")


def numeric_floor(value: float) -> tuple[int, dict[str, Any]]:
    out = math.floor(value)
    return out, _r("numeric_floor", value, out, "floor")


def numeric_trunc(value: float) -> tuple[int, dict[str, Any]]:
    out = math.trunc(value)
    return out, _r("numeric_trunc", value, out, "truncate toward zero")


def numeric_mean(items: list[float]) -> tuple[float, dict[str, Any]]:
    out = sum(items) / len(items)
    return out, _r("numeric_mean", items, out, "arithmetic mean")


def numeric_median(items: list[float]) -> tuple[float, dict[str, Any]]:
    s = sorted(items)
    n = len(s)
    mid = n // 2
    out = s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2
    return out, _r("numeric_median", items, out, "median")


def numeric_sum(items: list[float]) -> tuple[float, dict[str, Any]]:
    out = sum(items)
    return out, _r("numeric_sum", items, out, "sum")


def numeric_product(items: list[float]) -> tuple[float, dict[str, Any]]:
    out = 1
    for x in items:
        out *= x
    return out, _r("numeric_product", items, out, "product")


def numeric_min(items: list[float]) -> tuple[float, dict[str, Any]]:
    out = min(items)
    return out, _r("numeric_min", items, out, "minimum")


def numeric_max(items: list[float]) -> tuple[float, dict[str, Any]]:
    out = max(items)
    return out, _r("numeric_max", items, out, "maximum")


def numeric_range_span(items: list[float]) -> tuple[float, dict[str, Any]]:
    out = max(items) - min(items)
    return out, _r("numeric_range_span", items, out, "max minus min")


def numeric_dot(pair: list[list[float]]) -> tuple[float, dict[str, Any]]:
    a, b = pair[0], pair[1]
    out = sum(x * y for x, y in zip(a, b))
    return out, _r("numeric_dot", pair, out, "dot product of two equal-length vectors")


def numeric_negate(value: float) -> tuple[float, dict[str, Any]]:
    out = -value
    return out, _r("numeric_negate", value, out, "negate; self-inverse (roundtrips)", lossless=True)


def numeric_reciprocal(value: float) -> tuple[float, dict[str, Any]]:
    out = 1 / value
    return out, _r("numeric_reciprocal", value, out, "reciprocal; self-inverse for nonzero (roundtrips)", lossless=True)


def numeric_int_to_str(value: int) -> tuple[str, dict[str, Any]]:
    out = str(int(value))
    return out, _r("numeric_int_to_str", value, out, "emit int as canonical decimal string; parse restores", lossless=True)


def numeric_str_to_int(text: str) -> tuple[int, dict[str, Any]]:
    out = int(str(text))
    return out, _r("numeric_str_to_int", text, out, "parse a decimal string to int; emit restores", lossless=True)


#: new pure numeric mutators to plug into the shared registry (idempotent setdefault; never overwrites).
_NEW_MUTATORS: dict[str, Any] = {
    "numeric_clamp": numeric_clamp, "numeric_clamp_unit": numeric_clamp_unit,
    "numeric_round_half_up": numeric_round_half_up, "numeric_scale_to_01": numeric_scale_to_01,
    "numeric_minmax_normalize": numeric_minmax_normalize, "numeric_gcd": numeric_gcd, "numeric_lcm": numeric_lcm,
    "numeric_gcd_list": numeric_gcd_list, "numeric_lcm_list": numeric_lcm_list, "numeric_bucketize": numeric_bucketize,
    "numeric_safe_divide": numeric_safe_divide, "numeric_percent": numeric_percent,
    "numeric_percent_of": numeric_percent_of, "numeric_sign": numeric_sign,
    "numeric_cumulative_sum": numeric_cumulative_sum, "numeric_running_max": numeric_running_max,
    "numeric_running_min": numeric_running_min, "numeric_abs": numeric_abs, "numeric_scale": numeric_scale,
    "numeric_ceil": numeric_ceil, "numeric_floor": numeric_floor, "numeric_trunc": numeric_trunc,
    "numeric_mean": numeric_mean, "numeric_median": numeric_median, "numeric_sum": numeric_sum,
    "numeric_product": numeric_product, "numeric_min": numeric_min, "numeric_max": numeric_max,
    "numeric_range_span": numeric_range_span, "numeric_dot": numeric_dot, "numeric_negate": numeric_negate,
    "numeric_reciprocal": numeric_reciprocal, "numeric_int_to_str": numeric_int_to_str,
    "numeric_str_to_int": numeric_str_to_int,
}
# Inverse pairs (for roundtrip proofs). Self-inverse leaves list the same name both sides.
_NEW_INVERSE_PAIRS: list[tuple[str, str]] = [
    ("numeric_negate", "numeric_negate"), ("numeric_reciprocal", "numeric_reciprocal"),
    ("numeric_int_to_str", "numeric_str_to_int"), ("numeric_str_to_int", "numeric_int_to_str"),
]


def register_new_mutators() -> None:
    """Plug the numeric mutators into the shared MUTATOR_REGISTRY (registration, not a rewrite). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)
    for pair in _NEW_INVERSE_PAIRS:
        if pair not in INVERSE_PAIRS:
            INVERSE_PAIRS.append(pair)


register_new_mutators()


# ── the leaf primitives: each a REAL numeric capability with a concrete fixture + independently-computed expected ──
# spec fields: id, mutator, fixture, expected, args, inverse, input_edge, output_edge
LEAF_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:numeric_clamp_high", "mutator": "numeric_clamp", "fixture": 15, "expected": 10,
     "args": {"lo": 0, "hi": 10}, "input_edge": "Number", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_clamp_low", "mutator": "numeric_clamp", "fixture": -5, "expected": 0,
     "args": {"lo": 0, "hi": 10}, "input_edge": "Number", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_clamp_inside", "mutator": "numeric_clamp", "fixture": 4, "expected": 4,
     "args": {"lo": 0, "hi": 10}, "input_edge": "Number", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_clamp_unit", "mutator": "numeric_clamp_unit", "fixture": 1.5, "expected": 1.0,
     "args": {}, "input_edge": "Number", "output_edge": "UnitInterval"},
    {"id": "prim:leaf:numeric_round_half_up_tie", "mutator": "numeric_round_half_up", "fixture": 2.5, "expected": 3.0,
     "args": {"ndigits": 0}, "input_edge": "Number", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_round_half_up_2dp", "mutator": "numeric_round_half_up", "fixture": 2.675,
     "expected": 2.68, "args": {"ndigits": 2}, "input_edge": "Number", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_round_half_up_neg_tie", "mutator": "numeric_round_half_up", "fixture": -2.5,
     "expected": -3.0, "args": {"ndigits": 0}, "input_edge": "Number", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_scale_to_01", "mutator": "numeric_scale_to_01", "fixture": 5, "expected": 0.5,
     "args": {"lo": 0, "hi": 10}, "input_edge": "Number", "output_edge": "UnitInterval"},
    {"id": "prim:leaf:numeric_minmax_normalize", "mutator": "numeric_minmax_normalize", "fixture": [0, 5, 10],
     "expected": [0.0, 0.5, 1.0], "args": {}, "input_edge": "NumberList", "output_edge": "UnitIntervalList"},
    {"id": "prim:leaf:numeric_gcd", "mutator": "numeric_gcd", "fixture": [12, 18], "expected": 6,
     "args": {}, "input_edge": "NumberPair", "output_edge": "Integer"},
    {"id": "prim:leaf:numeric_lcm", "mutator": "numeric_lcm", "fixture": [4, 6], "expected": 12,
     "args": {}, "input_edge": "NumberPair", "output_edge": "Integer"},
    {"id": "prim:leaf:numeric_gcd_list", "mutator": "numeric_gcd_list", "fixture": [12, 18, 24], "expected": 6,
     "args": {}, "input_edge": "NumberList", "output_edge": "Integer"},
    {"id": "prim:leaf:numeric_lcm_list", "mutator": "numeric_lcm_list", "fixture": [2, 3, 4], "expected": 12,
     "args": {}, "input_edge": "NumberList", "output_edge": "Integer"},
    {"id": "prim:leaf:numeric_bucketize", "mutator": "numeric_bucketize", "fixture": 25, "expected": 2,
     "args": {"boundaries": [10, 20, 30]}, "input_edge": "Number", "output_edge": "Integer"},
    {"id": "prim:leaf:numeric_bucketize_low", "mutator": "numeric_bucketize", "fixture": 5, "expected": 0,
     "args": {"boundaries": [10, 20, 30]}, "input_edge": "Number", "output_edge": "Integer"},
    {"id": "prim:leaf:numeric_safe_divide", "mutator": "numeric_safe_divide", "fixture": [10, 2], "expected": 5.0,
     "args": {}, "input_edge": "NumberPair", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_safe_divide_zero", "mutator": "numeric_safe_divide", "fixture": [10, 0], "expected": 0.0,
     "args": {"default": 0.0}, "input_edge": "NumberPair", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_percent", "mutator": "numeric_percent", "fixture": [1, 4], "expected": 25.0,
     "args": {}, "input_edge": "NumberPair", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_percent_of", "mutator": "numeric_percent_of", "fixture": [200, 15], "expected": 30.0,
     "args": {}, "input_edge": "NumberPair", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_sign_neg", "mutator": "numeric_sign", "fixture": -3, "expected": -1,
     "args": {}, "input_edge": "Number", "output_edge": "Integer"},
    {"id": "prim:leaf:numeric_sign_zero", "mutator": "numeric_sign", "fixture": 0, "expected": 0,
     "args": {}, "input_edge": "Number", "output_edge": "Integer"},
    {"id": "prim:leaf:numeric_sign_pos", "mutator": "numeric_sign", "fixture": 7, "expected": 1,
     "args": {}, "input_edge": "Number", "output_edge": "Integer"},
    {"id": "prim:leaf:numeric_cumulative_sum", "mutator": "numeric_cumulative_sum", "fixture": [1, 2, 3, 4],
     "expected": [1, 3, 6, 10], "args": {}, "input_edge": "NumberList", "output_edge": "NumberList"},
    {"id": "prim:leaf:numeric_running_max", "mutator": "numeric_running_max", "fixture": [1, 3, 2, 5, 4],
     "expected": [1, 3, 3, 5, 5], "args": {}, "input_edge": "NumberList", "output_edge": "NumberList"},
    {"id": "prim:leaf:numeric_running_min", "mutator": "numeric_running_min", "fixture": [5, 3, 4, 1, 2],
     "expected": [5, 3, 3, 1, 1], "args": {}, "input_edge": "NumberList", "output_edge": "NumberList"},
    {"id": "prim:leaf:numeric_abs", "mutator": "numeric_abs", "fixture": -4, "expected": 4,
     "args": {}, "input_edge": "Number", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_scale", "mutator": "numeric_scale", "fixture": 5, "expected": 10,
     "args": {"factor": 2}, "input_edge": "Number", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_ceil", "mutator": "numeric_ceil", "fixture": 4.2, "expected": 5,
     "args": {}, "input_edge": "Number", "output_edge": "Integer"},
    {"id": "prim:leaf:numeric_floor", "mutator": "numeric_floor", "fixture": 4.8, "expected": 4,
     "args": {}, "input_edge": "Number", "output_edge": "Integer"},
    {"id": "prim:leaf:numeric_trunc", "mutator": "numeric_trunc", "fixture": -4.7, "expected": -4,
     "args": {}, "input_edge": "Number", "output_edge": "Integer"},
    {"id": "prim:leaf:numeric_mean", "mutator": "numeric_mean", "fixture": [2, 4, 6], "expected": 4.0,
     "args": {}, "input_edge": "NumberList", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_median", "mutator": "numeric_median", "fixture": [3, 1, 2], "expected": 2,
     "args": {}, "input_edge": "NumberList", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_sum", "mutator": "numeric_sum", "fixture": [1, 2, 3], "expected": 6,
     "args": {}, "input_edge": "NumberList", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_product", "mutator": "numeric_product", "fixture": [1, 2, 3, 4], "expected": 24,
     "args": {}, "input_edge": "NumberList", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_min", "mutator": "numeric_min", "fixture": [3, 1, 2], "expected": 1,
     "args": {}, "input_edge": "NumberList", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_max", "mutator": "numeric_max", "fixture": [3, 1, 2], "expected": 3,
     "args": {}, "input_edge": "NumberList", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_range_span", "mutator": "numeric_range_span", "fixture": [1, 5, 3], "expected": 4,
     "args": {}, "input_edge": "NumberList", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_dot", "mutator": "numeric_dot", "fixture": [[1, 2], [3, 4]], "expected": 11,
     "args": {}, "input_edge": "NumberVectorPair", "output_edge": "Number"},
    # roundtrip-inverse leaves — proven reversible via has_inverse
    {"id": "prim:leaf:numeric_negate", "mutator": "numeric_negate", "fixture": 5, "expected": -5,
     "args": {}, "inverse": "numeric_negate", "input_edge": "Number", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_reciprocal", "mutator": "numeric_reciprocal", "fixture": 4, "expected": 0.25,
     "args": {}, "inverse": "numeric_reciprocal", "input_edge": "Number", "output_edge": "Number"},
    {"id": "prim:leaf:numeric_int_to_str", "mutator": "numeric_int_to_str", "fixture": 42, "expected": "42",
     "args": {}, "inverse": "numeric_str_to_int", "input_edge": "Integer", "output_edge": "Text"},
    {"id": "prim:leaf:numeric_str_to_int", "mutator": "numeric_str_to_int", "fixture": "99", "expected": 99,
     "args": {}, "inverse": "numeric_int_to_str", "input_edge": "Text", "output_edge": "Integer"},
]

#: deliberately-wrong leaf — the proof gate MUST leave this candidate (never persisted as proven).
NEGATIVE_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:numeric_WRONG_expected", "mutator": "numeric_clamp", "fixture": 15, "expected": 999,
     "args": {"lo": 0, "hi": 10}, "input_edge": "Number", "output_edge": "Number"},
]

_SPEC_BY_ID: dict[str, dict[str, Any]] = {s["id"]: s for s in LEAF_SPECS}


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    receipt = run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )
    return receipt


def prove_all() -> list[dict[str, Any]]:
    """Run every declared leaf through the imported executed-proof runner."""
    return [_prove_one(s) for s in LEAF_SPECS]


def proven_primitive_index() -> dict[str, dict[str, Any]]:
    """{primitive_id -> receipt} for leaves whose executed proof PASSED (serves_truth=true)."""
    return {r["primitive_id"]: r for r in prove_all() if r["serves_truth"] is True}


def build_rows() -> list[dict[str, Any]]:
    """TYPE + assemble the persisted rows for every PROVEN leaf. Each carries canonical edge type ids."""
    index = proven_primitive_index()
    rows: list[dict[str, Any]] = []
    for pid in sorted(index):
        spec = _SPEC_BY_ID[pid]
        input_edge = spec["input_edge"]
        output_edge = spec["output_edge"]
        rows.append({
            "primitive_id": pid,
            "mutator": spec["mutator"],
            "family": FAMILY,
            "serves_truth": True,
            "candidate": False,
            "verification_level": "L7_executed_proof",
            "input_edge": input_edge,
            "output_edge": output_edge,
            # THE fix for 'proven but untyped' — a workable leaf MUST carry canonical edge types so it can chain.
            "input_edge_type_id": canonicalize_edge(input_edge),
            "output_edge_type_id": canonicalize_edge(output_edge),
            "has_inverse": spec.get("inverse"),
            "output_hash": index[pid]["output_hash"],
        })
    return rows


def build_manifest(rows: list[dict[str, Any]], *, date: str) -> dict[str, Any]:
    typed = [r for r in rows if r.get("input_edge_type_id") and r.get("output_edge_type_id")]
    return {
        "record_type": "proven_numeric_math_manifest",
        "pack_id": "proven-leaf-primitives-numeric-math",
        "generator": "scripts/prove_leaves_numeric_math.py",
        "family": FAMILY,
        "generated_utc": date,
        "declared_leaf_count": len(LEAF_SPECS),
        "proven_count": len(rows),
        "typed_count": len(typed),
        "verification_level": "L7_executed_proof",
        "proven_primitive_ids": [r["primitive_id"] for r in rows],
        "register_tuple": list(REGISTER_TUPLE),
        "note": "serves_truth=true is set ONLY by an executed passing proof (run_primitive_proof, imported from "
                "scripts/mutator_registry.py); every persisted row is TYPED via canonicalize_edge (imported from "
                "scripts/build_edge_type_retrofit.py) so proven leaves can compose. A deliberately-wrong leaf "
                "stays candidate and is never persisted.",
    }


def write_pack(*, date: str) -> dict[str, Any]:
    rows = build_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(rows, date=date)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    receipts = prove_all()
    index = proven_primitive_index()
    rows = build_rows()
    ids = [r["primitive_id"] for r in receipts]

    # a deliberately-wrong leaf must stay candidate (the gate is real, not a rubber stamp)
    wrong = _prove_one(NEGATIVE_SPECS[0])
    # an un-runnable fixture -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:numeric_EXEC_ERROR", "numeric_sum", 123, "irrelevant")

    inverse_specs = [s for s in LEAF_SPECS if s.get("inverse")]

    checks: list[tuple[str, bool]] = [
        (">=28 leaf primitives declared", len(LEAF_SPECS) >= 28),
        ("unique primitive ids", len(set(ids)) == len(ids)),
        (">=28 leaves PROVE serves_truth=true via an executed proof", len(index) >= 28),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(index[p]["verification_level"] == "L7_executed_proof" and all(q["passed"] for q in index[p]["proofs"])
             for p in index)),
        ("EVERY persisted row carries non-null input_edge_type_id + output_edge_type_id",
         all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in rows)),
        ("persisted rows == proven count (typed_count == proven_count)",
         len(rows) == len(index) and len(rows) >= 28),
        ("persisted rows all serves_truth=true / candidate=false / typed L7",
         all(r["serves_truth"] is True and r["candidate"] is False
             and r["verification_level"] == "L7_executed_proof" for r in rows)),
        ("roundtrip-inverse pairs prove reversible (roundtrip_test passed)",
         bool(inverse_specs) and all(
             any(q["name"] == "roundtrip_test" and q["passed"] for q in index[s["id"]]["proofs"])
             for s in inverse_specs)),
        ("deterministic: re-running yields identical receipts",
         [json.dumps(r, sort_keys=True) for r in prove_all()]
         == [json.dumps(r, sort_keys=True) for r in receipts]),
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT in the proven index / not persisted",
         wrong["primitive_id"] not in index and wrong["primitive_id"] not in {r["primitive_id"] for r in rows}),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("manifest proven_count/typed_count agree and typed_count == proven_count",
         (lambda m: m["proven_count"] == len(rows) and m["typed_count"] == m["proven_count"])(
             build_manifest(rows, date="X"))),
        ("new numeric mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_leaves_numeric_math:\n  " + "\n  ".join(failed))
        return 1
    example = rows[0]
    print(f"PASS - prove_leaves_numeric_math: {len(index)} REAL numeric_math leaf primitives PROVEN end-to-end "
          f"(serves_truth=true, L7_executed_proof) and every one TYPED with canonical edge type ids "
          f"(e.g. {example['primitive_id']}: {example['input_edge_type_id']}->{example['output_edge_type_id']}); "
          "roundtrip-inverse pairs proven reversible; a deliberately-wrong leaf and an un-runnable fixture "
          "correctly stay candidate. Register tuple: " + json.dumps(list(REGISTER_TUPLE)))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default=None)
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_pack(date=args.date or DEFAULT_DATE)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
