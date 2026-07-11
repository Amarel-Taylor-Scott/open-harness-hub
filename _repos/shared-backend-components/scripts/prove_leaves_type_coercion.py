#!/usr/bin/env python3
"""scripts.prove_leaves_type_coercion — WORKABLE (proven + TYPED) deterministic leaf primitives for 'type_coercion'.

The family turns loose Text into a canonical TypedValue (int / float / bool / list / record / number-with-unit /
nullable). Every leaf here is a PURE deterministic mutator `(payload, **kwargs) -> (output, receipt)`; each is run
through the imported `run_primitive_proof` (from scripts.mutator_registry) which EXECUTES the mutator against a
concrete fixture and flips serves_truth false->true ONLY on a passing executed proof. A leaf with a wrong
expected_output stays candidate and is never persisted — that gate is the whole point.

Two properties make a leaf WORKABLE (not merely "proven"):
  1. an executed passing proof (serves_truth=true, verification_level=L7_executed_proof), and
  2. canonical EDGE TYPES — every persisted row carries input_edge_type_id / output_edge_type_id via the imported
     `canonicalize_edge`, so the leaf can chain in the edge graph (the fix for "proven but untyped").

Roundtrip-inverse pairs (to_list_split/join_list, bool_to_int/int_to_bool, int_to_hex/hex_to_int,
int_to_bin/bin_to_int) are proven REVERSIBLE via has_inverse.

ADD-ONLY: this is a NEW file. It IMPORTS the shared machinery (never edits mutator_registry.py /
build_edge_type_retrofit.py) and registers its extra pure mutators via setdefault (idempotent). It writes its OWN
family output file + manifest (no shared JSONL). Offline + deterministic: no network, no LLM, no wall-clock, no RNG.
CLI: --self-test | --write [--date D].
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the shared machinery — never edit it (ADD-ONLY).
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402
from scripts.mutator_registry import (  # noqa: E402
    INVERSE_PAIRS,
    MUTATOR_REGISTRY,
    _receipt,
    run_primitive_proof,
)

FAMILY = "type_coercion"
FIXED_DATE = "2026-07-03"  # fixed literal — NO wall-clock (repo law: deterministic + offline)

OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_type_coercion.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_type_coercion.json"

# register-tuple to REPORT back (this module is NOT self-registered in flywheel_proof_modules.py by us).
REGISTER_TUPLE = ("scripts/prove_leaves_type_coercion.py", "scripts.prove_leaves_type_coercion")

# ── shared coercion helpers (single source; imported nowhere else, defined once here) ──
#: canonical truthy/falsey token map (one definition, reused by to_bool / bool casts)
_BOOL_TOKENS: dict[str, bool] = {
    "true": True, "false": False, "1": True, "0": False, "yes": True, "no": False,
    "y": True, "n": False, "on": True, "off": False, "t": True, "f": False,
}


def _cast_value(value: Any, cast: str) -> Any:
    """Deterministically coerce one scalar to a named type. Raises on unparseable (callers may catch for -> None)."""
    if cast == "int":
        return int(str(value).strip())
    if cast == "float":
        return float(str(value).strip())
    if cast == "str":
        return str(value)
    if cast == "bool":
        return _BOOL_TOKENS[str(value).strip().lower()]
    return value


# ── the PURE deterministic mutators (each: (payload, **kwargs) -> (output, receipt)) ──
def _to_int_safe(text: Any, default: int = 0) -> tuple[int, dict[str, Any]]:
    try:
        out = int(str(text).strip())
    except (ValueError, TypeError):
        out = default
    return out, _receipt("to_int_safe", before=text, after=out, lossless=False, note="parse int; default on failure")


def _to_float_safe(text: Any, default: float = 0.0) -> tuple[float, dict[str, Any]]:
    try:
        out = float(str(text).strip())
    except (ValueError, TypeError):
        out = default
    return out, _receipt("to_float_safe", before=text, after=out, lossless=False, note="parse float; default on failure")


def _to_bool(text: Any) -> tuple[bool, dict[str, Any]]:
    out = _BOOL_TOKENS[str(text).strip().lower()]
    return out, _receipt("to_bool", before=text, after=out, lossless=False, note="canonical truthy/falsey coercion")


def _to_list_split(text: str, sep: str = ",") -> tuple[list[str], dict[str, Any]]:
    out = text.split(sep)
    return out, _receipt("to_list_split", before=text, after=out, lossless=True, note=f"split on {sep!r}; join_list restores")


def _join_list(items: list[Any], sep: str = ",") -> tuple[str, dict[str, Any]]:
    out = sep.join(str(i) for i in items)
    return out, _receipt("join_list", before=items, after=out, lossless=True, note=f"join with {sep!r}")


def _list_split_strip(text: str, sep: str = ",") -> tuple[list[str], dict[str, Any]]:
    out = [p.strip() for p in text.split(sep)]
    return out, _receipt("list_split_strip", before=text, after=out, lossless=False, note=f"split on {sep!r} + strip tokens")


def _coerce_int_list(text: str, sep: str = ",") -> tuple[list[int], dict[str, Any]]:
    out = [int(p.strip()) for p in text.split(sep)]
    return out, _receipt("coerce_int_list", before=text, after=out, lossless=False, note="split + int each")


def _coerce_float_list(text: str, sep: str = ",") -> tuple[list[float], dict[str, Any]]:
    out = [float(p.strip()) for p in text.split(sep)]
    return out, _receipt("coerce_float_list", before=text, after=out, lossless=False, note="split + float each")


def _null_default(value: Any, default: Any = None) -> tuple[Any, dict[str, Any]]:
    out = default if value is None else value
    return out, _receipt("null_default", before=value, after=out, lossless=False, note="None -> default; else passthrough")


def _empty_to_none(text: Any) -> tuple[Any, dict[str, Any]]:
    out = None if (isinstance(text, str) and text == "") else text
    return out, _receipt("empty_to_none", before=text, after=out, lossless=False, note="empty string -> None")


def _coerce_record_schema(record: dict[str, Any], casts: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {k: (_cast_value(v, casts[k]) if k in casts else v) for k, v in record.items()}
    return out, _receipt("coerce_record_schema", before=record, after=out, lossless=False, note=f"cast fields {list(casts)}")


def _strip_and_cast(text: Any, cast: str) -> tuple[Any, dict[str, Any]]:
    out = _cast_value(text, cast)
    return out, _receipt("strip_and_cast", before=text, after=out, lossless=False, note=f"strip + cast->{cast}")


def _parse_number_with_unit(text: str) -> tuple[dict[str, Any], dict[str, Any]]:
    m = re.match(r"^\s*([+-]?\d+(?:\.\d+)?)\s*([A-Za-z%]*)\s*$", text)
    if not m:
        raise ValueError(f"not a number-with-unit: {text!r}")
    out = {"value": float(m.group(1)), "unit": m.group(2)}
    return out, _receipt("parse_number_with_unit", before=text, after=out, lossless=False, note="split magnitude/unit")


def _parse_percent(text: str) -> tuple[float, dict[str, Any]]:
    out = float(str(text).strip().rstrip("%")) / 100.0
    return out, _receipt("parse_percent", before=text, after=out, lossless=False, note="percent string -> fraction")


def _parse_currency(text: str) -> tuple[float, dict[str, Any]]:
    cleaned = str(text).strip().replace("$", "").replace(",", "")
    out = float(cleaned)
    return out, _receipt("parse_currency", before=text, after=out, lossless=False, note="strip $/commas -> float")


def _to_str(value: Any) -> tuple[str, dict[str, Any]]:
    out = str(value)
    return out, _receipt("to_str", before=value, after=out, lossless=False, note="canonical str()")


def _to_int_from_float(value: float) -> tuple[int, dict[str, Any]]:
    out = int(value)
    return out, _receipt("to_int_from_float", before=value, after=out, lossless=False, note="truncate float -> int")


def _round_to_int(text: Any) -> tuple[int, dict[str, Any]]:
    out = int(round(float(str(text).strip())))
    return out, _receipt("round_to_int", before=text, after=out, lossless=False, note="round numeric string -> int")


def _cast_or_none(text: Any, cast: str) -> tuple[Any, dict[str, Any]]:
    try:
        out: Any = _cast_value(text, cast)
    except (ValueError, TypeError, KeyError):
        out = None
    return out, _receipt("cast_or_none", before=text, after=out, lossless=False, note=f"cast->{cast} or None")


def _bool_to_int(value: bool) -> tuple[int, dict[str, Any]]:
    out = int(bool(value))
    return out, _receipt("bool_to_int", before=value, after=out, lossless=True, note="bool -> 0/1; int_to_bool restores")


def _int_to_bool(value: Any) -> tuple[bool, dict[str, Any]]:
    out = bool(int(value))
    return out, _receipt("int_to_bool", before=value, after=out, lossless=True, note="0/1 -> bool")


def _int_to_hex(value: int) -> tuple[str, dict[str, Any]]:
    out = format(int(value), "x")
    return out, _receipt("int_to_hex", before=value, after=out, lossless=True, note="int -> lowercase hex; hex_to_int restores")


def _hex_to_int(text: str) -> tuple[int, dict[str, Any]]:
    out = int(str(text).strip(), 16)
    return out, _receipt("hex_to_int", before=text, after=out, lossless=True, note="hex string -> int")


def _int_to_bin(value: int) -> tuple[str, dict[str, Any]]:
    out = format(int(value), "b")
    return out, _receipt("int_to_bin", before=value, after=out, lossless=True, note="int -> binary string; bin_to_int restores")


def _bin_to_int(text: str) -> tuple[int, dict[str, Any]]:
    out = int(str(text).strip(), 2)
    return out, _receipt("bin_to_int", before=text, after=out, lossless=True, note="binary string -> int")


#: extra pure mutators to plug into the shared registry (idempotent setdefault; never overwrites existing entries)
_NEW_MUTATORS = {
    "to_int_safe": _to_int_safe, "to_float_safe": _to_float_safe, "to_bool": _to_bool,
    "to_list_split": _to_list_split, "join_list": _join_list, "list_split_strip": _list_split_strip,
    "coerce_int_list": _coerce_int_list, "coerce_float_list": _coerce_float_list,
    "null_default": _null_default, "empty_to_none": _empty_to_none,
    "coerce_record_schema": _coerce_record_schema, "strip_and_cast": _strip_and_cast,
    "parse_number_with_unit": _parse_number_with_unit, "parse_percent": _parse_percent,
    "parse_currency": _parse_currency, "to_str": _to_str, "to_int_from_float": _to_int_from_float,
    "round_to_int": _round_to_int, "cast_or_none": _cast_or_none,
    "bool_to_int": _bool_to_int, "int_to_bool": _int_to_bool,
    "int_to_hex": _int_to_hex, "hex_to_int": _hex_to_int,
    "int_to_bin": _int_to_bin, "bin_to_int": _bin_to_int,
}
_NEW_INVERSE_PAIRS = [
    ("to_list_split", "join_list"), ("bool_to_int", "int_to_bool"),
    ("int_to_hex", "hex_to_int"), ("int_to_bin", "bin_to_int"),
]


def register_new_mutators() -> None:
    """Plug the extra pure mutators into the shared MUTATOR_REGISTRY (registration, not a rewrite). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)
    for pair in _NEW_INVERSE_PAIRS:
        if pair not in INVERSE_PAIRS:
            INVERSE_PAIRS.append(pair)


