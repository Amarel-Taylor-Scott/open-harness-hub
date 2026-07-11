#!/usr/bin/env python3
"""scripts.prove_leaves_validation_predicate — WORKABLE (proven + TYPED) deterministic leaf primitives for the
'validation_predicate' family.

Vocabulary is not capability. This module declares >=28 REAL pure-deterministic validation-predicate leaf primitives
(in-range · non-empty · regex-match · uuid-shape · email-shape · required-keys-present · enum-member · length-bound ·
type-check · schema-required · min/max/positive/non-negative · startswith/endswith/contains · digit/alpha/lowercase ·
exact-length · no-whitespace · url/iso-date/hex-color shape · json-parseable · unique-items · all-keys-str · verdict
emit/parse roundtrip · rulespec flatten/unflatten roundtrip), runs EVERY ONE through the IMPORTED executed-proof
runner `run_primitive_proof` (from _repos/shared-backend-components/scripts/mutator_registry.py), keeps ONLY the passing ProofReceipts, and — the fix
for "proven but untyped" — TYPES every persisted row with canonical edge types via `canonicalize_edge` so a workable
leaf can chain. The logical family shape is Record -> ValidationVerdict; some leaves carry a more specific shape.

ADD-ONLY / flexible: a NEW parallel path. It IMPORTS the shared machinery and REGISTERS extra pure mutators into the
shared MUTATOR_REGISTRY via setdefault (registration, never a rewrite; never overwrites an existing entry). It does
NOT edit any contract-locked or shared file. serves_truth=true here is CORRECT + required — it is set ONLY by an
executed passing proof; a deliberately-wrong-expected leaf stays candidate and is never persisted. Deterministic +
offline: no network, no LLM, no wall-clock (fixed literal timestamps), no RNG. CLI: --self-test | --write [--date D].
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

# IMPORT the shared machinery — never edit it (ADD-ONLY / flexible-multi-path).
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402
from scripts.mutator_registry import (  # noqa: E402
    INVERSE_PAIRS,
    MUTATOR_REGISTRY,
    _receipt,
    run_primitive_proof,
)

FAMILY = "validation_predicate"
#: fixed literal timestamp — NEVER wall-clock (repo law: deterministic + offline).
_FIXED_UTC = "2026-07-03"

OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_validation_predicate.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_validation_predicate.json"


# ── verdict helper: every validation leaf emits a ValidationVerdict record ──
def _verdict(check: str, valid: Any, **extra: Any) -> dict[str, Any]:
    rec: dict[str, Any] = {"check": check, "valid": bool(valid)}
    rec.update(extra)
    return rec


def _rec(name: str, before: Any, after: Any, note: str) -> dict[str, Any]:
    return _receipt(name, before=before, after=after, lossless=False, note=note)


# ── PURE deterministic validation-predicate mutators (payload, **kwargs) -> (ValidationVerdict, receipt) ──
def vp_in_range(value: Any, lo: Any, hi: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("in_range", lo <= value <= hi, value=value, lo=lo, hi=hi)
    return out, _rec("vp_in_range", value, out, f"value in [{lo},{hi}]")


def vp_non_empty(value: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    length = len(value) if value is not None else 0
    out = _verdict("non_empty", value is not None and length > 0, length=length)
    return out, _rec("vp_non_empty", value, out, "value is non-empty")


def vp_regex_match(value: str, pattern: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("regex_match", re.fullmatch(pattern, value) is not None, pattern=pattern)
    return out, _rec("vp_regex_match", value, out, f"fullmatch /{pattern}/")


def vp_is_uuid_shape(value: str) -> tuple[dict[str, Any], dict[str, Any]]:
    pat = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    out = _verdict("is_uuid_shape", re.fullmatch(pat, value) is not None)
    return out, _rec("vp_is_uuid_shape", value, out, "canonical 8-4-4-4-12 uuid shape")


def vp_is_email_shape(value: str) -> tuple[dict[str, Any], dict[str, Any]]:
    pat = r"[^@\s]+@[^@\s]+\.[^@\s]+"
    out = _verdict("is_email_shape", re.fullmatch(pat, value) is not None)
    return out, _rec("vp_is_email_shape", value, out, "local@domain.tld shape")


def vp_required_keys(record: dict[str, Any], required: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    missing = [k for k in required if k not in record]
    out = _verdict("required_keys", not missing, missing=missing)
    return out, _rec("vp_required_keys", record, out, f"required={required}")


def vp_enum_member(value: Any, choices: list[Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("enum_member", value in choices, value=value)
    return out, _rec("vp_enum_member", value, out, f"value in {choices}")


def vp_length_bound(value: Any, min_len: int, max_len: int) -> tuple[dict[str, Any], dict[str, Any]]:
    n = len(value)
    out = _verdict("length_bound", min_len <= n <= max_len, length=n, min=min_len, max=max_len)
    return out, _rec("vp_length_bound", value, out, f"len in [{min_len},{max_len}]")


def vp_type_check(value: Any, expected: str) -> tuple[dict[str, Any], dict[str, Any]]:
    actual = type(value).__name__
    out = _verdict("type_check", actual == expected, actual=actual, expected=expected)
    return out, _rec("vp_type_check", value, out, f"type == {expected}")


def vp_schema_required(record: dict[str, Any], schema: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    missing = [f for f in schema if f not in record]
    type_errors = [f for f, t in schema.items() if f in record and type(record[f]).__name__ != t]
    out = _verdict("schema_required", not missing and not type_errors, missing=missing, type_errors=type_errors)
    return out, _rec("vp_schema_required", record, out, f"schema={schema}")


def vp_min(value: Any, minimum: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("min", value >= minimum, value=value, minimum=minimum)
    return out, _rec("vp_min", value, out, f"value >= {minimum}")


def vp_max(value: Any, maximum: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("max", value <= maximum, value=value, maximum=maximum)
    return out, _rec("vp_max", value, out, f"value <= {maximum}")


def vp_positive(value: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("positive", value > 0, value=value)
    return out, _rec("vp_positive", value, out, "value > 0")


def vp_non_negative(value: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("non_negative", value >= 0, value=value)
    return out, _rec("vp_non_negative", value, out, "value >= 0")


def vp_is_int(value: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("is_int", isinstance(value, int) and not isinstance(value, bool))
    return out, _rec("vp_is_int", value, out, "int and not bool")


def vp_is_bool(value: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("is_bool", isinstance(value, bool))
    return out, _rec("vp_is_bool", value, out, "value is bool")


def vp_starts_with(value: str, prefix: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("starts_with", value.startswith(prefix), prefix=prefix)
    return out, _rec("vp_starts_with", value, out, f"startswith {prefix!r}")


def vp_ends_with(value: str, suffix: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("ends_with", value.endswith(suffix), suffix=suffix)
    return out, _rec("vp_ends_with", value, out, f"endswith {suffix!r}")


def vp_contains(value: str, needle: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("contains", needle in value, needle=needle)
    return out, _rec("vp_contains", value, out, f"contains {needle!r}")


def vp_is_digit_string(value: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("is_digit_string", value.isdigit())
    return out, _rec("vp_is_digit_string", value, out, "all-digit string")


def vp_is_alpha(value: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("is_alpha", value.isalpha())
    return out, _rec("vp_is_alpha", value, out, "all-alpha string")


def vp_is_lowercase(value: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("is_lowercase", value.islower())
    return out, _rec("vp_is_lowercase", value, out, "lowercase string")


def vp_exact_length(value: Any, n: int) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("exact_length", len(value) == n, length=len(value), expected=n)
    return out, _rec("vp_exact_length", value, out, f"len == {n}")


def vp_no_whitespace(value: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("no_whitespace", not any(c.isspace() for c in value))
    return out, _rec("vp_no_whitespace", value, out, "no whitespace chars")


def vp_is_url_shape(value: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("is_url_shape", re.fullmatch(r"https?://[^\s]+", value) is not None)
    return out, _rec("vp_is_url_shape", value, out, "http(s):// url shape")


def vp_is_iso_date_shape(value: str) -> tuple[dict[str, Any], dict[str, Any]]:
    # SHAPE only (no wall-clock): matches YYYY-MM-DD structurally, does not compare to 'now'.
    out = _verdict("is_iso_date_shape", re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is not None)
    return out, _rec("vp_is_iso_date_shape", value, out, "YYYY-MM-DD shape")


def vp_is_hex_color(value: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("is_hex_color", re.fullmatch(r"#[0-9a-fA-F]{6}", value) is not None)
    return out, _rec("vp_is_hex_color", value, out, "#rrggbb hex color")


def vp_json_parseable(value: str) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        json.loads(value)
        ok = True
    except (ValueError, TypeError):
        ok = False
    out = _verdict("json_parseable", ok)
    return out, _rec("vp_json_parseable", value, out, "value parses as JSON")


def vp_unique_items(items: list[Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("unique_items", len(items) == len(set(items)), count=len(items), unique=len(set(items)))
    return out, _rec("vp_unique_items", items, out, "all items unique")


def vp_all_keys_str(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("all_keys_str", all(isinstance(k, str) for k in record))
    return out, _rec("vp_all_keys_str", record, out, "every mapping key is a string")


# ── reversible pairs (roundtrip-proven): emit/parse a verdict line; flatten/unflatten a rule spec ──
def vp_verdict_emit(verdict: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    out = json.dumps(verdict, sort_keys=True)
    return out, _rec("vp_verdict_emit", verdict, out, "verdict -> canonical line; vp_verdict_parse restores")


def vp_verdict_parse(text: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = json.loads(text)
    return out, _rec("vp_verdict_parse", text, out, "verdict line -> verdict record")


def vp_rulespec_flatten(spec: dict[str, Any], sep: str = ".") -> tuple[dict[str, Any], dict[str, Any]]:
    out: dict[str, Any] = {}

    def _walk(node: dict[str, Any], prefix: str) -> None:
        for k, v in node.items():
            key = f"{prefix}{sep}{k}" if prefix else k
            if isinstance(v, dict) and v:
                _walk(v, key)
            else:
                out[key] = v

    _walk(spec, "")
    return out, _rec("vp_rulespec_flatten", spec, out, "nested rule spec -> dotted flat; vp_rulespec_unflatten restores")


def vp_rulespec_unflatten(flat: dict[str, Any], sep: str = ".") -> tuple[dict[str, Any], dict[str, Any]]:
    out: dict[str, Any] = {}
    for key, v in flat.items():
        parts = key.split(sep)
        node = out
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = v
    return out, _rec("vp_rulespec_unflatten", flat, out, "dotted flat -> nested rule spec")


#: extra pure mutators to plug into the shared registry (idempotent setdefault registration; never overwrites)
_NEW_MUTATORS = {
    "vp_in_range": vp_in_range, "vp_non_empty": vp_non_empty, "vp_regex_match": vp_regex_match,
    "vp_is_uuid_shape": vp_is_uuid_shape, "vp_is_email_shape": vp_is_email_shape,
    "vp_required_keys": vp_required_keys, "vp_enum_member": vp_enum_member, "vp_length_bound": vp_length_bound,
    "vp_type_check": vp_type_check, "vp_schema_required": vp_schema_required, "vp_min": vp_min, "vp_max": vp_max,
    "vp_positive": vp_positive, "vp_non_negative": vp_non_negative, "vp_is_int": vp_is_int, "vp_is_bool": vp_is_bool,
    "vp_starts_with": vp_starts_with, "vp_ends_with": vp_ends_with, "vp_contains": vp_contains,
    "vp_is_digit_string": vp_is_digit_string, "vp_is_alpha": vp_is_alpha, "vp_is_lowercase": vp_is_lowercase,
    "vp_exact_length": vp_exact_length, "vp_no_whitespace": vp_no_whitespace, "vp_is_url_shape": vp_is_url_shape,
    "vp_is_iso_date_shape": vp_is_iso_date_shape, "vp_is_hex_color": vp_is_hex_color,
    "vp_json_parseable": vp_json_parseable, "vp_unique_items": vp_unique_items, "vp_all_keys_str": vp_all_keys_str,
    "vp_verdict_emit": vp_verdict_emit, "vp_verdict_parse": vp_verdict_parse,
    "vp_rulespec_flatten": vp_rulespec_flatten, "vp_rulespec_unflatten": vp_rulespec_unflatten,
}
_NEW_INVERSE_PAIRS = [("vp_verdict_emit", "vp_verdict_parse"), ("vp_rulespec_flatten", "vp_rulespec_unflatten")]


def register_new_mutators() -> None:
    """Plug the extra pure validation mutators into the shared MUTATOR_REGISTRY (setdefault — idempotent, never
    overwrites an existing entry). Also records the two inverse pairs for roundtrip proofs."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)
    for pair in _NEW_INVERSE_PAIRS:
        if pair not in INVERSE_PAIRS:
            INVERSE_PAIRS.append(pair)


