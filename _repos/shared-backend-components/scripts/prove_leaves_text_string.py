#!/usr/bin/env python3
"""scripts.prove_leaves_text_string — WORKABLE (proven + TYPED) deterministic leaf primitives for the 'text_string' family.

Vocabulary is not capability, and "proven but untyped" leaves cannot chain. This module is the fix for the
text_string family: it declares >=28 REAL pure deterministic leaf callables (case/casefold, trim/strip, pad/truncate,
reverse, slugify, split/join, replace, normalize-whitespace, count-substr, title-case, snake<->camel/kebab, ...),
registers them into the shared MUTATOR_REGISTRY (setdefault — add-only, never overwrite), runs EVERY ONE through the
imported executed-proof runner `run_primitive_proof` (which flips serves_truth false->true ONLY on a PASSING executed
proof — a wrong-expected leaf stays candidate and is never persisted), and TYPES every persisted row by folding its
input_edge / output_edge through `canonicalize_edge` (input_edge_type_id / output_edge_type_id) so a workable leaf can
compose by edge type. Where a leaf has a true inverse (swapcase, reverse, split/join, snake/camel, snake/kebab) the
ROUNDTRIP is proven via has_inverse so the pair is proven reversible.

ADD-ONLY / flexible: this is a NEW parallel path. It IMPORTS the existing machinery
(_repos/shared-backend-components/scripts/mutator_registry.py, _repos/shared-backend-components/scripts/build_edge_type_retrofit.py) and never edits it. Deterministic + offline ONLY:
no network, no LLM, no wall-clock (fixed literal timestamp), no RNG. CLI: --self-test | --write.
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

# IMPORT the existing machinery — never edit it (ADD-ONLY).
from scripts.mutator_registry import (  # noqa: E402
    INVERSE_PAIRS,
    MUTATOR_REGISTRY,
    _receipt,
    run_primitive_proof,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

FAMILY = "text_string"
# fixed literal timestamp — NO wall-clock (deterministic + offline law).
GENERATED_UTC = "2026-07-03T00:00:00Z"

OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_text_string.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_text_string.json"

# tuple this module contributes to the shared proof registry (REPORTED, not self-registered).
REGISTER_TUPLE = ("scripts/prove_leaves_text_string.py", "scripts.prove_leaves_text_string")


# ── PURE deterministic text_string leaf mutators: each (payload, **kwargs) -> (transformed_output, receipt_dict) ──
def _r(name: str, before: Any, after: Any, lossless: bool, note: str) -> dict[str, Any]:
    return _receipt(name, before=before, after=after, lossless=lossless, note=note)


def ts_upper(text: str) -> tuple[str, dict[str, Any]]:
    out = text.upper()
    return out, _r("ts_upper", text, out, False, "uppercase")


def ts_lower(text: str) -> tuple[str, dict[str, Any]]:
    out = text.lower()
    return out, _r("ts_lower", text, out, False, "lowercase")


def ts_casefold(text: str) -> tuple[str, dict[str, Any]]:
    out = text.casefold()
    return out, _r("ts_casefold", text, out, False, "aggressive caseless-match fold")


def ts_swapcase(text: str) -> tuple[str, dict[str, Any]]:
    out = text.swapcase()
    return out, _r("ts_swapcase", text, out, True, "swap case; self-inverse (roundtrips)")


def ts_capitalize(text: str) -> tuple[str, dict[str, Any]]:
    out = text.capitalize()
    return out, _r("ts_capitalize", text, out, False, "capitalize first char, lower rest")


def ts_title_case(text: str) -> tuple[str, dict[str, Any]]:
    out = text.title()
    return out, _r("ts_title_case", text, out, False, "title-case each word")


def ts_strip(text: str) -> tuple[str, dict[str, Any]]:
    out = text.strip()
    return out, _r("ts_strip", text, out, False, "trim leading+trailing whitespace")


def ts_lstrip(text: str) -> tuple[str, dict[str, Any]]:
    out = text.lstrip()
    return out, _r("ts_lstrip", text, out, False, "trim leading whitespace")


def ts_rstrip(text: str) -> tuple[str, dict[str, Any]]:
    out = text.rstrip()
    return out, _r("ts_rstrip", text, out, False, "trim trailing whitespace")


def ts_strip_chars(text: str, chars: str = " ") -> tuple[str, dict[str, Any]]:
    out = text.strip(chars)
    return out, _r("ts_strip_chars", text, out, False, f"trim leading+trailing {chars!r}")


def ts_ljust(text: str, width: int, fill: str = " ") -> tuple[str, dict[str, Any]]:
    out = text.ljust(width, fill)
    return out, _r("ts_ljust", text, out, False, f"left-justify to width {width}")


def ts_rjust(text: str, width: int, fill: str = " ") -> tuple[str, dict[str, Any]]:
    out = text.rjust(width, fill)
    return out, _r("ts_rjust", text, out, False, f"right-justify to width {width}")


def ts_center(text: str, width: int, fill: str = " ") -> tuple[str, dict[str, Any]]:
    out = text.center(width, fill)
    return out, _r("ts_center", text, out, False, f"center to width {width}")


def ts_zero_pad(text: str, width: int) -> tuple[str, dict[str, Any]]:
    out = text.zfill(width)
    return out, _r("ts_zero_pad", text, out, False, f"zero-fill to width {width}")


def ts_truncate(text: str, maxlen: int) -> tuple[str, dict[str, Any]]:
    out = text[:maxlen]
    return out, _r("ts_truncate", text, out, False, f"hard truncate to {maxlen}")


def ts_truncate_ellipsis(text: str, maxlen: int, ellipsis: str = "...") -> tuple[str, dict[str, Any]]:
    out = text if len(text) <= maxlen else text[: max(0, maxlen - len(ellipsis))] + ellipsis
    return out, _r("ts_truncate_ellipsis", text, out, False, f"truncate to {maxlen} with {ellipsis!r}")


def ts_reverse(text: str) -> tuple[str, dict[str, Any]]:
    out = text[::-1]
    return out, _r("ts_reverse", text, out, True, "reverse characters; self-inverse (roundtrips)")


def ts_reverse_words(text: str) -> tuple[str, dict[str, Any]]:
    out = " ".join(text.split(" ")[::-1])
    return out, _r("ts_reverse_words", text, out, False, "reverse word order (single-space)")


def ts_slugify(text: str) -> tuple[str, dict[str, Any]]:
    lowered = text.lower()
    out = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return out, _r("ts_slugify", text, out, False, "lowercase, non-alnum->hyphen, trim hyphens")


def ts_normalize_whitespace(text: str) -> tuple[str, dict[str, Any]]:
    out = " ".join(text.split())
    return out, _r("ts_normalize_whitespace", text, out, False, "collapse+trim all whitespace runs")


def ts_replace(text: str, old: str, new: str) -> tuple[str, dict[str, Any]]:
    out = text.replace(old, new)
    return out, _r("ts_replace", text, out, False, f"replace {old!r}->{new!r}")


def ts_remove_punctuation(text: str) -> tuple[str, dict[str, Any]]:
    out = re.sub(r"[^\w\s]", "", text)
    return out, _r("ts_remove_punctuation", text, out, False, "drop punctuation")


def ts_expand_tabs(text: str, tabsize: int = 8) -> tuple[str, dict[str, Any]]:
    out = text.expandtabs(tabsize)
    return out, _r("ts_expand_tabs", text, out, False, f"expand tabs to {tabsize} spaces")


def ts_collapse_blank_lines(text: str) -> tuple[str, dict[str, Any]]:
    out = re.sub(r"\n{2,}", "\n", text)
    return out, _r("ts_collapse_blank_lines", text, out, False, "collapse consecutive newlines")


def ts_count_substr(text: str, sub: str) -> tuple[int, dict[str, Any]]:
    out = text.count(sub)
    return out, _r("ts_count_substr", text, out, False, f"count non-overlapping {sub!r}")


def ts_count_words(text: str) -> tuple[int, dict[str, Any]]:
    out = len(text.split())
    return out, _r("ts_count_words", text, out, False, "whitespace-delimited word count")


def ts_count_chars(text: str) -> tuple[int, dict[str, Any]]:
    out = len(text)
    return out, _r("ts_count_chars", text, out, False, "character length")


def ts_index_of(text: str, sub: str) -> tuple[int, dict[str, Any]]:
    out = text.find(sub)
    return out, _r("ts_index_of", text, out, False, f"first index of {sub!r} (-1 if absent)")


def ts_startswith(text: str, prefix: str) -> tuple[bool, dict[str, Any]]:
    out = text.startswith(prefix)
    return out, _r("ts_startswith", text, out, False, f"starts with {prefix!r}")


# ── split/join — Text<->Collection, a true inverse pair (join(split(x))==x for the default separator) ──
def ts_split(text: str, sep: str = ",") -> tuple[list[str], dict[str, Any]]:
    out = text.split(sep)
    return out, _r("ts_split", text, out, True, f"split on {sep!r}; ts_join restores")


def ts_join(parts: list[str], sep: str = ",") -> tuple[str, dict[str, Any]]:
    out = sep.join(parts)
    return out, _r("ts_join", parts, out, True, f"join on {sep!r}")


# ── snake<->camel — a true inverse pair over well-formed identifiers ──
def ts_snake_to_camel(text: str) -> tuple[str, dict[str, Any]]:
    parts = text.split("_")
    out = parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])
    return out, _r("ts_snake_to_camel", text, out, True, "snake_case->camelCase; ts_camel_to_snake restores")


def ts_camel_to_snake(text: str) -> tuple[str, dict[str, Any]]:
    out = re.sub(r"([A-Z])", r"_\1", text).lower()
    return out, _r("ts_camel_to_snake", text, out, True, "camelCase->snake_case")


# ── snake<->kebab — a true inverse pair ──
def ts_snake_to_kebab(text: str) -> tuple[str, dict[str, Any]]:
    out = text.replace("_", "-")
    return out, _r("ts_snake_to_kebab", text, out, True, "snake_case->kebab-case; ts_kebab_to_snake restores")


def ts_kebab_to_snake(text: str) -> tuple[str, dict[str, Any]]:
    out = text.replace("-", "_")
    return out, _r("ts_kebab_to_snake", text, out, True, "kebab-case->snake_case")


#: new pure mutators to plug into the shared registry (idempotent setdefault; never overwrites existing entries)
_NEW_MUTATORS = {
    "ts_upper": ts_upper, "ts_lower": ts_lower, "ts_casefold": ts_casefold, "ts_swapcase": ts_swapcase,
    "ts_capitalize": ts_capitalize, "ts_title_case": ts_title_case, "ts_strip": ts_strip, "ts_lstrip": ts_lstrip,
    "ts_rstrip": ts_rstrip, "ts_strip_chars": ts_strip_chars, "ts_ljust": ts_ljust, "ts_rjust": ts_rjust,
    "ts_center": ts_center, "ts_zero_pad": ts_zero_pad, "ts_truncate": ts_truncate,
    "ts_truncate_ellipsis": ts_truncate_ellipsis, "ts_reverse": ts_reverse, "ts_reverse_words": ts_reverse_words,
    "ts_slugify": ts_slugify, "ts_normalize_whitespace": ts_normalize_whitespace, "ts_replace": ts_replace,
    "ts_remove_punctuation": ts_remove_punctuation, "ts_expand_tabs": ts_expand_tabs,
    "ts_collapse_blank_lines": ts_collapse_blank_lines, "ts_count_substr": ts_count_substr,
    "ts_count_words": ts_count_words, "ts_count_chars": ts_count_chars, "ts_index_of": ts_index_of,
    "ts_startswith": ts_startswith, "ts_split": ts_split, "ts_join": ts_join,
    "ts_snake_to_camel": ts_snake_to_camel, "ts_camel_to_snake": ts_camel_to_snake,
    "ts_snake_to_kebab": ts_snake_to_kebab, "ts_kebab_to_snake": ts_kebab_to_snake,
}
_NEW_INVERSE_PAIRS = [
    ("ts_split", "ts_join"), ("ts_snake_to_camel", "ts_camel_to_snake"),
    ("ts_snake_to_kebab", "ts_kebab_to_snake"),
]


def register_new_mutators() -> None:
    """Plug the text_string leaf mutators into the shared MUTATOR_REGISTRY (setdefault — add-only). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)
    for pair in _NEW_INVERSE_PAIRS:
        if pair not in INVERSE_PAIRS:
            INVERSE_PAIRS.append(pair)


