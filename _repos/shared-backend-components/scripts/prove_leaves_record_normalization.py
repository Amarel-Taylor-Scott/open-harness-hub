#!/usr/bin/env python3
"""scripts.prove_leaves_record_normalization — WORKABLE (proven + TYPED) deterministic leaf primitives for the
`record_normalization` family.

Repo law: `serves_truth=true` is set ONLY by a PASSING executed proof — never hand-set. A leaf that fails its
fixture-behavior / roundtrip / determinism proof (or carries a wrong expected_output) stays CANDIDATE and is NOT
persisted; that gate is the whole point. This module is ADD-ONLY: it IMPORTS the shared machinery
(`scripts.mutator_registry.run_primitive_proof` + `MUTATOR_REGISTRY`) and the pure edge canonicalizer
(`scripts.build_edge_type_retrofit.canonicalize_edge`) and never edits a contract-locked or shared file. It plugs a
family of pure `record_normalization` mutators into the shared registry via `setdefault` (idempotent, never
overwrites), proves >=28 REAL leaves end-to-end, and PERSISTS only the passers — each row carrying canonical
`input_edge_type_id` / `output_edge_type_id` so a workable primitive can actually chain (the fix for "proven but
untyped").

Coverage: canonicalize-field-names, standardize-phone-shape, standardize-email-lower, trim-all-strings,
coalesce-nulls, dedupe-key-from-fields, title-normalize, whitespace-collapse-record (+ many siblings). Logical family
edge shape: Record -> NormalizedRecord; string-level leaves carry a more specific shape (Text -> NormalizedEmail,
PhoneString -> E164Phone, …). Inverse pairs (flatten/unflatten, record<->json, kv encode/decode) prove the ROUNDTRIP
via `has_inverse` so the pair is proven reversible.

Deterministic + offline ONLY: no network, no LLM, no wall-clock (fixed literal timestamp), no RNG. CLI:
--self-test | --write.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the shared machinery — never edit it (ADD-ONLY).
from scripts.mutator_registry import (  # noqa: E402
    INVERSE_PAIRS,
    MUTATOR_REGISTRY,
    _hash,
    _receipt,
    run_primitive_proof,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

FAMILY = "record_normalization"
# Fixed literal timestamp — deterministic, no wall-clock (repo law: no datetime.now / time.time).
GENERATED_UTC = "2026-07-03"

OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_record_normalization.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_record_normalization.json"


# ── PURE deterministic record_normalization mutators. Each: (payload, **kwargs) -> (output, receipt_dict). ──
def rn_canonicalize_field_names(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {re.sub(r"[\s\-]+", "_", str(k).strip().lower()): v for k, v in record.items()}
    return out, _receipt("rn_canonicalize_field_names", before=record, after=out, lossless=False,
                         note="snake_case + lower field names")


def rn_lower_keys(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {str(k).lower(): v for k, v in record.items()}
    return out, _receipt("rn_lower_keys", before=record, after=out, lossless=False, note="lowercase keys")


def rn_strip_keys(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {str(k).strip(): v for k, v in record.items()}
    return out, _receipt("rn_strip_keys", before=record, after=out, lossless=False, note="trim whitespace from keys")


def rn_trim_all_strings(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {k: (v.strip() if isinstance(v, str) else v) for k, v in record.items()}
    return out, _receipt("rn_trim_all_strings", before=record, after=out, lossless=False,
                         note="strip all string values")


def rn_whitespace_collapse_record(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {k: (" ".join(v.split()) if isinstance(v, str) else v) for k, v in record.items()}
    return out, _receipt("rn_whitespace_collapse_record", before=record, after=out, lossless=False,
                         note="collapse internal whitespace in string values")


def rn_lower_string_values(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {k: (v.lower() if isinstance(v, str) else v) for k, v in record.items()}
    return out, _receipt("rn_lower_string_values", before=record, after=out, lossless=False,
                         note="lowercase all string values")


def rn_title_case_record(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {k: (" ".join(w.capitalize() for w in v.split()) if isinstance(v, str) else v) for k, v in record.items()}
    return out, _receipt("rn_title_case_record", before=record, after=out, lossless=False,
                         note="title-case all string values")


def rn_coalesce_nulls(record: dict[str, Any], defaults: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {k: (defaults.get(k) if v is None else v) for k, v in record.items()}
    return out, _receipt("rn_coalesce_nulls", before=record, after=out, lossless=False,
                         note="replace None values with per-field defaults")


def rn_strip_none_fields(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {k: v for k, v in record.items() if v is not None}
    return out, _receipt("rn_strip_none_fields", before=record, after=out, lossless=False,
                         note="drop null-valued fields")


def rn_default_fill_record(record: dict[str, Any], defaults: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {**defaults, **record}
    return out, _receipt("rn_default_fill_record", before=record, after=out, lossless=True,
                         note="fill missing keys from defaults")


def rn_sort_record_keys(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {k: record[k] for k in sorted(record)}
    return out, _receipt("rn_sort_record_keys", before=record, after=out, lossless=True, note="sort keys ascending")


def rn_prefix_keys(record: dict[str, Any], prefix: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {f"{prefix}{k}": v for k, v in record.items()}
    return out, _receipt("rn_prefix_keys", before=record, after=out, lossless=True, note=f"prefix keys with {prefix!r}")


def rn_dedupe_key_from_fields(record: dict[str, Any], fields: list[str],
                              sep: str = "|") -> tuple[dict[str, Any], dict[str, Any]]:
    token = sep.join(str(record.get(f, "")).strip().lower() for f in fields)
    key = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
    out = {**record, "dedupe_key": key}
    return out, _receipt("rn_dedupe_key_from_fields", before=record, after=out, lossless=True,
                         note=f"deterministic dedupe_key over {fields}")


# ── field-scoped record normalizers ──
def rn_normalize_email_field(record: dict[str, Any], field: str = "email") -> tuple[dict[str, Any], dict[str, Any]]:
    out = dict(record)
    if field in out and isinstance(out[field], str):
        out[field] = out[field].strip().lower()
    return out, _receipt("rn_normalize_email_field", before=record, after=out, lossless=False,
                         note=f"lowercase+trim the {field!r} field")


def rn_normalize_phone_field(record: dict[str, Any], field: str = "phone",
                             country: str = "1") -> tuple[dict[str, Any], dict[str, Any]]:
    out = dict(record)
    if field in out and out[field] is not None:
        digits = "".join(ch for ch in str(out[field]) if ch.isdigit())
        if len(digits) == 10:
            digits = country + digits
        out[field] = "+" + digits
    return out, _receipt("rn_normalize_phone_field", before=record, after=out, lossless=False,
                         note=f"E.164-shape the {field!r} field")


def rn_normalize_zip_field(record: dict[str, Any], field: str = "zip",
                           width: int = 5) -> tuple[dict[str, Any], dict[str, Any]]:
    out = dict(record)
    if field in out and out[field] is not None:
        out[field] = str(out[field]).zfill(width)
    return out, _receipt("rn_normalize_zip_field", before=record, after=out, lossless=False,
                         note=f"zero-pad the {field!r} field to width {width}")


def rn_normalize_bool_field(record: dict[str, Any], field: str) -> tuple[dict[str, Any], dict[str, Any]]:
    mapping = {"true": True, "false": False, "1": True, "0": False, "yes": True, "no": False, "y": True, "n": False}
    out = dict(record)
    if field in out:
        out[field] = mapping[str(out[field]).strip().lower()]
    return out, _receipt("rn_normalize_bool_field", before=record, after=out, lossless=False,
                         note=f"coerce the {field!r} field to a canonical boolean")


def rn_cast_field_int(record: dict[str, Any], field: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = dict(record)
    if field in out:
        out[field] = int(out[field])
    return out, _receipt("rn_cast_field_int", before=record, after=out, lossless=False,
                         note=f"cast the {field!r} field to int")


# ── string / scalar level normalizers ──
def rn_standardize_email_lower(value: str) -> tuple[str, dict[str, Any]]:
    out = value.strip().lower()
    return out, _receipt("rn_standardize_email_lower", before=value, after=out, lossless=False,
                         note="trim + lowercase email")


def rn_standardize_phone(value: Any, country: str = "1") -> tuple[str, dict[str, Any]]:
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if len(digits) == 10:
        digits = country + digits
    out = "+" + digits
    return out, _receipt("rn_standardize_phone", before=value, after=out, lossless=False,
                         note="strip to digits + E.164 shape")


def rn_collapse_ws_string(value: str) -> tuple[str, dict[str, Any]]:
    out = " ".join(value.split())
    return out, _receipt("rn_collapse_ws_string", before=value, after=out, lossless=False,
                         note="collapse + trim whitespace")


def rn_title_normalize(value: str) -> tuple[str, dict[str, Any]]:
    out = " ".join(w.capitalize() for w in value.split())
    return out, _receipt("rn_title_normalize", before=value, after=out, lossless=False,
                         note="title-case a name string")


def rn_lower_string(value: str) -> tuple[str, dict[str, Any]]:
    out = value.lower()
    return out, _receipt("rn_lower_string", before=value, after=out, lossless=False, note="lowercase a string")


def rn_strip_string(value: str) -> tuple[str, dict[str, Any]]:
    out = value.strip()
    return out, _receipt("rn_strip_string", before=value, after=out, lossless=False, note="trim a string")


def rn_zero_pad_zip(value: Any, width: int = 5) -> tuple[str, dict[str, Any]]:
    out = str(value).zfill(width)
    return out, _receipt("rn_zero_pad_zip", before=value, after=out, lossless=False,
                         note=f"zero-pad to width {width}")


def rn_normalize_state(value: str) -> tuple[str, dict[str, Any]]:
    mapping = {"california": "CA", "new york": "NY", "texas": "TX", "florida": "FL", "washington": "WA"}
    key = " ".join(value.split()).strip().lower()
    out = mapping.get(key, value.strip().upper())
    return out, _receipt("rn_normalize_state", before=value, after=out, lossless=False,
                         note="fold US state name -> 2-letter code")


def rn_normalize_country(value: str) -> tuple[str, dict[str, Any]]:
    mapping = {"united states": "US", "usa": "US", "us": "US", "canada": "CA", "united kingdom": "GB", "uk": "GB"}
    key = " ".join(value.split()).strip().lower()
    out = mapping.get(key, value.strip().upper())
    return out, _receipt("rn_normalize_country", before=value, after=out, lossless=False,
                         note="fold country name -> ISO-3166 alpha-2")


def rn_strip_currency(value: str) -> tuple[str, dict[str, Any]]:
    out = re.sub(r"[^\d.]", "", value)
    return out, _receipt("rn_strip_currency", before=value, after=out, lossless=False,
                         note="strip currency symbols + thousands separators")


def rn_normalize_decimal(value: str) -> tuple[str, dict[str, Any]]:
    out = value.replace(",", "").strip()
    return out, _receipt("rn_normalize_decimal", before=value, after=out, lossless=False,
                         note="drop thousands separators")


def rn_slugify(value: str) -> tuple[str, dict[str, Any]]:
    out = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return out, _receipt("rn_slugify", before=value, after=out, lossless=False, note="url-safe slug")


# ── inverse pairs (roundtrip-provable) ──
def rn_flatten_record(record: dict[str, Any], sep: str = ".") -> tuple[dict[str, Any], dict[str, Any]]:
    out: dict[str, Any] = {}

    def _walk(node: dict[str, Any], prefix: str) -> None:
        for k, v in node.items():
            key = f"{prefix}{sep}{k}" if prefix else str(k)
            if isinstance(v, dict):
                _walk(v, key)
            else:
                out[key] = v

    _walk(record, "")
    return out, _receipt("rn_flatten_record", before=record, after=out, lossless=True,
                         note="flatten nested record with dotted keys; unflatten restores")


def rn_unflatten_record(flat: dict[str, Any], sep: str = ".") -> tuple[dict[str, Any], dict[str, Any]]:
    out: dict[str, Any] = {}
    for k, v in flat.items():
        parts = str(k).split(sep)
        node = out
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = v
    return out, _receipt("rn_unflatten_record", before=flat, after=out, lossless=True,
                         note="rebuild nested record from dotted keys")


def rn_record_to_json(record: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    out = json.dumps(record, sort_keys=True)
    return out, _receipt("rn_record_to_json", before=record, after=out, lossless=True,
                         note="canonical JSON; rn_json_to_record restores")


def rn_json_to_record(text: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = json.loads(text)
    return out, _receipt("rn_json_to_record", before=text, after=out, lossless=True, note="parse canonical JSON")


def rn_kv_encode(record: dict[str, str], sep: str = ",", eq: str = "=") -> tuple[str, dict[str, Any]]:
    out = sep.join(f"{k}{eq}{record[k]}" for k in sorted(record))
    return out, _receipt("rn_kv_encode", before=record, after=out, lossless=True,
                         note="canonical (sorted) kv line; rn_kv_decode restores")


def rn_kv_decode(text: str, sep: str = ",", eq: str = "=") -> tuple[dict[str, str], dict[str, Any]]:
    out = dict(p.split(eq, 1) for p in text.split(sep)) if text else {}
    return out, _receipt("rn_kv_decode", before=text, after=out, lossless=True, note="parse kv line to record")


#: new pure mutators to plug into the shared registry (idempotent registration; never overwrites existing entries)
_NEW_MUTATORS = {
    "rn_canonicalize_field_names": rn_canonicalize_field_names, "rn_lower_keys": rn_lower_keys,
    "rn_strip_keys": rn_strip_keys, "rn_trim_all_strings": rn_trim_all_strings,
    "rn_whitespace_collapse_record": rn_whitespace_collapse_record, "rn_lower_string_values": rn_lower_string_values,
    "rn_title_case_record": rn_title_case_record, "rn_coalesce_nulls": rn_coalesce_nulls,
    "rn_strip_none_fields": rn_strip_none_fields, "rn_default_fill_record": rn_default_fill_record,
    "rn_sort_record_keys": rn_sort_record_keys, "rn_prefix_keys": rn_prefix_keys,
    "rn_dedupe_key_from_fields": rn_dedupe_key_from_fields, "rn_normalize_email_field": rn_normalize_email_field,
    "rn_normalize_phone_field": rn_normalize_phone_field, "rn_normalize_zip_field": rn_normalize_zip_field,
    "rn_normalize_bool_field": rn_normalize_bool_field, "rn_cast_field_int": rn_cast_field_int,
    "rn_standardize_email_lower": rn_standardize_email_lower, "rn_standardize_phone": rn_standardize_phone,
    "rn_collapse_ws_string": rn_collapse_ws_string, "rn_title_normalize": rn_title_normalize,
    "rn_lower_string": rn_lower_string, "rn_strip_string": rn_strip_string, "rn_zero_pad_zip": rn_zero_pad_zip,
    "rn_normalize_state": rn_normalize_state, "rn_normalize_country": rn_normalize_country,
    "rn_strip_currency": rn_strip_currency, "rn_normalize_decimal": rn_normalize_decimal, "rn_slugify": rn_slugify,
    "rn_flatten_record": rn_flatten_record, "rn_unflatten_record": rn_unflatten_record,
    "rn_record_to_json": rn_record_to_json, "rn_json_to_record": rn_json_to_record,
    "rn_kv_encode": rn_kv_encode, "rn_kv_decode": rn_kv_decode,
}
_NEW_INVERSE_PAIRS = [
    ("rn_flatten_record", "rn_unflatten_record"),
    ("rn_record_to_json", "rn_json_to_record"),
    ("rn_kv_encode", "rn_kv_decode"),
]


def register_new_mutators() -> None:
    """Plug the record_normalization mutators into the shared MUTATOR_REGISTRY (setdefault — idempotent, add-only)."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)
    for pair in _NEW_INVERSE_PAIRS:
        if pair not in INVERSE_PAIRS:
            INVERSE_PAIRS.append(pair)