register_new_mutators()


# ── leaf specs: each a REAL validation predicate with a concrete fixture + expected verdict (+ optional inverse) ──
# fields: (id, capability, mutator, fixture, expected, args, inverse, input_edge, output_edge)
LEAF_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:vp_in_range", "capability": "value within an inclusive numeric range",
     "mutator": "vp_in_range", "fixture": 5, "args": {"lo": 0, "hi": 10},
     "expected": {"check": "in_range", "valid": True, "value": 5, "lo": 0, "hi": 10},
     "input_edge": "Number", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_non_empty", "capability": "value is present and non-empty",
     "mutator": "vp_non_empty", "fixture": "hi", "args": {},
     "expected": {"check": "non_empty", "valid": True, "length": 2},
     "input_edge": "Text", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_regex_match", "capability": "string fully matches a regex",
     "mutator": "vp_regex_match", "fixture": "abc123", "args": {"pattern": r"[a-z]+[0-9]+"},
     "expected": {"check": "regex_match", "valid": True, "pattern": r"[a-z]+[0-9]+"},
     "input_edge": "Text", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_is_uuid_shape", "capability": "string is a canonical uuid shape",
     "mutator": "vp_is_uuid_shape", "fixture": "550e8400-e29b-41d4-a716-446655440000", "args": {},
     "expected": {"check": "is_uuid_shape", "valid": True},
     "input_edge": "Text", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_is_email_shape", "capability": "string is a local@domain.tld email shape",
     "mutator": "vp_is_email_shape", "fixture": "user@example.com", "args": {},
     "expected": {"check": "is_email_shape", "valid": True},
     "input_edge": "Text", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_required_keys", "capability": "record contains all required keys",
     "mutator": "vp_required_keys", "fixture": {"name": "x", "email": "y"}, "args": {"required": ["name", "email"]},
     "expected": {"check": "required_keys", "valid": True, "missing": []},
     "input_edge": "Record", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_enum_member", "capability": "value is a member of an allowed set",
     "mutator": "vp_enum_member", "fixture": "red", "args": {"choices": ["red", "green", "blue"]},
     "expected": {"check": "enum_member", "valid": True, "value": "red"},
     "input_edge": "Value", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_length_bound", "capability": "length within an inclusive bound",
     "mutator": "vp_length_bound", "fixture": "hello", "args": {"min_len": 1, "max_len": 10},
     "expected": {"check": "length_bound", "valid": True, "length": 5, "min": 1, "max": 10},
     "input_edge": "Text", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_type_check", "capability": "value has the expected python type",
     "mutator": "vp_type_check", "fixture": 5, "args": {"expected": "int"},
     "expected": {"check": "type_check", "valid": True, "actual": "int", "expected": "int"},
     "input_edge": "Value", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_schema_required", "capability": "record satisfies a required-field+type schema",
     "mutator": "vp_schema_required", "fixture": {"name": "x", "age": 30},
     "args": {"schema": {"name": "str", "age": "int"}},
     "expected": {"check": "schema_required", "valid": True, "missing": [], "type_errors": []},
     "input_edge": "Record", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_min", "capability": "value is at least a minimum",
     "mutator": "vp_min", "fixture": 5, "args": {"minimum": 3},
     "expected": {"check": "min", "valid": True, "value": 5, "minimum": 3},
     "input_edge": "Number", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_max", "capability": "value is at most a maximum",
     "mutator": "vp_max", "fixture": 5, "args": {"maximum": 10},
     "expected": {"check": "max", "valid": True, "value": 5, "maximum": 10},
     "input_edge": "Number", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_positive", "capability": "value is strictly positive",
     "mutator": "vp_positive", "fixture": 5, "args": {},
     "expected": {"check": "positive", "valid": True, "value": 5},
     "input_edge": "Number", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_non_negative", "capability": "value is non-negative",
     "mutator": "vp_non_negative", "fixture": 0, "args": {},
     "expected": {"check": "non_negative", "valid": True, "value": 0},
     "input_edge": "Number", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_is_int", "capability": "value is an int (not bool)",
     "mutator": "vp_is_int", "fixture": 7, "args": {},
     "expected": {"check": "is_int", "valid": True},
     "input_edge": "Value", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_is_bool", "capability": "value is a boolean",
     "mutator": "vp_is_bool", "fixture": True, "args": {},
     "expected": {"check": "is_bool", "valid": True},
     "input_edge": "Value", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_starts_with", "capability": "string starts with a prefix",
     "mutator": "vp_starts_with", "fixture": "hello", "args": {"prefix": "he"},
     "expected": {"check": "starts_with", "valid": True, "prefix": "he"},
     "input_edge": "Text", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_ends_with", "capability": "string ends with a suffix",
     "mutator": "vp_ends_with", "fixture": "hello", "args": {"suffix": "lo"},
     "expected": {"check": "ends_with", "valid": True, "suffix": "lo"},
     "input_edge": "Text", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_contains", "capability": "string contains a substring",
     "mutator": "vp_contains", "fixture": "hello", "args": {"needle": "ell"},
     "expected": {"check": "contains", "valid": True, "needle": "ell"},
     "input_edge": "Text", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_is_digit_string", "capability": "string is all digits",
     "mutator": "vp_is_digit_string", "fixture": "12345", "args": {},
     "expected": {"check": "is_digit_string", "valid": True},
     "input_edge": "Text", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_is_alpha", "capability": "string is all letters",
     "mutator": "vp_is_alpha", "fixture": "abcDEF", "args": {},
     "expected": {"check": "is_alpha", "valid": True},
     "input_edge": "Text", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_is_lowercase", "capability": "string is lowercase",
     "mutator": "vp_is_lowercase", "fixture": "hello", "args": {},
     "expected": {"check": "is_lowercase", "valid": True},
     "input_edge": "Text", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_exact_length", "capability": "length equals an exact count",
     "mutator": "vp_exact_length", "fixture": "abcd", "args": {"n": 4},
     "expected": {"check": "exact_length", "valid": True, "length": 4, "expected": 4},
     "input_edge": "Text", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_no_whitespace", "capability": "string has no whitespace",
     "mutator": "vp_no_whitespace", "fixture": "no_spaces", "args": {},
     "expected": {"check": "no_whitespace", "valid": True},
     "input_edge": "Text", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_is_url_shape", "capability": "string is an http(s) url shape",
     "mutator": "vp_is_url_shape", "fixture": "https://example.com/path", "args": {},
     "expected": {"check": "is_url_shape", "valid": True},
     "input_edge": "Text", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_is_iso_date_shape", "capability": "string is a YYYY-MM-DD shape (no wall-clock)",
     "mutator": "vp_is_iso_date_shape", "fixture": "2026-07-03", "args": {},
     "expected": {"check": "is_iso_date_shape", "valid": True},
     "input_edge": "Text", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_is_hex_color", "capability": "string is a #rrggbb hex color",
     "mutator": "vp_is_hex_color", "fixture": "#ff8800", "args": {},
     "expected": {"check": "is_hex_color", "valid": True},
     "input_edge": "Text", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_json_parseable", "capability": "string parses as JSON",
     "mutator": "vp_json_parseable", "fixture": "{\"a\": 1}", "args": {},
     "expected": {"check": "json_parseable", "valid": True},
     "input_edge": "Text", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_unique_items", "capability": "list has no duplicate items",
     "mutator": "vp_unique_items", "fixture": [1, 2, 3], "args": {},
     "expected": {"check": "unique_items", "valid": True, "count": 3, "unique": 3},
     "input_edge": "List", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_all_keys_str", "capability": "every mapping key is a string",
     "mutator": "vp_all_keys_str", "fixture": {"a": 1, "b": 2}, "args": {},
     "expected": {"check": "all_keys_str", "valid": True},
     "input_edge": "Record", "output_edge": "ValidationVerdict"},
    # ── reversible pairs: roundtrip-proven via has_inverse ──
    {"id": "prim:leaf:vp_verdict_emit", "capability": "emit a verdict to a canonical line (roundtrips)",
     "mutator": "vp_verdict_emit", "fixture": {"check": "non_empty", "valid": True},
     "expected": "{\"check\": \"non_empty\", \"valid\": true}", "args": {}, "inverse": "vp_verdict_parse",
     "input_edge": "ValidationVerdict", "output_edge": "VerdictLine"},
    {"id": "prim:leaf:vp_verdict_parse", "capability": "parse a verdict line back to a verdict record",
     "mutator": "vp_verdict_parse", "fixture": "{\"check\": \"in_range\", \"valid\": false}",
     "expected": {"check": "in_range", "valid": False}, "args": {},
     "input_edge": "VerdictLine", "output_edge": "ValidationVerdict"},
    {"id": "prim:leaf:vp_rulespec_flatten", "capability": "flatten a nested rule spec to dotted keys (roundtrips)",
     "mutator": "vp_rulespec_flatten", "fixture": {"a": {"b": 1}, "c": 2},
     "expected": {"a.b": 1, "c": 2}, "args": {}, "inverse": "vp_rulespec_unflatten",
     "input_edge": "RuleSpec", "output_edge": "FlatRuleSpec"},
    {"id": "prim:leaf:vp_rulespec_unflatten", "capability": "unflatten a dotted rule spec to nested form",
     "mutator": "vp_rulespec_unflatten", "fixture": {"x.y": 1, "z": 2},
     "expected": {"x": {"y": 1}, "z": 2}, "args": {},
     "input_edge": "FlatRuleSpec", "output_edge": "RuleSpec"},
]

