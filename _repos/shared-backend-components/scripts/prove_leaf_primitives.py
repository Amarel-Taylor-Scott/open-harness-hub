#!/usr/bin/env python3
"""scripts.prove_leaf_primitives — move the proven-primitive count from 2 to >=20 with REAL executed proofs.

Red-team gap F6: the mutator/proof substrate exists (`_repos/shared-backend-components/scripts/mutator_registry.py` — 11 real executable mutators +
`run_primitive_proof()` that flips serves_truth false->true ONLY on a PASSING executed proof), but only 2 leaf
primitives had ever been proven. Vocabulary is not capability. This module is the fix: it declares >=20 REAL
deterministic leaf primitives (parse / validate / content-hash / dedupe / normalize / type-cast / envelope /
idempotency / roundtrip / schema-validate / field-project / receipt-wrap / base64 / kv / clamp / default-fill /
strip-none / zero-pad / round / sort / bool-coerce), each with a concrete fixture_input + expected_output (+ an
inverse where a roundtrip proof applies), runs EVERY ONE through the imported `run_primitive_proof`, and PERSISTS
the passing ProofReceipts (serves_truth=true, verification_level=L7_executed_proof).

FLEXIBLE / ADD-ONLY: this is a NEW parallel path. It IMPORTS the existing machinery (does not edit it) and plugs a
handful of extra pure mutators INTO the shared `MUTATOR_REGISTRY` (registration, not a rewrite — exactly the seam
that module documents). `proven_primitive_index()` exposes {primitive_id -> receipt} so the runtime can consult which
leaves are actually PROVEN, benchmarkable against the old 2. serves_truth=true here is CORRECT and required: it is
only ever set by an executed passing proof — a deliberately-wrong leaf stays candidate. Offline + deterministic
(no wall-clock/RNG/network in bodies). CLI: --self-test | --write [--date D].
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import base64 as _b64
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the existing machinery — never edit it (ADD-ONLY / flexible-multi-path).
from scripts.mutator_registry import (  # noqa: E402
    INVERSE_PAIRS,
    MUTATOR_REGISTRY,
    _hash,
    _receipt,
    run_primitive_proof,
)

OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_leaf_primitives.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest.json"


# ── extra PURE deterministic mutators, registered into the shared registry (one registration each, not a rewrite) ──
def _normalize_whitespace(text: str) -> tuple[str, dict[str, Any]]:
    out = " ".join(text.split())
    return out, _receipt("normalize_whitespace", before=text, after=out, lossless=False, note="collapse+trim whitespace")


def _casefold_text(text: str) -> tuple[str, dict[str, Any]]:
    out = text.lower()
    return out, _receipt("casefold_text", before=text, after=out, lossless=False, note="lowercase-normalize")


def _content_hash_sha256(payload: Any) -> tuple[str, dict[str, Any]]:
    out = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    return out, _receipt("content_hash_sha256", before=payload, after=out, lossless=False, note="canonical content hash")


def _base64_encode(text: str) -> tuple[str, dict[str, Any]]:
    out = _b64.b64encode(text.encode("utf-8")).decode("ascii")
    return out, _receipt("base64_encode", before=text, after=out, lossless=True, note="base64 encode; decode restores")


def _base64_decode(text: str) -> tuple[str, dict[str, Any]]:
    out = _b64.b64decode(text.encode("ascii")).decode("utf-8")
    return out, _receipt("base64_decode", before=text, after=out, lossless=True, note="base64 decode")


def _kv_serialize(record: dict[str, str], sep: str = ",", eq: str = "=") -> tuple[str, dict[str, Any]]:
    out = sep.join(f"{k}{eq}{record[k]}" for k in sorted(record))
    return out, _receipt("kv_serialize", before=record, after=out, lossless=True, note="canonical (sorted) kv line; kv_parse restores")


def _kv_parse(text: str, sep: str = ",", eq: str = "=") -> tuple[dict[str, str], dict[str, Any]]:
    out = dict(p.split(eq, 1) for p in text.split(sep)) if text else {}
    return out, _receipt("kv_parse", before=text, after=out, lossless=True, note="parse kv line to dict")


def _list_unique(items: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    out = list(dict.fromkeys(items))
    return out, _receipt("list_unique", before=items, after=out, lossless=False, note="order-preserving unique")


def _clamp(value: Any, lo: Any, hi: Any) -> tuple[Any, dict[str, Any]]:
    out = max(lo, min(hi, value))
    return out, _receipt("clamp", before=value, after=out, lossless=False, note=f"clamp to [{lo},{hi}]")


def _default_fill(record: dict[str, Any], defaults: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {**defaults, **record}
    return out, _receipt("default_fill", before=record, after=out, lossless=True, note="fill missing keys from defaults")


def _strip_none(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {k: v for k, v in record.items() if v is not None}
    return out, _receipt("strip_none", before=record, after=out, lossless=False, note="drop null-valued fields")


def _zero_pad(value: Any, width: int) -> tuple[str, dict[str, Any]]:
    out = str(value).zfill(width)
    return out, _receipt("zero_pad", before=value, after=out, lossless=False, note=f"left-pad to width {width}")


def _round_number(value: float, ndigits: int) -> tuple[float, dict[str, Any]]:
    out = round(value, ndigits)
    return out, _receipt("round_number", before=value, after=out, lossless=False, note=f"round to {ndigits} places")


def _sort_list(items: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    out = sorted(items)
    return out, _receipt("sort_list", before=items, after=out, lossless=False, note="stable-sort ascending")


def _bool_coerce(value: str) -> tuple[bool, dict[str, Any]]:
    mapping = {"true": True, "false": False, "1": True, "0": False, "yes": True, "no": False}
    out = mapping[str(value).strip().lower()]
    return out, _receipt("bool_coerce", before=value, after=out, lossless=False, note="canonical truthy/falsey coercion")


#: new pure mutators to plug into the shared registry (idempotent registration; never overwrites existing entries)
_NEW_MUTATORS = {
    "normalize_whitespace": _normalize_whitespace, "casefold_text": _casefold_text,
    "content_hash_sha256": _content_hash_sha256, "base64_encode": _base64_encode, "base64_decode": _base64_decode,
    "kv_serialize": _kv_serialize, "kv_parse": _kv_parse, "list_unique": _list_unique, "clamp": _clamp,
    "default_fill": _default_fill, "strip_none": _strip_none, "zero_pad": _zero_pad, "round_number": _round_number,
    "sort_list": _sort_list, "bool_coerce": _bool_coerce,
}
_NEW_INVERSE_PAIRS = [("base64_encode", "base64_decode"), ("kv_serialize", "kv_parse")]


def register_new_mutators() -> None:
    """Plug the extra pure mutators into the shared MUTATOR_REGISTRY (registration, not a rewrite). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)
    for pair in _NEW_INVERSE_PAIRS:
        if pair not in INVERSE_PAIRS:
            INVERSE_PAIRS.append(pair)