register_new_mutators()


# ── the leaf specs: each a REAL text capability with a concrete fixture + expected output (+ optional inverse) ──
# fields: id, mutator, fixture, expected, args, inverse, input_edge, output_edge
LEAF_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:ts_upper", "mutator": "ts_upper", "fixture": "hello", "expected": "HELLO",
     "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_lower", "mutator": "ts_lower", "fixture": "HeLLo", "expected": "hello",
     "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_casefold", "mutator": "ts_casefold", "fixture": "Straße", "expected": "strasse",
     "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_swapcase", "mutator": "ts_swapcase", "fixture": "Hello World", "expected": "hELLO wORLD",
     "inverse": "ts_swapcase", "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_capitalize", "mutator": "ts_capitalize", "fixture": "hELLO world", "expected": "Hello world",
     "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_title_case", "mutator": "ts_title_case", "fixture": "hello world", "expected": "Hello World",
     "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_strip", "mutator": "ts_strip", "fixture": "  hi  ", "expected": "hi",
     "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_lstrip", "mutator": "ts_lstrip", "fixture": "  hi  ", "expected": "hi  ",
     "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_rstrip", "mutator": "ts_rstrip", "fixture": "  hi  ", "expected": "  hi",
     "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_strip_chars", "mutator": "ts_strip_chars", "fixture": "xxhixx", "expected": "hi",
     "args": {"chars": "x"}, "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_ljust", "mutator": "ts_ljust", "fixture": "5", "expected": "5  ",
     "args": {"width": 3}, "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_rjust", "mutator": "ts_rjust", "fixture": "5", "expected": "  5",
     "args": {"width": 3}, "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_center", "mutator": "ts_center", "fixture": "hi", "expected": "  hi  ",
     "args": {"width": 6}, "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_zero_pad", "mutator": "ts_zero_pad", "fixture": "42", "expected": "00042",
     "args": {"width": 5}, "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_truncate", "mutator": "ts_truncate", "fixture": "hello world", "expected": "hello",
     "args": {"maxlen": 5}, "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_truncate_ellipsis", "mutator": "ts_truncate_ellipsis", "fixture": "hello world",
     "expected": "hello...", "args": {"maxlen": 8}, "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_reverse", "mutator": "ts_reverse", "fixture": "abcde", "expected": "edcba",
     "inverse": "ts_reverse", "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_reverse_words", "mutator": "ts_reverse_words", "fixture": "a b c", "expected": "c b a",
     "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_slugify", "mutator": "ts_slugify", "fixture": "Hello, World!", "expected": "hello-world",
     "input_edge": "Text", "output_edge": "TextSlug"},
    {"id": "prim:leaf:ts_normalize_whitespace", "mutator": "ts_normalize_whitespace", "fixture": "  a   b \n",
     "expected": "a b", "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_replace", "mutator": "ts_replace", "fixture": "foobar", "expected": "f00bar",
     "args": {"old": "o", "new": "0"}, "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_remove_punctuation", "mutator": "ts_remove_punctuation", "fixture": "a,b.c!",
     "expected": "abc", "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_expand_tabs", "mutator": "ts_expand_tabs", "fixture": "a\tb", "expected": "a       b",
     "args": {"tabsize": 8}, "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_collapse_blank_lines", "mutator": "ts_collapse_blank_lines", "fixture": "a\n\n\nb",
     "expected": "a\nb", "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_count_substr", "mutator": "ts_count_substr", "fixture": "banana", "expected": 3,
     "args": {"sub": "a"}, "input_edge": "Text", "output_edge": "Count"},
    {"id": "prim:leaf:ts_count_words", "mutator": "ts_count_words", "fixture": "the quick brown fox", "expected": 4,
     "input_edge": "Text", "output_edge": "Count"},
    {"id": "prim:leaf:ts_count_chars", "mutator": "ts_count_chars", "fixture": "abcd", "expected": 4,
     "input_edge": "Text", "output_edge": "Count"},
    {"id": "prim:leaf:ts_index_of", "mutator": "ts_index_of", "fixture": "hello", "expected": 2,
     "args": {"sub": "l"}, "input_edge": "Text", "output_edge": "Integer"},
    {"id": "prim:leaf:ts_startswith", "mutator": "ts_startswith", "fixture": "hello", "expected": True,
     "args": {"prefix": "he"}, "input_edge": "Text", "output_edge": "Boolean"},
    {"id": "prim:leaf:ts_split", "mutator": "ts_split", "fixture": "a,b,c", "expected": ["a", "b", "c"],
     "inverse": "ts_join", "input_edge": "Text", "output_edge": "Collection"},
    {"id": "prim:leaf:ts_join", "mutator": "ts_join", "fixture": ["x", "y", "z"], "expected": "x,y,z",
     "input_edge": "Collection", "output_edge": "Text"},
    {"id": "prim:leaf:ts_snake_to_camel", "mutator": "ts_snake_to_camel", "fixture": "hello_world_foo",
     "expected": "helloWorldFoo", "inverse": "ts_camel_to_snake", "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_camel_to_snake", "mutator": "ts_camel_to_snake", "fixture": "myVarName",
     "expected": "my_var_name", "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_snake_to_kebab", "mutator": "ts_snake_to_kebab", "fixture": "a_b_c", "expected": "a-b-c",
     "inverse": "ts_kebab_to_snake", "input_edge": "Text", "output_edge": "Text"},
    {"id": "prim:leaf:ts_kebab_to_snake", "mutator": "ts_kebab_to_snake", "fixture": "a-b-c", "expected": "a_b_c",
     "input_edge": "Text", "output_edge": "Text"},
]