register_new_mutators()

# independent recomputation of the one hash-based expected value (repo pattern — not derived from the mutator body)
_RN_DEDUPE_KEY = hashlib.sha256("john|doe".encode("utf-8")).hexdigest()[:16]


# ── leaf specs: each a REAL capability with a concrete fixture + LITERAL expected output (+ optional inverse) ──
# fields: id, capability, mutator, fixture, expected, args?, inverse?, in_edge, out_edge
LEAF_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:rn_canonicalize_field_names", "capability": "canonicalize record field names to snake_case",
     "mutator": "rn_canonicalize_field_names",
     "fixture": {"First Name": "a", "Last-Name": "b", "  Email  ": "c"},
     "expected": {"first_name": "a", "last_name": "b", "email": "c"},
     "in_edge": "Record", "out_edge": "NormalizedRecord"},
    {"id": "prim:leaf:rn_lower_keys", "capability": "lowercase record keys", "mutator": "rn_lower_keys",
     "fixture": {"A": 1, "B": 2}, "expected": {"a": 1, "b": 2}, "in_edge": "Record", "out_edge": "NormalizedRecord"},
    {"id": "prim:leaf:rn_strip_keys", "capability": "trim whitespace from record keys", "mutator": "rn_strip_keys",
     "fixture": {" a ": 1, "b ": 2}, "expected": {"a": 1, "b": 2}, "in_edge": "Record", "out_edge": "NormalizedRecord"},
    {"id": "prim:leaf:rn_trim_all_strings", "capability": "strip all string values in a record",
     "mutator": "rn_trim_all_strings", "fixture": {"a": " x ", "b": 2, "c": "y "},
     "expected": {"a": "x", "b": 2, "c": "y"}, "in_edge": "Record", "out_edge": "NormalizedRecord"},
    {"id": "prim:leaf:rn_whitespace_collapse_record", "capability": "collapse internal whitespace in record strings",
     "mutator": "rn_whitespace_collapse_record", "fixture": {"a": "  hi   there ", "b": 5},
     "expected": {"a": "hi there", "b": 5}, "in_edge": "Record", "out_edge": "NormalizedRecord"},
    {"id": "prim:leaf:rn_lower_string_values", "capability": "lowercase all string values in a record",
     "mutator": "rn_lower_string_values", "fixture": {"a": "HeLLo", "b": 2},
     "expected": {"a": "hello", "b": 2}, "in_edge": "Record", "out_edge": "NormalizedRecord"},
    {"id": "prim:leaf:rn_title_case_record", "capability": "title-case all string values in a record",
     "mutator": "rn_title_case_record", "fixture": {"name": "john smith", "n": 1},
     "expected": {"name": "John Smith", "n": 1}, "in_edge": "Record", "out_edge": "NormalizedRecord"},
    {"id": "prim:leaf:rn_coalesce_nulls", "capability": "replace null field values with per-field defaults",
     "mutator": "rn_coalesce_nulls", "fixture": {"a": None, "b": 2}, "expected": {"a": 0, "b": 2},
     "args": {"defaults": {"a": 0}}, "in_edge": "Record", "out_edge": "NormalizedRecord"},
    {"id": "prim:leaf:rn_strip_none_fields", "capability": "drop null-valued record fields",
     "mutator": "rn_strip_none_fields", "fixture": {"a": 1, "b": None, "c": 3}, "expected": {"a": 1, "c": 3},
     "in_edge": "Record", "out_edge": "NormalizedRecord"},
    {"id": "prim:leaf:rn_default_fill_record", "capability": "fill missing record fields from defaults",
     "mutator": "rn_default_fill_record", "fixture": {"a": 1}, "expected": {"a": 1, "b": 2},
     "args": {"defaults": {"a": 0, "b": 2}}, "in_edge": "Record", "out_edge": "NormalizedRecord"},
    {"id": "prim:leaf:rn_sort_record_keys", "capability": "sort record keys ascending",
     "mutator": "rn_sort_record_keys", "fixture": {"b": 2, "a": 1}, "expected": {"a": 1, "b": 2},
     "in_edge": "Record", "out_edge": "NormalizedRecord"},
    {"id": "prim:leaf:rn_prefix_keys", "capability": "prefix all record keys",
     "mutator": "rn_prefix_keys", "fixture": {"a": 1, "b": 2}, "expected": {"p_a": 1, "p_b": 2},
     "args": {"prefix": "p_"}, "in_edge": "Record", "out_edge": "NormalizedRecord"},
    {"id": "prim:leaf:rn_dedupe_key_from_fields", "capability": "derive a deterministic dedupe key from fields",
     "mutator": "rn_dedupe_key_from_fields", "fixture": {"first": "John", "last": " Doe ", "x": 1},
     "expected": {"first": "John", "last": " Doe ", "x": 1, "dedupe_key": _RN_DEDUPE_KEY},
     "args": {"fields": ["first", "last"]}, "in_edge": "Record", "out_edge": "KeyedRecord"},
    {"id": "prim:leaf:rn_normalize_email_field", "capability": "normalize the email field of a record",
     "mutator": "rn_normalize_email_field", "fixture": {"email": " John@Example.COM ", "id": 1},
     "expected": {"email": "john@example.com", "id": 1}, "in_edge": "Record", "out_edge": "NormalizedRecord"},
    {"id": "prim:leaf:rn_normalize_phone_field", "capability": "normalize the phone field of a record to E.164 shape",
     "mutator": "rn_normalize_phone_field", "fixture": {"phone": "(415) 555-1234", "id": 1},
     "expected": {"phone": "+14155551234", "id": 1}, "in_edge": "Record", "out_edge": "NormalizedRecord"},
    {"id": "prim:leaf:rn_normalize_zip_field", "capability": "zero-pad the zip field of a record",
     "mutator": "rn_normalize_zip_field", "fixture": {"zip": "123", "id": 1},
     "expected": {"zip": "00123", "id": 1}, "in_edge": "Record", "out_edge": "NormalizedRecord"},
    {"id": "prim:leaf:rn_normalize_bool_field", "capability": "coerce a record field to a canonical boolean",
     "mutator": "rn_normalize_bool_field", "fixture": {"active": "Yes", "id": 1},
     "expected": {"active": True, "id": 1}, "args": {"field": "active"},
     "in_edge": "Record", "out_edge": "NormalizedRecord"},
    {"id": "prim:leaf:rn_cast_field_int", "capability": "cast a record field to int",
     "mutator": "rn_cast_field_int", "fixture": {"count": "5", "id": 1}, "expected": {"count": 5, "id": 1},
     "args": {"field": "count"}, "in_edge": "Record", "out_edge": "NormalizedRecord"},
    {"id": "prim:leaf:rn_standardize_email_lower", "capability": "trim + lowercase an email string",
     "mutator": "rn_standardize_email_lower", "fixture": "  John.Doe@Example.COM ",
     "expected": "john.doe@example.com", "in_edge": "EmailString", "out_edge": "NormalizedEmail"},
    {"id": "prim:leaf:rn_standardize_phone", "capability": "standardize a phone string to E.164 shape",
     "mutator": "rn_standardize_phone", "fixture": "(415) 555-1234", "expected": "+14155551234",
     "in_edge": "PhoneString", "out_edge": "E164Phone"},
    {"id": "prim:leaf:rn_collapse_ws_string", "capability": "collapse + trim whitespace in a string",
     "mutator": "rn_collapse_ws_string", "fixture": "  hello   world \n", "expected": "hello world",
     "in_edge": "Text", "out_edge": "NormalizedText"},
    {"id": "prim:leaf:rn_title_normalize", "capability": "title-case a name string",
     "mutator": "rn_title_normalize", "fixture": "john  SMITH", "expected": "John Smith",
     "in_edge": "Text", "out_edge": "TitleText"},
    {"id": "prim:leaf:rn_lower_string", "capability": "lowercase a string", "mutator": "rn_lower_string",
     "fixture": "HeLLo", "expected": "hello", "in_edge": "Text", "out_edge": "NormalizedText"},
    {"id": "prim:leaf:rn_strip_string", "capability": "trim a string", "mutator": "rn_strip_string",
     "fixture": "  x  ", "expected": "x", "in_edge": "Text", "out_edge": "NormalizedText"},
    {"id": "prim:leaf:rn_zero_pad_zip", "capability": "zero-pad a zip to a fixed width",
     "mutator": "rn_zero_pad_zip", "fixture": "123", "expected": "00123", "in_edge": "ZipString", "out_edge": "ZipCode"},
    {"id": "prim:leaf:rn_normalize_state", "capability": "fold a US state name to its 2-letter code",
     "mutator": "rn_normalize_state", "fixture": "California", "expected": "CA",
     "in_edge": "StateString", "out_edge": "StateCode"},
    {"id": "prim:leaf:rn_normalize_country", "capability": "fold a country name to ISO alpha-2",
     "mutator": "rn_normalize_country", "fixture": "USA", "expected": "US",
     "in_edge": "CountryString", "out_edge": "CountryCode"},
    {"id": "prim:leaf:rn_strip_currency", "capability": "strip currency symbols + separators from money text",
     "mutator": "rn_strip_currency", "fixture": "$1,234.50", "expected": "1234.50",
     "in_edge": "MoneyString", "out_edge": "DecimalString"},
    {"id": "prim:leaf:rn_normalize_decimal", "capability": "drop thousands separators from a decimal string",
     "mutator": "rn_normalize_decimal", "fixture": "1,234.5", "expected": "1234.5",
     "in_edge": "NumberString", "out_edge": "DecimalString"},
    {"id": "prim:leaf:rn_slugify", "capability": "produce a url-safe slug from text",
     "mutator": "rn_slugify", "fixture": "Hello World!", "expected": "hello-world",
     "in_edge": "Text", "out_edge": "Slug"},
    # ── inverse pairs — the forward leaf carries `inverse` so run_primitive_proof runs a ROUNDTRIP proof ──
    {"id": "prim:leaf:rn_flatten_record", "capability": "flatten a nested record with dotted keys (roundtrips)",
     "mutator": "rn_flatten_record", "fixture": {"a": {"b": 1, "c": 2}, "d": 3},
     "expected": {"a.b": 1, "a.c": 2, "d": 3}, "inverse": "rn_unflatten_record",
     "in_edge": "Record", "out_edge": "FlatRecord"},
    {"id": "prim:leaf:rn_unflatten_record", "capability": "rebuild a nested record from dotted keys",
     "mutator": "rn_unflatten_record", "fixture": {"a.b": 1, "a.c": 2, "d": 3},
     "expected": {"a": {"b": 1, "c": 2}, "d": 3}, "in_edge": "FlatRecord", "out_edge": "Record"},
    {"id": "prim:leaf:rn_record_to_json", "capability": "serialize a record to canonical JSON (roundtrips)",
     "mutator": "rn_record_to_json", "fixture": {"z": 9, "a": 1}, "expected": '{"a": 1, "z": 9}',
     "inverse": "rn_json_to_record", "in_edge": "Record", "out_edge": "JsonText"},
    {"id": "prim:leaf:rn_json_to_record", "capability": "parse a canonical JSON record",
     "mutator": "rn_json_to_record", "fixture": '{"a": 1, "b": 2}', "expected": {"a": 1, "b": 2},
     "in_edge": "JsonText", "out_edge": "Record"},
    {"id": "prim:leaf:rn_kv_encode", "capability": "serialize a record to a canonical kv line (roundtrips)",
     "mutator": "rn_kv_encode", "fixture": {"b": "2", "a": "1"}, "expected": "a=1,b=2",
     "inverse": "rn_kv_decode", "in_edge": "Record", "out_edge": "KvLine"},
    {"id": "prim:leaf:rn_kv_decode", "capability": "parse a kv line into a record",
     "mutator": "rn_kv_decode", "fixture": "x=9,y=8", "expected": {"x": "9", "y": "8"},
     "in_edge": "KvLine", "out_edge": "Record"},
]