register_new_mutators()

# precomputed reference values (independent recomputation of the deterministic function — the repo's own pattern)
_IDEMPOTENCY_KEY_U1_PAY = hashlib.sha256("u1|pay".encode()).hexdigest()[:24]
_CONTENT_HASH_A1 = hashlib.sha256(json.dumps({"a": 1}, sort_keys=True, default=str).encode()).hexdigest()


# ── the leaf primitives: each a REAL capability with a concrete fixture + expected output (+ optional inverse) ──
# spec fields: (primitive_id, capability, mutator, fixture, expected, args, inverse)
LEAF_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:field_rename", "capability": "rename record fields by mapping",
     "mutator": "field_rename", "fixture": {"a": 1, "b": 2}, "expected": {"x": 1, "b": 2},
     "args": {"mapping": {"a": "x"}}},
    {"id": "prim:leaf:field_project", "capability": "project a record down to a keep-list",
     "mutator": "field_project", "fixture": {"a": 1, "b": 2, "c": 3}, "expected": {"a": 1, "c": 3},
     "args": {"keep": ["a", "c"]}},
    {"id": "prim:leaf:type_cast", "capability": "coerce field types deterministically",
     "mutator": "type_cast", "fixture": {"n": "5", "f": "1.5"}, "expected": {"n": 5, "f": 1.5},
     "args": {"casts": {"n": "int", "f": "float"}}},
    {"id": "prim:leaf:envelope_roundtrip", "capability": "wrap payload in a policy envelope (roundtrips)",
     "mutator": "envelope_wrap", "fixture": {"p": 1},
     "expected": {"payload": {"p": 1}, "policy": {"pol": "x"}, "envelope_version": 1},
     "args": {"policy": {"pol": "x"}}, "inverse": "envelope_unwrap"},
    {"id": "prim:leaf:envelope_unwrap", "capability": "unwrap a policy envelope to its payload",
     "mutator": "envelope_unwrap", "fixture": {"payload": {"q": 2}, "policy": {}, "envelope_version": 1},
     "expected": {"q": 2}, "args": {}},
    {"id": "prim:leaf:output_receipt_wrap", "capability": "attach a content-hash receipt to an output",
     "mutator": "output_receipt_wrapper", "fixture": "hello",
     "expected": {"output": "hello", "receipt": {"output_hash": _hash("hello"), "verified_first": True}}, "args": {}},
    {"id": "prim:leaf:idempotency_key", "capability": "derive a deterministic idempotency key",
     "mutator": "idempotency_wrapper", "fixture": {"user": "u1", "op": "pay"},
     "expected": {"user": "u1", "op": "pay", "idempotency_key": _IDEMPOTENCY_KEY_U1_PAY},
     "args": {"key_fields": ["user", "op"]}},
    {"id": "prim:leaf:row_to_json_roundtrip", "capability": "serialize a row to canonical JSON (roundtrips)",
     "mutator": "row_to_json", "fixture": {"z": 9}, "expected": '{"z": 9}', "args": {}, "inverse": "json_to_row"},
    {"id": "prim:leaf:json_to_row", "capability": "parse a JSON row",
     "mutator": "json_to_row", "fixture": '{"a": 1, "b": 2}', "expected": {"a": 1, "b": 2}, "args": {}},
    {"id": "prim:leaf:dedupe_by_key", "capability": "collapse rows by key, preserving aliases",
     "mutator": "dedupe_by_key",
     "fixture": [{"k": 1, "id": "a"}, {"k": 1, "id": "b"}, {"k": 2, "id": "c"}],
     "expected": [{"k": 1, "id": "a"}, {"k": 2, "id": "c"}], "args": {"key": "k"}},
    {"id": "prim:leaf:schema_validate", "capability": "validate a record against required fields",
     "mutator": "schema_validator_inserter", "fixture": {"name": "x"},
     "expected": {"name": "x", "_validation": {"required": ["name", "email"], "missing": ["email"], "valid": False}},
     "args": {"required": ["name", "email"]}},
    {"id": "prim:leaf:normalize_whitespace", "capability": "normalize whitespace in text",
     "mutator": "normalize_whitespace", "fixture": "  hello   world \n", "expected": "hello world", "args": {}},
    {"id": "prim:leaf:casefold_text", "capability": "lowercase-normalize text",
     "mutator": "casefold_text", "fixture": "HeLLo", "expected": "hello", "args": {}},
    {"id": "prim:leaf:content_hash_sha256", "capability": "compute a canonical content hash",
     "mutator": "content_hash_sha256", "fixture": {"a": 1}, "expected": _CONTENT_HASH_A1, "args": {}},
    {"id": "prim:leaf:base64_roundtrip", "capability": "base64-encode text (roundtrips)",
     "mutator": "base64_encode", "fixture": "data", "expected": "ZGF0YQ==", "args": {}, "inverse": "base64_decode"},
    {"id": "prim:leaf:base64_decode", "capability": "base64-decode text",
     "mutator": "base64_decode", "fixture": "aGVsbG8=", "expected": "hello", "args": {}},
    {"id": "prim:leaf:kv_roundtrip", "capability": "serialize a dict to a canonical kv line (roundtrips)",
     "mutator": "kv_serialize", "fixture": {"a": "1", "b": "2"}, "expected": "a=1,b=2", "args": {}, "inverse": "kv_parse"},
    {"id": "prim:leaf:kv_parse", "capability": "parse a kv line to a dict",
     "mutator": "kv_parse", "fixture": "x=9,y=8", "expected": {"x": "9", "y": "8"}, "args": {}},
    {"id": "prim:leaf:list_unique", "capability": "order-preserving list dedupe",
     "mutator": "list_unique", "fixture": [1, 2, 2, 3, 1], "expected": [1, 2, 3], "args": {}},
    {"id": "prim:leaf:clamp", "capability": "clamp a number into a range",
     "mutator": "clamp", "fixture": 15, "expected": 10, "args": {"lo": 0, "hi": 10}},
    {"id": "prim:leaf:default_fill", "capability": "fill missing fields from defaults",
     "mutator": "default_fill", "fixture": {"a": 1}, "expected": {"a": 1, "b": 2}, "args": {"defaults": {"a": 0, "b": 2}}},
    {"id": "prim:leaf:strip_none", "capability": "drop null-valued fields",
     "mutator": "strip_none", "fixture": {"a": 1, "b": None, "c": 3}, "expected": {"a": 1, "c": 3}, "args": {}},
    {"id": "prim:leaf:zero_pad", "capability": "left-pad an id to a fixed width",
     "mutator": "zero_pad", "fixture": 42, "expected": "00042", "args": {"width": 5}},
    {"id": "prim:leaf:round_number", "capability": "round a number to N places",
     "mutator": "round_number", "fixture": 3.14159, "expected": 3.14, "args": {"ndigits": 2}},
    {"id": "prim:leaf:sort_list", "capability": "sort a list ascending",
     "mutator": "sort_list", "fixture": [3, 1, 2], "expected": [1, 2, 3], "args": {}},
    {"id": "prim:leaf:bool_coerce", "capability": "coerce a string to a canonical boolean",
     "mutator": "bool_coerce", "fixture": "true", "expected": True, "args": {}},
]