register_new_mutators()


# ── the leaf primitives: each a concrete fixture + expected output + a TYPED edge shape (Text -> TypedValue) ──
# spec fields: id, capability, mutator, fixture, expected, args, inverse?, input_edge, output_edge
LEAF_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:to_int_safe", "capability": "parse a numeric string to int",
     "mutator": "to_int_safe", "fixture": "42", "expected": 42, "args": {},
     "input_edge": "Text", "output_edge": "Integer"},
    {"id": "prim:leaf:to_int_safe_default", "capability": "non-numeric string falls back to a default int",
     "mutator": "to_int_safe", "fixture": "abc", "expected": 7, "args": {"default": 7},
     "input_edge": "Text", "output_edge": "Integer"},
    {"id": "prim:leaf:to_int_safe_whitespace", "capability": "parse int tolerating surrounding whitespace",
     "mutator": "to_int_safe", "fixture": "  15 ", "expected": 15, "args": {},
     "input_edge": "Text", "output_edge": "Integer"},
    {"id": "prim:leaf:to_float_safe", "capability": "parse a decimal string to float",
     "mutator": "to_float_safe", "fixture": "1.5", "expected": 1.5, "args": {},
     "input_edge": "Text", "output_edge": "Number"},
    {"id": "prim:leaf:to_float_safe_default", "capability": "unparseable float falls back to a default",
     "mutator": "to_float_safe", "fixture": "n/a", "expected": 0.0, "args": {"default": 0.0},
     "input_edge": "Text", "output_edge": "Number"},
    {"id": "prim:leaf:to_float_int_string", "capability": "parse an integer-looking string to float",
     "mutator": "to_float_safe", "fixture": "3", "expected": 3.0, "args": {},
     "input_edge": "Text", "output_edge": "Number"},
    {"id": "prim:leaf:to_bool_yes", "capability": "coerce 'yes' to boolean true",
     "mutator": "to_bool", "fixture": "yes", "expected": True, "args": {},
     "input_edge": "Text", "output_edge": "Boolean"},
    {"id": "prim:leaf:to_bool_no", "capability": "coerce 'no' to boolean false",
     "mutator": "to_bool", "fixture": "no", "expected": False, "args": {},
     "input_edge": "Text", "output_edge": "Boolean"},
    {"id": "prim:leaf:to_bool_one", "capability": "coerce '1' to boolean true",
     "mutator": "to_bool", "fixture": "1", "expected": True, "args": {},
     "input_edge": "Text", "output_edge": "Boolean"},
    {"id": "prim:leaf:to_bool_off", "capability": "coerce 'off' to boolean false",
     "mutator": "to_bool", "fixture": "OFF", "expected": False, "args": {},
     "input_edge": "Text", "output_edge": "Boolean"},
    {"id": "prim:leaf:to_list_split", "capability": "split a delimited string to a list (roundtrips)",
     "mutator": "to_list_split", "fixture": "a,b,c", "expected": ["a", "b", "c"], "args": {},
     "inverse": "join_list", "input_edge": "Text", "output_edge": "StringList"},
    {"id": "prim:leaf:join_list", "capability": "join a list of tokens into a delimited string",
     "mutator": "join_list", "fixture": ["x", "y"], "expected": "x,y", "args": {},
     "input_edge": "StringList", "output_edge": "Text"},
    {"id": "prim:leaf:to_list_split_pipe", "capability": "split on a pipe delimiter",
     "mutator": "to_list_split", "fixture": "a|b|c", "expected": ["a", "b", "c"], "args": {"sep": "|"},
     "input_edge": "Text", "output_edge": "StringList"},
    {"id": "prim:leaf:list_split_strip", "capability": "split and strip whitespace from each token",
     "mutator": "list_split_strip", "fixture": "a, b , c", "expected": ["a", "b", "c"], "args": {},
     "input_edge": "Text", "output_edge": "StringList"},
    {"id": "prim:leaf:coerce_int_list", "capability": "split a string into a list of ints",
     "mutator": "coerce_int_list", "fixture": "1, 2, 3", "expected": [1, 2, 3], "args": {},
     "input_edge": "Text", "output_edge": "IntegerList"},
    {"id": "prim:leaf:coerce_float_list", "capability": "split a string into a list of floats",
     "mutator": "coerce_float_list", "fixture": "1.5,2.5", "expected": [1.5, 2.5], "args": {},
     "input_edge": "Text", "output_edge": "NumberList"},
    {"id": "prim:leaf:null_default", "capability": "replace None with a default value",
     "mutator": "null_default", "fixture": None, "expected": 5, "args": {"default": 5},
     "input_edge": "NullableValue", "output_edge": "TypedValue"},
    {"id": "prim:leaf:null_default_passthrough", "capability": "a present value passes the default through",
     "mutator": "null_default", "fixture": "keep", "expected": "keep", "args": {"default": "x"},
     "input_edge": "NullableValue", "output_edge": "TypedValue"},
    {"id": "prim:leaf:null_default_zero", "capability": "None becomes a zero integer default",
     "mutator": "null_default", "fixture": None, "expected": 0, "args": {"default": 0},
     "input_edge": "NullableValue", "output_edge": "Integer"},
    {"id": "prim:leaf:empty_to_none", "capability": "convert an empty string to None",
     "mutator": "empty_to_none", "fixture": "", "expected": None, "args": {},
     "input_edge": "Text", "output_edge": "NullableValue"},
    {"id": "prim:leaf:empty_to_none_passthrough", "capability": "a non-empty string passes through unchanged",
     "mutator": "empty_to_none", "fixture": "text", "expected": "text", "args": {},
     "input_edge": "Text", "output_edge": "NullableValue"},
    {"id": "prim:leaf:coerce_record_schema", "capability": "coerce record fields to a typed schema",
     "mutator": "coerce_record_schema", "fixture": {"n": "5", "f": "1.5", "b": "yes"},
     "expected": {"n": 5, "f": 1.5, "b": True}, "args": {"casts": {"n": "int", "f": "float", "b": "bool"}},
     "input_edge": "Record", "output_edge": "TypedRecord"},
    {"id": "prim:leaf:coerce_record_schema_partial", "capability": "cast only the declared fields, keep the rest raw",
     "mutator": "coerce_record_schema", "fixture": {"n": "9", "keep": "raw"},
     "expected": {"n": 9, "keep": "raw"}, "args": {"casts": {"n": "int"}},
     "input_edge": "Record", "output_edge": "TypedRecord"},
    {"id": "prim:leaf:strip_and_cast_int", "capability": "strip whitespace then cast to int",
     "mutator": "strip_and_cast", "fixture": "  42  ", "expected": 42, "args": {"cast": "int"},
     "input_edge": "Text", "output_edge": "Integer"},
    {"id": "prim:leaf:strip_and_cast_float", "capability": "strip whitespace then cast to float",
     "mutator": "strip_and_cast", "fixture": " 3.14 ", "expected": 3.14, "args": {"cast": "float"},
     "input_edge": "Text", "output_edge": "Number"},
    {"id": "prim:leaf:strip_and_cast_bool", "capability": "strip whitespace then cast to bool",
     "mutator": "strip_and_cast", "fixture": " yes ", "expected": True, "args": {"cast": "bool"},
     "input_edge": "Text", "output_edge": "Boolean"},
    {"id": "prim:leaf:parse_number_with_unit_kg", "capability": "split a magnitude and its unit ('10kg')",
     "mutator": "parse_number_with_unit", "fixture": "10kg", "expected": {"value": 10.0, "unit": "kg"}, "args": {},
     "input_edge": "Text", "output_edge": "NumberWithUnit"},
    {"id": "prim:leaf:parse_number_with_unit_ms", "capability": "split a magnitude and unit with a space ('250 ms')",
     "mutator": "parse_number_with_unit", "fixture": "250 ms", "expected": {"value": 250.0, "unit": "ms"}, "args": {},
     "input_edge": "Text", "output_edge": "NumberWithUnit"},
    {"id": "prim:leaf:parse_percent", "capability": "parse a percent string to a fraction",
     "mutator": "parse_percent", "fixture": "50%", "expected": 0.5, "args": {},
     "input_edge": "Text", "output_edge": "Number"},
    {"id": "prim:leaf:parse_currency", "capability": "parse a currency string to a float",
     "mutator": "parse_currency", "fixture": "$1,234.50", "expected": 1234.5, "args": {},
     "input_edge": "Text", "output_edge": "Number"},
    {"id": "prim:leaf:to_str", "capability": "coerce a typed value to its canonical string",
     "mutator": "to_str", "fixture": 42, "expected": "42", "args": {},
     "input_edge": "TypedValue", "output_edge": "Text"},
    {"id": "prim:leaf:to_int_from_float", "capability": "truncate a float to an int",
     "mutator": "to_int_from_float", "fixture": 3.9, "expected": 3, "args": {},
     "input_edge": "Number", "output_edge": "Integer"},
    {"id": "prim:leaf:round_to_int", "capability": "round a numeric string to the nearest int",
     "mutator": "round_to_int", "fixture": "3.6", "expected": 4, "args": {},
     "input_edge": "Text", "output_edge": "Integer"},
    {"id": "prim:leaf:cast_or_none_fail", "capability": "an unparseable cast yields None (not an error)",
     "mutator": "cast_or_none", "fixture": "abc", "expected": None, "args": {"cast": "int"},
     "input_edge": "Text", "output_edge": "NullableValue"},
    {"id": "prim:leaf:cast_or_none_ok", "capability": "a parseable cast yields the typed value",
     "mutator": "cast_or_none", "fixture": "12", "expected": 12, "args": {"cast": "int"},
     "input_edge": "Text", "output_edge": "NullableValue"},
    {"id": "prim:leaf:bool_to_int", "capability": "coerce a bool to 0/1 (roundtrips)",
     "mutator": "bool_to_int", "fixture": True, "expected": 1, "args": {},
     "inverse": "int_to_bool", "input_edge": "Boolean", "output_edge": "Integer"},
    {"id": "prim:leaf:int_to_bool", "capability": "coerce 0/1 to a bool",
     "mutator": "int_to_bool", "fixture": 1, "expected": True, "args": {},
     "input_edge": "Integer", "output_edge": "Boolean"},
    {"id": "prim:leaf:int_to_hex", "capability": "encode an int as a lowercase hex string (roundtrips)",
     "mutator": "int_to_hex", "fixture": 255, "expected": "ff", "args": {},
     "inverse": "hex_to_int", "input_edge": "Integer", "output_edge": "HexString"},
    {"id": "prim:leaf:hex_to_int", "capability": "decode a hex string to an int",
     "mutator": "hex_to_int", "fixture": "ff", "expected": 255, "args": {},
     "input_edge": "HexString", "output_edge": "Integer"},
    {"id": "prim:leaf:int_to_bin", "capability": "encode an int as a binary string (roundtrips)",
     "mutator": "int_to_bin", "fixture": 5, "expected": "101", "args": {},
     "inverse": "bin_to_int", "input_edge": "Integer", "output_edge": "BinaryString"},
    {"id": "prim:leaf:bin_to_int", "capability": "decode a binary string to an int",
     "mutator": "bin_to_int", "fixture": "101", "expected": 5, "args": {},
     "input_edge": "BinaryString", "output_edge": "Integer"},
]