#: deliberately-wrong leaf — the proof gate MUST leave this candidate (never persisted as proven)
NEGATIVE_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:rn_WRONG_expected", "capability": "email-lower with a wrong expected output",
     "mutator": "rn_standardize_email_lower", "fixture": " A@B.COM ", "expected": "WRONG-not-normalized",
     "in_edge": "EmailString", "out_edge": "NormalizedEmail"},
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
    """Build a persisted row from a PASSING proof receipt: proven + TYPED (canonical edge type ids)."""
    spec = receipt["_spec"]
    in_edge, out_edge = spec["in_edge"], spec["out_edge"]
    return {
        "primitive_id": receipt["primitive_id"],
        "mutator": receipt["mutator"],
        "family": FAMILY,
        "capability": receipt["capability"],
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": in_edge,
        "output_edge": out_edge,
        "input_edge_type_id": canonicalize_edge(in_edge),
        "output_edge_type_id": canonicalize_edge(out_edge),
        "has_inverse": spec.get("inverse"),
        "proofs": receipt["proofs"],
        "input_hash": receipt["input_hash"],
        "output_hash": receipt["output_hash"],
    }


def proven_typed_rows() -> list[dict[str, Any]]:
    """The workable set: only leaves whose executed proof PASSED, each carrying canonical edge type ids."""
    rows = [_typed_row(r) for r in prove_all() if r["serves_truth"] is True]
    return sorted(rows, key=lambda r: r["primitive_id"])