#: deliberately-wrong leaves — the proof gate MUST leave these candidate (never persisted as proven)
NEGATIVE_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:WRONG_expected", "capability": "field_rename with a wrong expected output",
     "mutator": "field_rename", "fixture": {"a": 1}, "expected": {"WRONG": 999}, "args": {"mapping": {"a": "x"}}},
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


def proven_primitive_index() -> dict[str, dict[str, Any]]:
    """{primitive_id -> ProofReceipt} for leaves whose executed proof PASSED (serves_truth=true).

    The runtime consults this to know which leaf primitives are actually PROVEN (vs merely declared candidates)."""
    return {r["primitive_id"]: r for r in prove_all() if r["serves_truth"] is True}


def build_manifest(receipts: list[dict[str, Any]], *, date: str) -> dict[str, Any]:
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in receipts)
    return {
        "record_type": "proven_leaf_primitives_manifest",
        "pack_id": "proven-leaf-primitives", "generator": "scripts/prove_leaf_primitives.py",
        "generated_utc": date,
        "declared_leaf_count": len(LEAF_SPECS),
        "proven_count": len(receipts),
        "proven_primitive_ids": sorted(r["primitive_id"] for r in receipts),
        "verification_level": "L7_executed_proof",
        "row_counts": {OUT_JSONL.name: len(receipts)},
        "total_rows": len(receipts),
        "note": "serves_truth=true here is CORRECT + required — set ONLY by an executed passing proof "
                "(run_primitive_proof, imported from scripts/mutator_registry.py); a deliberately-wrong leaf "
                "stays candidate and is never persisted here.",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def write_pack(*, date: str) -> dict[str, Any]:
    index = proven_primitive_index()
    receipts = [index[k] for k in sorted(index)]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in receipts), encoding="utf-8")
    manifest = build_manifest(receipts, date=date)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    receipts = prove_all()
    index = proven_primitive_index()
    ids = [r["primitive_id"] for r in receipts]
    # a deliberately-wrong leaf must stay candidate (the gate is real, not a rubber stamp)
    wrong = _prove_one(NEGATIVE_SPECS[0])
    # a second wrong path: pass a fixture the mutator cannot handle -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:EXEC_ERROR", "content_hash_sha256", object(), "irrelevant")

    checks: list[tuple[str, bool]] = [
        (">=20 leaf primitives declared", len(LEAF_SPECS) >= 20),
        ("unique primitive ids", len(set(ids)) == len(ids)),
        ("EVERY declared leaf PROVES serves_truth=true via an executed proof",
         all(r["serves_truth"] is True and r["promoted"] is True for r in receipts)),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"]) for r in receipts)),
        (">=20 primitives in the proven index (moved off 2)", len(index) >= 20),
        ("roundtrip leaves actually ran a roundtrip proof", all(
            any(p["name"] == "roundtrip_test" and p["passed"] for p in index[s["id"]]["proofs"])
            for s in LEAF_SPECS if s.get("inverse"))),
        ("deterministic: re-running yields identical receipts",
         [json.dumps(r, sort_keys=True) for r in prove_all()] == [json.dumps(r, sort_keys=True) for r in receipts]),
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT in the proven index", wrong["primitive_id"] not in index),
        ("an un-runnable fixture fails the proof, does not promote", err["serves_truth"] is False and err["promoted"] is False),
        ("manifest proven_count matches the index", build_manifest(list(index.values()), date="X")["proven_count"] == len(index)),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_leaf_primitives:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_leaf_primitives: {len(index)} REAL leaf primitives PROVEN end-to-end via the imported "
          f"executed-proof runner (serves_truth=true, L7_executed_proof) — the proven count moved from 2 to "
          f"{len(index)}; a deliberately-wrong leaf and an un-runnable fixture correctly stay candidate. "
          "Real capability, not vocabulary.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default=None)
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
    manifest = write_pack(date=date)
    print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