#: deliberately-wrong leaves — the proof gate MUST leave these candidate (never persisted as proven)
NEGATIVE_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:vp_WRONG_expected", "capability": "in_range with a wrong expected verdict",
     "mutator": "vp_in_range", "fixture": 5, "args": {"lo": 0, "hi": 10},
     "expected": {"check": "in_range", "valid": False, "value": 5, "lo": 0, "hi": 10},
     "input_edge": "Number", "output_edge": "ValidationVerdict"},
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
    # TYPE the row: canonical edge types so a workable leaf can chain (the fix for 'proven but untyped').
    receipt["input_edge_type_id"] = canonicalize_edge(spec["input_edge"])
    receipt["output_edge_type_id"] = canonicalize_edge(spec["output_edge"])
    return receipt


def prove_all() -> list[dict[str, Any]]:
    """Run every declared leaf primitive through the IMPORTED executed-proof runner."""
    return [_prove_one(s) for s in LEAF_SPECS]


def proven_rows() -> list[dict[str, Any]]:
    """Only the receipts whose executed proof PASSED (serves_truth=true), each typed with canonical edges."""
    return [r for r in prove_all() if r["serves_truth"] is True]


def build_manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in rows if r.get("input_edge_type_id") and r.get("output_edge_type_id")]
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    import hashlib
    return {
        "record_type": "proven_validation_predicate_manifest",
        "pack_id": "proven-validation-predicate", "family": FAMILY,
        "generator": "scripts/prove_leaves_validation_predicate.py",
        "generated_utc": _FIXED_UTC,
        "declared_leaf_count": len(LEAF_SPECS),
        "proven_count": len(rows),
        "typed_count": len(typed),
        "proven_primitive_ids": sorted(r["primitive_id"] for r in rows),
        "verification_level": "L7_executed_proof",
        "row_counts": {OUT_JSONL.name: len(rows)},
        "total_rows": len(rows),
        "note": "serves_truth=true is set ONLY by an executed passing proof (run_primitive_proof, imported from "
                "scripts/mutator_registry.py). Every persisted row is TYPED with canonical edge types via "
                "canonicalize_edge so it can chain. A deliberately-wrong-expected leaf stays candidate and is "
                "never persisted here.",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def _persist_row(r: dict[str, Any]) -> dict[str, Any]:
    """The workable persisted row shape (required fields + edges + proofs for lineage)."""
    return {
        "primitive_id": r["primitive_id"],
        "mutator": r["mutator"],
        "family": FAMILY,
        "capability": r.get("capability"),
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": r["input_edge"],
        "output_edge": r["output_edge"],
        "input_edge_type_id": r["input_edge_type_id"],
        "output_edge_type_id": r["output_edge_type_id"],
        "proofs": r["proofs"],
        "input_hash": r.get("input_hash"),
        "output_hash": r.get("output_hash"),
    }


def write_pack() -> dict[str, Any]:
    rows = proven_rows()
    persisted = [_persist_row(r) for r in sorted(rows, key=lambda r: r["primitive_id"])]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in persisted), encoding="utf-8")
    manifest = build_manifest(persisted)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    rows = proven_rows()
    ids = [r["primitive_id"] for r in rows]
    persisted = [_persist_row(r) for r in rows]
    # a deliberately-wrong leaf must stay candidate (the gate is real, not a rubber stamp)
    wrong = run_primitive_proof(
        NEGATIVE_SPECS[0]["id"], NEGATIVE_SPECS[0]["mutator"], NEGATIVE_SPECS[0]["fixture"],
        NEGATIVE_SPECS[0]["expected"], mutator_args=NEGATIVE_SPECS[0]["args"])
    # a second wrong path: an un-runnable fixture -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:vp_EXEC_ERROR", "vp_length_bound", 5, "irrelevant",
                              mutator_args={"min_len": 0, "max_len": 3})
    roundtrip_specs = [s for s in LEAF_SPECS if s.get("inverse")]

    checks: list[tuple[str, bool]] = [
        (">=28 leaf primitives declared", len(LEAF_SPECS) >= 28),
        (">=28 leaves PROVE serves_truth=true", len(rows) >= 28),
        ("unique primitive ids", len(set(ids)) == len(ids)),
        ("EVERY proven leaf has serves_truth=true + promoted via executed proof",
         all(r["serves_truth"] is True and r["promoted"] is True for r in rows)),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"]) for r in rows)),
        ("EVERY persisted row carries non-null input+output edge type ids (typed==proven)",
         all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in persisted)),
        ("typed_count == proven_count",
         sum(1 for r in persisted if r["input_edge_type_id"] and r["output_edge_type_id"]) == len(persisted)),
        ("roundtrip-inverse pairs prove reversible (roundtrip_test passed)",
         all(any(p["name"] == "roundtrip_test" and p["passed"] for p in
                 next(x for x in rows if x["primitive_id"] == s["id"])["proofs"]) for s in roundtrip_specs)),
        (">=2 reversible pairs present", len(roundtrip_specs) >= 2),
        ("deterministic: re-running yields identical proven rows",
         [json.dumps(r, sort_keys=True) for r in proven_rows()] == [json.dumps(r, sort_keys=True) for r in rows]),
        ("a deliberately-wrong-expected leaf stays CANDIDATE (never promoted/persisted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False and wrong["primitive_id"] not in ids),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("manifest proven_count + typed_count agree with the persisted rows",
         build_manifest(persisted)["proven_count"] == len(persisted)
         and build_manifest(persisted)["typed_count"] == len(persisted)),
        ("new validation mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_leaves_validation_predicate:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_leaves_validation_predicate: {len(rows)} REAL validation-predicate leaf primitives PROVEN "
          f"end-to-end via the imported executed-proof runner (serves_truth=true, L7_executed_proof), ALL TYPED with "
          f"canonical edge types (typed_count == proven_count == {len(persisted)}); "
          f"{len(roundtrip_specs)} reversible pairs proven roundtrip; a wrong-expected leaf and an un-runnable "
          "fixture correctly stay candidate. Workable capability, not vocabulary.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default=None)  # accepted for parity; body uses a fixed literal timestamp
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_pack()
    print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