def build_manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"]]
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    return {
        "record_type": "proven_leaf_primitives_manifest",
        "family": FAMILY,
        "pack_id": f"proven-{FAMILY}",
        "generator": "scripts/prove_leaves_record_normalization.py",
        "generated_utc": GENERATED_UTC,
        "declared_leaf_count": len(LEAF_SPECS),
        "proven_count": len(rows),
        "typed_count": len(typed),
        "proven_primitive_ids": sorted(r["primitive_id"] for r in rows),
        "verification_level": "L7_executed_proof",
        "row_counts": {OUT_JSONL.name: len(rows)},
        "total_rows": len(rows),
        "note": "serves_truth=true is set ONLY by an executed passing proof (run_primitive_proof, imported from "
                "scripts/mutator_registry.py). Each row carries canonical input/output edge type ids "
                "(scripts.build_edge_type_retrofit.canonicalize_edge) so the proven leaf can chain. A "
                "deliberately-wrong leaf stays candidate and is never persisted here.",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def write_pack() -> dict[str, Any]:
    rows = proven_typed_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows),
                         encoding="utf-8")
    manifest = build_manifest(rows)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    receipts = prove_all()
    proven = [r for r in receipts if r["serves_truth"] is True]
    rows = proven_typed_rows()
    ids = [r["primitive_id"] for r in receipts]

    # a deliberately-wrong leaf must stay candidate (the gate is real, not a rubber stamp)
    wrong = _prove_one(NEGATIVE_SPECS[0])
    # an un-runnable fixture (execution error) must also stay candidate
    err = run_primitive_proof("prim:leaf:rn_EXEC_ERROR", "rn_canonicalize_field_names", object(), "irrelevant")

    inverse_specs = [s for s in LEAF_SPECS if s.get("inverse")]
    proven_by_id = {r["primitive_id"]: r for r in proven}

    checks: list[tuple[str, bool]] = [
        (">=28 leaf primitives declared", len(LEAF_SPECS) >= 28),
        ("unique primitive ids", len(set(ids)) == len(ids)),
        (">=28 leaves PROVE serves_truth=true via an executed proof",
         len(proven) >= 28 and all(r["promoted"] is True for r in proven)),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"]) for r in proven)),
        (">=28 typed rows persisted", len(rows) >= 28),
        ("EVERY persisted row carries non-null input+output edge type ids",
         all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in rows)),
        ("typed_count == proven_count (every workable leaf is typed)",
         build_manifest(rows)["typed_count"] == build_manifest(rows)["proven_count"] == len(rows)),
        ("every persisted row is serves_truth=true + candidate=false + family-tagged",
         all(r["serves_truth"] is True and r["candidate"] is False and r["family"] == FAMILY for r in rows)),
        ("roundtrip-inverse leaves actually ran + PASSED a roundtrip proof",
         all(s["id"] in proven_by_id and any(p["name"] == "roundtrip_test" and p["passed"]
             for p in proven_by_id[s["id"]]["proofs"]) for s in inverse_specs)),
        ("at least 3 inverse pairs proven reversible", len(inverse_specs) >= 3),
        ("deterministic: re-running yields identical typed rows",
         [json.dumps(r, sort_keys=True) for r in proven_typed_rows()]
         == [json.dumps(r, sort_keys=True) for r in rows]),
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT among the persisted rows", wrong["primitive_id"] not in {r["primitive_id"] for r in rows}),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("new mutators registered into the shared registry (add-only setdefault seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_leaves_record_normalization:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_leaves_record_normalization: {len(rows)} REAL '{FAMILY}' leaf primitives PROVEN end-to-end "
          f"(serves_truth=true, L7_executed_proof) AND TYPED (canonical input/output edge type ids), "
          f"typed_count == proven_count == {len(rows)}; {len(inverse_specs)} inverse pairs proven reversible; a "
          "deliberately-wrong leaf and an un-runnable fixture correctly stay candidate.")
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
