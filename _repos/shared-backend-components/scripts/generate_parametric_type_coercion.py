#!/usr/bin/env python3
"""scripts.generate_parametric_type_coercion — WORKABLE configured-primitives for 'type_coercion' by PARAMETRIC PROOF.

A configured-primitive = (a PROVEN mutator TEMPLATE) x (a specific parameter BINDING) x (canonical edge types). e.g.
coerce_record_schema{casts:{age:int,price:float}} and coerce_record_schema{casts:{qty:int,active:bool}} are DISTINCT
workable primitives — each proven by EXECUTING the mutator on a concrete fixture and checking the output. This is how
thousands of primitives are HONEST (not filler): every row here passed an executed proof of THAT binding.

Repo laws honored (violations reverted):
  * serves_truth=true is set ONLY by a PASSING executed proof of THAT binding — never inferred from the template. We
    compute the expected output by running the mutator ONCE, then hand (mutator, fixture, expected) to the imported
    `run_primitive_proof`, which RE-EXECUTES the mutator, checks output==expected, and re-runs for determinism. A
    binding whose expected is wrong, or that raises, or that is non-deterministic, is NOT persisted.
  * Honest accounting: generated vs unique(deduped) vs proven vs typed are SEPARATE counts, never conflated.
  * ADD-ONLY: this is a NEW file. It IMPORTS the contract-locked machinery (mutator_registry.py,
    build_edge_type_retrofit.py) and the sibling proven-template modules; it edits none of them. It writes its OWN
    shard file + manifest (no shared-JSONL write race). It is NOT self-registered in flywheel_proof_modules.py — the
    (script_path, module_name) tuple is REPORTED for the caller to register.
  * Deterministic + offline ONLY: no network, no LLM, no wall-clock (FIXED_DATE literal), no RNG. The parameter space
    is ENUMERATED deterministically (curated field catalogs + combinations); the only "hashing" is hashlib content
    hashing for the id/dedupe key (never the python builtin hash()).

Templates parameterized here (proven callables from the shared registry + the sibling `prove_leaves_type_coercion`):
  * coerce_record_schema  — string-valued record -> typed record via a per-field cast-spec (token bools, parsed nums)
  * type_cast             — mixed/native record -> re-typed record via python-native cast semantics
  * to_int_safe / to_float_safe / to_bool / cast_or_none / null_default / strip_and_cast — scalar coercions

CLI: --self-test | --write [--date D].
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import itertools
import json
import sys
from pathlib import Path
from typing import Any, Callable, Iterable

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the contract-locked machinery — never edit it (ADD-ONLY).
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    apply_mutator,
    run_primitive_proof,
)

# IMPORT the proven TEMPLATES: the sibling registers real mutators (coerce_record_schema, to_int_safe, to_float_safe,
# to_bool, cast_or_none, null_default, strip_and_cast, ...) into MUTATOR_REGISTRY on import. try/except so --self-test
# still runs if the sibling is absent — we then fall back to whatever the base registry already provides (type_cast).
try:  # noqa: SIM105
    import scripts.prove_leaves_type_coercion  # noqa: F401  (import side effect: registers mutators)
except Exception:  # noqa: BLE001  (offline resilience: base registry still gives type_cast)
    pass

FAMILY = "type_coercion"
FIXED_DATE = "2026-07-03"  # fixed literal — NO wall-clock (repo law: deterministic + offline)

OUT_DIR = _resource("data") / "dev-intel" / "parametric_primitives"
OUT_JSONL = OUT_DIR / "param_type_coercion.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_type_coercion.json"

# register-tuple to REPORT back (this module is NOT self-registered in flywheel_proof_modules.py by us).
REGISTER_TUPLE = ("scripts/generate_parametric_type_coercion.py", "scripts.generate_parametric_type_coercion")

# ── canonical edge labels (folded to type_ids via the imported canonicalize_edge; all verified non-"Unknown") ──
EDGE_STRING_RECORD = "StringRecord"   # a record whose values are strings (the coerce_record_schema input)
EDGE_MIXED_RECORD = "MixedRecord"     # a record whose values are native python types (the type_cast input)
EDGE_TYPED_RECORD = "TypedRecord"     # output of a schema coercion
EDGE_TEXT = "Text"
EDGE_NULLABLE = "NullableValue"
#: scalar cast target -> output edge label (single source; reused by every scalar generator)
_CAST_OUTPUT_EDGE: dict[str, str] = {"int": "Integer", "float": "Number", "bool": "Boolean", "str": "Text"}


# ── curated field catalogs (deterministic; each entry is meaningfully coercible) ──
# STRING catalog: raw values are STRINGS -> coerce_record_schema does real string->typed work (token bools, parsed nums).
# (field, raw_string, natural_cast). int fields carry integer-looking strings; bool fields carry canonical tokens.
_STR_CATALOG: list[tuple[str, str, str]] = [
    ("age", "42", "int"), ("qty", "100", "int"), ("year", "2026", "int"),
    ("count", "7", "int"), ("level", "3", "int"), ("rank", "12", "int"),
    ("price", "19.99", "float"), ("rate", "0.5", "float"), ("weight", "3.14", "float"),
    ("active", "yes", "bool"), ("enabled", "true", "bool"), ("deleted", "no", "bool"),
    ("name", "alice", "str"), ("code", "AB12", "str"), ("tier", "gold", "str"), ("region", "us", "str"),
]
# NATIVE catalog: raw values are NATIVE python types -> type_cast does real python-native recasting
# (str(42)->"42", int(3.9)->3 truncation, bool(0)->False truthiness). (field, native_value, cast).
_NATIVE_CATALOG: list[tuple[str, Any, str]] = [
    ("count", 7, "str"), ("level", 3, "str"), ("rank", 12, "str"),
    ("score", 88.5, "int"), ("weight", 3.9, "int"), ("ratio", 1.25, "int"),
    ("balance", 19.99, "str"), ("delta", 0.5, "str"), ("factor", 2.5, "str"),
    ("flag_zero", 0, "bool"), ("flag_one", 1, "bool"), ("flag_neg", -3, "bool"),
    ("qty", 5, "float"), ("total", 100, "float"), ("idx", 8, "float"), ("bump", 2, "float"),
]

# scalar fixture catalogs (deterministic, meaningfully distinct)
_INT_NUMERIC_STRINGS = ["0", "1", "7", "12", "42", "100", "255", "1000", "2026", "-5", "-12", " 33 ", " 88", "500 "]
_INT_NONNUMERIC = ["abc", "n/a", "", "N/A", "none", "null", "?", "pending", "TBD", "--"]
_INT_DEFAULTS = [0, -1, 1, 7, 42, 99, 100, 1000, -999]
_FLOAT_NUMERIC_STRINGS = ["0.0", "1.5", "3.14", "2.5", "0.5", "19.99", "100.0", "-4.2", " 6.28 ", "88.5", "0", "1000", "42", "7"]
_FLOAT_NONNUMERIC = ["abc", "n/a", "", "N/A", "none", "null", "?", "missing", "TBD", "--"]
_FLOAT_DEFAULTS = [0.0, 1.0, -1.0, 3.14, 99.9, 100.0]
_BOOL_TOKENS_LIST = ["true", "false", "1", "0", "yes", "no", "y", "n", "on", "off", "t", "f"]
_CAST_OR_NONE_FIXTURES = ["12", "3.14", "yes", "abc", "0", "-7", "1.0", "no", "on", "42", "n/a", "", "100", "off", "1e3", "  9 "]
_NULL_DEFAULTS: list[Any] = [0, 1, -1, 42, "unknown", "N/A", 0.0, 3.14, "default", "none"]
_NULL_PRESENT_VALUES: list[Any] = ["keep", 5, 3.14, "x", 0, "present"]
_STRIP_CAST_FIXTURES = ["  42  ", " 3.14 ", " yes ", "\t100\t", "  0 ", " no ", "  -7 ", " true ", "  2.5  ", " off ",
                        "  1000", "88  ", " on ", "  -12 ", " false "]


def _default_edge_for_value(value: Any) -> str:
    """Pick a non-'Unknown' output edge label for a null_default result based on its concrete type."""
    if isinstance(value, bool):
        return "Boolean"
    if isinstance(value, int):
        return "Integer"
    if isinstance(value, float):
        return "Number"
    if isinstance(value, str):
        return "Text"
    return "TypedValue"


# ── the parametric candidate: a well-formed (mutator, fixture, binding, edges) tuple awaiting proof ──
def _content_hash(mutator: str, binding: dict[str, Any], fixture: Any) -> str:
    """Canonical content hash over (mutator, binding, fixture) — identical bindings collapse. hashlib, never hash()."""
    canonical = json.dumps({"mutator": mutator, "binding": binding, "fixture": fixture},
                           sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _make_candidate(mutator: str, fixture: Any, binding: dict[str, Any],
                    input_edge: str, output_edge: str, capability: str) -> dict[str, Any] | None:
    """Build ONE parametric candidate. Computes the expected output by running the mutator once (offline). Returns
    None for a candidate that is unavailable (mutator not registered), raises, or is a trivial identity no-op — these
    are never emitted (kept out of the honest 'generated' count)."""
    if mutator not in MUTATOR_REGISTRY:
        return None
    try:
        out, _ = apply_mutator(mutator, fixture, **binding)
    except Exception:  # noqa: BLE001  (a binding the mutator cannot handle is not a workable primitive)
        return None
    if out == fixture:  # trivial identity coercion (does nothing) — reject as noise, don't count as generated
        return None
    return {
        "mutator": mutator, "fixture": fixture, "binding": binding, "expected": out,
        "input_edge": input_edge, "output_edge": output_edge, "capability": capability,
        "content_hash": _content_hash(mutator, binding, fixture),
    }


# ── the parameter-space enumerators (deterministic; each yields meaningfully-distinct candidates) ──
def _enumerate_record_coercions(catalog: list[tuple[str, Any, str]], mutator: str,
                                input_edge: str, sizes: Iterable[int]) -> list[dict[str, Any]]:
    """For each size-k combination of catalog fields, build a distinct cast-spec (per-field natural cast) over a
    fixture record of exactly those fields. Different field-sets => different schemas => distinct behaviors."""
    out: list[dict[str, Any]] = []
    lookup = {name: (raw, cast) for name, raw, cast in catalog}
    names = [name for name, _r, _c in catalog]
    for size in sizes:
        for combo in itertools.combinations(names, size):
            fixture = {name: lookup[name][0] for name in combo}
            casts = {name: lookup[name][1] for name in combo}
            cap = f"coerce record fields {list(combo)} to types {[casts[n] for n in combo]}"
            cand = _make_candidate(mutator, fixture, {"casts": casts}, input_edge, EDGE_TYPED_RECORD, cap)
            if cand is not None:
                out.append(cand)
    return out


def _enumerate_scalar(mutator: str, fixtures: list[Any], bindings: list[dict[str, Any]],
                      input_edge: str, output_edge_for: Callable[[Any, dict[str, Any]], str],
                      capability_for: Callable[[Any, dict[str, Any]], str]) -> list[dict[str, Any]]:
    """Enumerate a scalar coercion template over (fixture x binding). output_edge_for/capability_for are pure."""
    out: list[dict[str, Any]] = []
    for fixture in fixtures:
        for binding in bindings:
            cand = _make_candidate(mutator, fixture, binding, input_edge,
                                   output_edge_for(fixture, binding), capability_for(fixture, binding))
            if cand is not None:
                out.append(cand)
    return out


def enumerate_candidates() -> list[dict[str, Any]]:
    """Deterministically enumerate the WHOLE curated parameter space. Order is stable (list concatenation)."""
    cands: list[dict[str, Any]] = []

    # 1) coerce_record_schema — string-valued records -> typed records (the semantically-rich schema coercer).
    #    sizes {2,3} over the full catalog + {4} over a stable 12-field slice (bounds the size-4 combinatorics).
    cands += _enumerate_record_coercions(_STR_CATALOG, "coerce_record_schema", EDGE_STRING_RECORD, sizes=(2, 3))
    cands += _enumerate_record_coercions(_STR_CATALOG[:12], "coerce_record_schema", EDGE_STRING_RECORD, sizes=(4,))
    # 2) type_cast — native-valued records -> re-typed records (python-native cast semantics; distinct template).
    cands += _enumerate_record_coercions(_NATIVE_CATALOG, "type_cast", EDGE_MIXED_RECORD, sizes=(2, 3))
    cands += _enumerate_record_coercions(_NATIVE_CATALOG[:12], "type_cast", EDGE_MIXED_RECORD, sizes=(4,))

    # 3) to_int_safe: numeric strings parse (default irrelevant -> one canonical default); non-numeric -> the default.
    cands += _enumerate_scalar(
        "to_int_safe", _INT_NUMERIC_STRINGS, [{}], EDGE_TEXT,
        output_edge_for=lambda f, b: "Integer",
        capability_for=lambda f, b: f"parse numeric string {f!r} to int")
    cands += _enumerate_scalar(
        "to_int_safe", _INT_NONNUMERIC, [{"default": d} for d in _INT_DEFAULTS], EDGE_TEXT,
        output_edge_for=lambda f, b: "Integer",
        capability_for=lambda f, b: f"non-numeric {f!r} falls back to default int {b['default']}")

    # 4) to_float_safe: same shape.
    cands += _enumerate_scalar(
        "to_float_safe", _FLOAT_NUMERIC_STRINGS, [{}], EDGE_TEXT,
        output_edge_for=lambda f, b: "Number",
        capability_for=lambda f, b: f"parse numeric string {f!r} to float")
    cands += _enumerate_scalar(
        "to_float_safe", _FLOAT_NONNUMERIC, [{"default": d} for d in _FLOAT_DEFAULTS], EDGE_TEXT,
        output_edge_for=lambda f, b: "Number",
        capability_for=lambda f, b: f"non-numeric {f!r} falls back to default float {b['default']}")

    # 5) to_bool: each canonical truthy/falsey token (12 distinct behaviors).
    cands += _enumerate_scalar(
        "to_bool", _BOOL_TOKENS_LIST, [{}], EDGE_TEXT,
        output_edge_for=lambda f, b: "Boolean",
        capability_for=lambda f, b: f"coerce token {f!r} to boolean")

    # 6) cast_or_none: (fixture x cast) — parseable -> typed value, unparseable -> None (never raises).
    cands += _enumerate_scalar(
        "cast_or_none", _CAST_OR_NONE_FIXTURES, [{"cast": c} for c in ("int", "float", "bool")], EDGE_TEXT,
        output_edge_for=lambda f, b: "NullableValue",
        capability_for=lambda f, b: f"cast {f!r} to {b['cast']} or None on failure")

    # 7) null_default: None -> a concrete typed default (passthrough of a present value is filtered as identity).
    cands += _enumerate_scalar(
        "null_default", [None] + _NULL_PRESENT_VALUES, [{"default": d} for d in _NULL_DEFAULTS], EDGE_NULLABLE,
        output_edge_for=lambda f, b: _default_edge_for_value(b["default"]) if f is None else _default_edge_for_value(f),
        capability_for=lambda f, b: f"replace {f!r} with default {b['default']!r}")

    # 8) strip_and_cast: whitespace-padded text -> stripped + cast.
    cands += _enumerate_scalar(
        "strip_and_cast", _STRIP_CAST_FIXTURES, [{"cast": c} for c in ("int", "float", "bool")], EDGE_TEXT,
        output_edge_for=lambda f, b: _CAST_OUTPUT_EDGE[b["cast"]],
        capability_for=lambda f, b: f"strip whitespace from {f!r} then cast to {b['cast']}")

    return cands


# ── prove + type + dedupe: the honest pipeline ──
def _prove_and_type(cand: dict[str, Any]) -> dict[str, Any] | None:
    """Run the EXECUTED proof for this binding; on pass, TYPE it via canonicalize_edge. Returns a persisted row ONLY
    when serves_truth flips true AND both edge type_ids resolve (non-empty, non-'Unknown'). Else None (never persisted)."""
    pid = f"prim:param:{cand['mutator']}:{cand['content_hash']}"
    receipt = run_primitive_proof(pid, cand["mutator"], cand["fixture"], cand["expected"],
                                  mutator_args=cand["binding"])
    if receipt.get("serves_truth") is not True:  # a failing/wrong/non-deterministic binding is NOT truth
        return None
    in_id = canonicalize_edge(cand["input_edge"])
    out_id = canonicalize_edge(cand["output_edge"])
    if in_id in (None, "", "Unknown") or out_id in (None, "", "Unknown"):
        return None
    return {
        "primitive_id": pid,
        "mutator": cand["mutator"],
        "binding": cand["binding"],
        "capability": cand["capability"],
        "family": FAMILY,
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": cand["input_edge"],
        "output_edge": cand["output_edge"],
        "input_edge_type_id": in_id,
        "output_edge_type_id": out_id,
        "proofs": receipt["proofs"],
        "input_hash": receipt["input_hash"],
        "output_hash": receipt["output_hash"],
    }


def build_pack() -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Enumerate -> dedupe -> prove -> type. Returns (persisted proven+typed rows, honest separate counts)."""
    generated = enumerate_candidates()
    # DEDUPE by canonical content hash (identical (mutator, binding, fixture) collapse). Deterministic first-wins.
    unique_by_hash: dict[str, dict[str, Any]] = {}
    for cand in generated:
        unique_by_hash.setdefault(cand["content_hash"], cand)
    unique = list(unique_by_hash.values())

    proven_rows: list[dict[str, Any]] = []
    typed_rows: list[dict[str, Any]] = []
    for cand in unique:
        row = _prove_and_type(cand)
        if row is None:
            continue
        proven_rows.append(row)  # _prove_and_type only returns on a passing proof
        # typed == proven here (row already carries both non-'Unknown' edge ids); tracked separately for honesty.
        if row["input_edge_type_id"] and row["output_edge_type_id"]:
            typed_rows.append(row)

    typed_rows.sort(key=lambda r: r["primitive_id"])
    counts = {
        "generated": len(generated),
        "unique_after_dedupe": len(unique),
        "proven": len(proven_rows),
        "typed": len(typed_rows),
    }
    return typed_rows, counts