#: deliberately-wrong leaf — the proof gate MUST leave this candidate (never persisted as proven).
NEGATIVE_SPEC: dict[str, Any] = {
    "id": "prim:leaf:ts_WRONG_expected", "mutator": "ts_upper", "fixture": "hi", "expected": "WRONG",
    "input_edge": "Text", "output_edge": "Text",
}


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    receipt = run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )
    receipt["input_edge"] = spec["input_edge"]
    receipt["output_edge"] = spec["output_edge"]
    return receipt


def prove_all() -> list[dict[str, Any]]:
    """Run every declared text_string leaf through the imported executed-proof runner."""
    return [_prove_one(s) for s in LEAF_SPECS]


def _typed_row(receipt: dict[str, Any]) -> dict[str, Any]:
    """A persisted, TYPED proven-leaf row: serves_truth=true + canonical edge type ids (so it can chain)."""
    return {
        "primitive_id": receipt["primitive_id"],
        "mutator": receipt["mutator"],
        "family": FAMILY,
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": receipt["input_edge"],
        "output_edge": receipt["output_edge"],
        "input_edge_type_id": canonicalize_edge(receipt["input_edge"]),
        "output_edge_type_id": canonicalize_edge(receipt["output_edge"]),
        "input_hash": receipt["input_hash"],
        "output_hash": receipt["output_hash"],
        "proofs": receipt["proofs"],
    }