#: deliberately-wrong leaf — the proof gate MUST leave this candidate (never persisted as proven)
NEGATIVE_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:WRONG_to_int", "capability": "to_int_safe with a wrong expected output",
     "mutator": "to_int_safe", "fixture": "42", "expected": 999, "args": {},
     "input_edge": "Text", "output_edge": "Integer"},
]


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    receipt = run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )
    receipt["capability"] = spec["capability"]
    receipt["family"] = FAMILY
    # TYPE the receipt (the fix for 'proven but untyped'): canonical edge types so the leaf can chain.
    receipt["input_edge"] = spec["input_edge"]
    receipt["output_edge"] = spec["output_edge"]
    receipt["input_edge_type_id"] = canonicalize_edge(spec["input_edge"])
    receipt["output_edge_type_id"] = canonicalize_edge(spec["output_edge"])
    return receipt


def prove_all() -> list[dict[str, Any]]:
    """Run every declared leaf primitive through the imported executed-proof runner."""
    return [_prove_one(s) for s in LEAF_SPECS]


def proven_rows() -> list[dict[str, Any]]:
    """The WORKABLE rows: passed an executed proof AND carry both canonical edge types. Sorted by primitive_id."""
    rows = [
        r for r in prove_all()
        if r["serves_truth"] is True
        and r.get("input_edge_type_id") not in (None, "")
        and r.get("output_edge_type_id") not in (None, "")
    ]
    return sorted(rows, key=lambda r: r["primitive_id"])