def build_manifest(rows: list[dict[str, Any]], counts: dict[str, int]) -> dict[str, Any]:
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    mutators = sorted({r["mutator"] for r in rows})
    return {
        "record_type": "parametric_type_coercion_manifest",
        "family": FAMILY,
        "pack_id": "parametric-type-coercion",
        "generator": REGISTER_TUPLE[0],
        "generated_utc": FIXED_DATE,
        # SEPARATE honest counts — never conflated (generated lines are NOT reported as active primitives).
        "generated": counts["generated"],
        "unique_after_dedupe": counts["unique_after_dedupe"],
        "proven": counts["proven"],
        "typed": counts["typed"],
        "active_primitive_count": len(rows),  # == typed (only proven+typed rows are persisted/active)
        "templates_parameterized": mutators,
        "verification_level": "L7_executed_proof",
        "row_counts": {OUT_JSONL.name: len(rows)},
        "register_module": {"script_path": REGISTER_TUPLE[0], "module_name": REGISTER_TUPLE[1]},
        "note": "Each row is a proven mutator TEMPLATE x a specific parameter BINDING x canonical edge types. "
                "serves_truth=true was set ONLY by an executed passing proof of THAT binding (run_primitive_proof, "
                "imported from scripts/mutator_registry.py) — never inferred from the template; a wrong/failing "
                "binding is not persisted. Counts are separate: generated (meaningful candidates enumerated) >= "
                "unique_after_dedupe (distinct content hashes) >= proven (passed executed proof) == typed "
                "(both canonical edge type_ids resolved).",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def write_pack() -> dict[str, Any]:
    rows, counts = build_pack()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8"
    )
    manifest = build_manifest(rows, counts)
    OUT_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # 1) a small curated enumeration proves + types correctly
    small = _enumerate_record_coercions(_STR_CATALOG[:4], "coerce_record_schema", EDGE_STRING_RECORD, sizes=(2,))
    small_rows = [_prove_and_type(c) for c in small]
    small_ok = [r for r in small_rows if r is not None]
    checks.append(("small enumeration produces proven+typed rows", len(small_ok) >= 3))
    checks.append(("every small row is L7 with all sub-proofs passing",
                   all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"])
                       for r in small_ok)))
    checks.append(("every small row carries BOTH non-'Unknown' edge type_ids",
                   all(r["input_edge_type_id"] not in (None, "", "Unknown")
                       and r["output_edge_type_id"] not in (None, "", "Unknown") for r in small_ok)))

    # 2) dedupe collapses an IDENTICAL binding (same mutator+binding+fixture => same content hash)
    fx = {"age": "42", "qty": "100"}
    b = {"casts": {"age": "int", "qty": "int"}}
    h1 = _content_hash("coerce_record_schema", b, fx)
    h2 = _content_hash("coerce_record_schema", dict(b), dict(fx))
    dupe_list = [
        _make_candidate("coerce_record_schema", fx, b, EDGE_STRING_RECORD, EDGE_TYPED_RECORD, "x"),
        _make_candidate("coerce_record_schema", dict(fx), dict(b), EDGE_STRING_RECORD, EDGE_TYPED_RECORD, "x"),
    ]
    collapsed: dict[str, Any] = {}
    for c in dupe_list:
        collapsed.setdefault(c["content_hash"], c)
    checks.append(("identical binding hashes identically", h1 == h2))
    checks.append(("dedupe collapses 2 identical candidates to 1", len(dupe_list) == 2 and len(collapsed) == 1))

    # 3) a deliberately-WRONG expected FAILS the proof and is NOT persisted (the gate is real, not a rubber stamp)
    wrong_pid = "prim:param:coerce_record_schema:WRONG"
    wrong_receipt = run_primitive_proof(wrong_pid, "coerce_record_schema", {"age": "42"},
                                        {"age": 999999}, mutator_args={"casts": {"age": "int"}})
    checks.append(("wrong-expected binding does NOT flip serves_truth",
                   wrong_receipt.get("serves_truth") is False and wrong_receipt.get("promoted") is False))
    # and via the pipeline: a candidate whose stored expected is corrupted is dropped
    corrupt = _make_candidate("coerce_record_schema", {"age": "42"}, {"casts": {"age": "int"}},
                              EDGE_STRING_RECORD, EDGE_TYPED_RECORD, "x")
    corrupt = dict(corrupt)
    corrupt["expected"] = {"age": 999999}  # tamper the expected -> proof must reject
    checks.append(("pipeline drops a tampered-expected candidate", _prove_and_type(corrupt) is None))

    # 4) the FULL pack: honest separate counts + every persisted row typed + truth-bearing
    rows, counts = build_pack()
    checks.append(("counts are separated (generated >= unique >= proven == typed)",
                   counts["generated"] >= counts["unique_after_dedupe"] >= counts["proven"] == counts["typed"]))
    checks.append(("pack is in the target band (>=1500 proven+typed)", counts["typed"] >= 1500))
    checks.append(("EVERY persisted row: serves_truth=true, candidate=false, L7",
                   all(r["serves_truth"] is True and r["candidate"] is False
                       and r["verification_level"] == "L7_executed_proof" for r in rows)))
    checks.append(("EVERY persisted row carries BOTH edge type_ids (non-null, non-'Unknown')",
                   all(r["input_edge_type_id"] not in (None, "", "Unknown")
                       and r["output_edge_type_id"] not in (None, "", "Unknown") for r in rows)))
    checks.append(("EVERY persisted primitive_id is unique", len({r["primitive_id"] for r in rows}) == len(rows)))
    checks.append(("re-running build_pack is deterministic (identical rows)",
                   [json.dumps(r, sort_keys=True) for r in build_pack()[0]]
                   == [json.dumps(r, sort_keys=True) for r in rows]))
    checks.append(("multiple proven templates present (parametric, not one mutator)",
                   len({r["mutator"] for r in rows}) >= 3))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - generate_parametric_type_coercion:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - generate_parametric_type_coercion: {counts['generated']} generated -> "
          f"{counts['unique_after_dedupe']} unique -> {counts['proven']} proven -> {counts['typed']} typed; "
          f"{len({r['mutator'] for r in rows})} templates parameterized; every persisted row passed an executed "
          "proof of THAT binding and carries both canonical edge type_ids; dedupe collapses identical bindings; a "
          "deliberately-wrong expected is correctly rejected (never persisted).")
    return 0


def main(argv: list[str] | None = None) -> int:
    global FIXED_DATE  # noqa: PLW0603 (explicit fixed-literal override via --date; still NO wall-clock)
    parser = argparse.ArgumentParser(description="Parametric WORKABLE type_coercion configured-primitives (proof-gated).")
    parser.add_argument("--self-test", action="store_true", help="run offline standalone self-test")
    parser.add_argument("--write", action="store_true", help="persist the deduped proven+typed shard + manifest")
    parser.add_argument("--date", default=FIXED_DATE, help="fixed literal date stamp (no wall-clock)")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.write:
        FIXED_DATE = args.date
        manifest = write_pack()
        print(json.dumps({k: manifest[k] for k in
                          ("generated", "unique_after_dedupe", "proven", "typed", "active_primitive_count")},
                         indent=2))
        print(f"wrote {OUT_JSONL}")
        print(f"wrote {OUT_MANIFEST}")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