def proven_typed_rows() -> list[dict[str, Any]]:
    """TYPED rows for leaves whose executed proof PASSED (serves_truth=true). Sorted by primitive_id."""
    rows = [_typed_row(r) for r in prove_all() if r["serves_truth"] is True]
    return sorted(rows, key=lambda r: r["primitive_id"])


def build_manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"]]
    return {
        "record_type": "proven_text_string_manifest",
        "pack_id": "proven-text-string-leaves",
        "generator": "scripts/prove_leaves_text_string.py",
        "family": FAMILY,
        "generated_utc": GENERATED_UTC,
        "declared_leaf_count": len(LEAF_SPECS),
        "proven_count": len(rows),
        "typed_count": len(typed),
        "proven_primitive_ids": [r["primitive_id"] for r in rows],
        "verification_level": "L7_executed_proof",
        "roundtrip_pairs": _NEW_INVERSE_PAIRS + [("ts_swapcase", "ts_swapcase"), ("ts_reverse", "ts_reverse")],
        "row_counts": {OUT_JSONL.name: len(rows)},
        "note": "serves_truth=true is set ONLY by an executed passing proof (run_primitive_proof); a wrong-expected "
                "leaf stays candidate and is never persisted. Every row is TYPED via canonicalize_edge so it can chain.",
    }