def build_manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"]]
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    return {
        "record_type": "proven_type_coercion_manifest",
        "family": FAMILY,
        "pack_id": "proven-type-coercion-leaves",
        "generator": REGISTER_TUPLE[0],
        "generated_utc": FIXED_DATE,
        "declared_leaf_count": len(LEAF_SPECS),
        "proven_count": len(rows),
        "typed_count": len(typed),
        "proven_primitive_ids": [r["primitive_id"] for r in rows],
        "verification_level": "L7_executed_proof",
        "row_counts": {OUT_JSONL.name: len(rows)},
        "total_rows": len(rows),
        "register_module": {"script_path": REGISTER_TUPLE[0], "module_name": REGISTER_TUPLE[1]},
        "note": "serves_truth=true is set ONLY by an executed passing proof (run_primitive_proof, imported from "
                "scripts/mutator_registry.py); a deliberately-wrong leaf stays candidate and is never persisted. "
                "Every workable row is TYPED via canonicalize_edge so it can chain.",
        "content_sha256": __import__("hashlib").sha256(canonical.encode("utf-8")).hexdigest(),
    }


def _persist_row(r: dict[str, Any]) -> dict[str, Any]:
    """The stored shape: proven + typed + family-stamped (candidate=false is correct — this is a truth-bearing leaf)."""
    return {
        "primitive_id": r["primitive_id"],
        "mutator": r["mutator"],
        "capability": r["capability"],
        "family": FAMILY,
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": r["input_edge"],
        "output_edge": r["output_edge"],
        "input_edge_type_id": r["input_edge_type_id"],
        "output_edge_type_id": r["output_edge_type_id"],
        "proofs": r["proofs"],
        "input_hash": r["input_hash"],
        "output_hash": r["output_hash"],
    }


def write_pack() -> dict[str, Any]:
    rows = [_persist_row(r) for r in proven_rows()]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8"
    )
    manifest = build_manifest(rows)
    OUT_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def self_test() -> int:
    rows = proven_rows()
    ids = [r["primitive_id"] for r in prove_all()]
    persisted = [_persist_row(r) for r in rows]

    # a deliberately-wrong leaf must stay candidate (the gate is real, not a rubber stamp)
    wrong = _prove_one(NEGATIVE_SPECS[0])
    # a second wrong path: a fixture the mutator cannot handle -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:EXEC_ERROR", "parse_number_with_unit", "not-a-number", "irrelevant")

    inverse_specs = [s for s in LEAF_SPECS if s.get("inverse")]
    proven_index = {r["primitive_id"]: r for r in rows}

    checks: list[tuple[str, bool]] = [
        (">=28 leaf primitives declared", len(LEAF_SPECS) >= 28),
        ("unique primitive ids", len(set(ids)) == len(ids)),
        (">=28 leaves PROVE serves_truth=true via an executed proof", len(rows) >= 28),
        ("every proven row is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"]) for r in rows)),
        ("EVERY persisted row carries a non-null input_edge_type_id",
         all(r["input_edge_type_id"] not in (None, "") for r in persisted)),
        ("EVERY persisted row carries a non-null output_edge_type_id",
         all(r["output_edge_type_id"] not in (None, "") for r in persisted)),
        ("no edge type folded to 'Unknown'",
         all(r["input_edge_type_id"] != "Unknown" and r["output_edge_type_id"] != "Unknown" for r in persisted)),
        ("typed_count == proven_count (every workable leaf is typed)",
         build_manifest(persisted)["typed_count"] == build_manifest(persisted)["proven_count"] == len(rows)),
        ("every persisted row is truth-bearing (serves_truth=true, candidate=false)",
         all(r["serves_truth"] is True and r["candidate"] is False for r in persisted)),
        (">=4 roundtrip-inverse pairs declared", len(inverse_specs) >= 4),
        ("roundtrip leaves actually PROVED reversibility (roundtrip_test passed)",
         all(s["id"] in proven_index and any(
             p["name"] == "roundtrip_test" and p["passed"] for p in proven_index[s["id"]]["proofs"])
             for s in inverse_specs)),
        ("deterministic: re-running yields identical proven rows",
         [json.dumps(_persist_row(r), sort_keys=True) for r in proven_rows()]
         == [json.dumps(r, sort_keys=True) for r in persisted]),
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted/persisted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False
         and wrong["primitive_id"] not in proven_index),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_leaves_type_coercion:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_leaves_type_coercion: {len(rows)} WORKABLE (proven + TYPED) '{FAMILY}' leaf primitives "
          f"proven end-to-end via the imported executed-proof runner (serves_truth=true, L7_executed_proof, both "
          f"edge types canonical); {len(inverse_specs)} roundtrip-inverse pairs proven reversible; a "
          f"deliberately-wrong leaf and an un-runnable fixture correctly stay candidate. Register tuple: "
          f"{REGISTER_TUPLE}.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default=None)  # accepted for interface parity; body uses the fixed literal date
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_pack()
    print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