def write_pack() -> dict[str, Any]:
    rows = proven_typed_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(rows)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    receipts = prove_all()
    rows = proven_typed_rows()
    ids = [r["primitive_id"] for r in receipts]

    # a deliberately-wrong leaf must stay candidate (the gate is real, not a rubber stamp)
    wrong = _prove_one(NEGATIVE_SPEC)
    # an un-runnable fixture (non-str) -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:ts_EXEC_ERROR", "ts_upper", object(), "irrelevant")

    typed = [r for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"]]
    roundtrip_specs = [s for s in LEAF_SPECS if s.get("inverse")]

    checks: list[tuple[str, bool]] = [
        (">=28 leaf primitives declared", len(LEAF_SPECS) >= 28),
        ("unique primitive ids", len(set(ids)) == len(ids)),
        (">=28 leaves PROVE serves_truth=true via an executed proof",
         sum(1 for r in receipts if r["serves_truth"] is True) >= 28),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"])
             for r in receipts if r["serves_truth"] is True)),
        ("EVERY persisted row carries non-null input+output edge type ids", len(typed) == len(rows) and len(rows) >= 28),
        ("persisted rows are serves_truth=true / candidate=false",
         all(r["serves_truth"] is True and r["candidate"] is False for r in rows)),
        ("roundtrip-inverse leaves actually ran a PASSING roundtrip proof",
         len(roundtrip_specs) >= 3 and all(
            any(p["name"] == "roundtrip_test" and p["passed"] for p in _prove_one(s)["proofs"])
            for s in roundtrip_specs)),
        ("split<->join, snake<->camel, snake<->kebab, swapcase, reverse all reversible",
         all(_prove_one(s)["serves_truth"] is True for s in roundtrip_specs)),
        ("deterministic: re-running yields identical typed rows",
         [json.dumps(r, sort_keys=True) for r in proven_typed_rows()]
         == [json.dumps(r, sort_keys=True) for r in rows]),
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT in the persisted rows",
         wrong["primitive_id"] not in {r["primitive_id"] for r in rows}),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("manifest proven_count == typed_count == persisted rows",
         build_manifest(rows)["proven_count"] == build_manifest(rows)["typed_count"] == len(rows)),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_leaves_text_string:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_leaves_text_string: {len(rows)} WORKABLE text_string leaf primitives PROVEN end-to-end "
          f"(serves_truth=true, L7_executed_proof) AND TYPED ({len(typed)}/{len(rows)} carry canonical input+output "
          f"edge type ids so they chain); {len(roundtrip_specs)} inverse pairs proven reversible; a wrong-expected "
          "leaf and an un-runnable fixture correctly stay candidate. Register tuple: "
          f"{REGISTER_TUPLE}.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        manifest = write_pack()
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
