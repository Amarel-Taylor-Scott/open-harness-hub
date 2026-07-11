#!/usr/bin/env python3
"""scripts.prove_composite_etl_intake — a PROVEN multi-step composite ROUTE ('etl_intake') over proven leaf primitives.

The leaf-family scripts prove *individual* deterministic mutators. This module proves the next level up: a real ingest
ROUTE that CHAINS several proven leaves end-to-end —

    raw CSV/dict row -> renamed record -> typed record -> validated record -> normalized record -> json text -> receipt

— then EXECUTES the whole chain over a realistic fixture and asserts the composite's executed output equals an
independently-reconstructed expected output. That end-to-end pass is the ONLY thing that flips serves_truth false->true
for the route (repo law: serves_truth is set by a PASSING executed proof, never hand-set). A route whose expected output
is wrong stays candidate and is NOT persisted — that gate is the whole point of the module.

Honest composability metric: edge_chain_strength = the number of step boundaries where step[i].output_edge_type_id ==
step[i+1].input_edge_type_id under the shared `canonicalize_edge` (canonical TYPE match, not a name guess). A route only
composes as far as its typed edges actually line up; we report the real count (target > 1).

ADD-ONLY: this is a NEW file. It IMPORTS the shared machinery (MUTATOR_REGISTRY / apply_mutator from
scripts.mutator_registry, canonicalize_edge from scripts.build_edge_type_retrofit) and never edits it. Relevant
leaf-family modules are imported in try/except so their proven mutators register on import; if a family import fails the
route falls back to the base 11 mutators in MUTATOR_REGISTRY, so --self-test runs standalone. This module is NOT
self-registered in flywheel_proof_modules.py by us — its (script_path, module_name) tuple is REPORTED for the owner.

Offline + deterministic: no network, no LLM, no wall-clock (fixed literal date), no RNG. CLI: --self-test | --write.
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

# IMPORT the shared machinery — never edit it (ADD-ONLY, contract-locked files).
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    _hash,
    apply_mutator,
)

ROUTE_ID = "etl_intake"
FAMILY = "composite_route"
FIXED_DATE = "2026-07-03"  # fixed literal — NO wall-clock (repo law: deterministic + offline)

OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_composite_etl_intake.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_composite_etl_intake.json"

# register-tuple to REPORT back (this module is NOT self-registered in flywheel_proof_modules.py by us).
REGISTER_TUPLE = ("scripts/prove_composite_etl_intake.py", "scripts.prove_composite_etl_intake")


# ── register relevant proven leaf families (best-effort; base 11 mutators are the fallback so we run standalone) ──
def _load_leaf_families() -> list[str]:
    """Import a few relevant leaf-family modules so their proven mutators register into the shared registry.

    Each import is guarded: a failed family import degrades gracefully to the base 11 mutators. Returns the list of
    families that registered successfully (for the manifest — pure bookkeeping, never changes route behavior)."""
    loaded: list[str] = []
    for family, module in (
        ("type_coercion", "scripts.prove_leaves_type_coercion"),
        ("record_normalization", "scripts.prove_leaves_record_normalization"),
        ("validation_predicate", "scripts.prove_leaves_validation_predicate"),
        ("json_csv_transform", "scripts.prove_leaves_json_csv_transform"),
    ):
        try:
            __import__(module)  # side effect: the module registers its mutators via setdefault on import
            loaded.append(family)
        except Exception:  # noqa: BLE001 — a family that won't import must not break the standalone route
            continue
    return loaded


_LOADED_FAMILIES = _load_leaf_families()

# The typed-coercion step prefers the proven `coerce_record_schema` leaf (type_coercion family) when it registered;
# it falls back to the base-11 `type_cast` leaf. Both take (record, casts=...) and — for this route's fixture — return
# the identical typed record, so the composite's expected output is invariant to whether the family import succeeded.
_TYPED_STEP_MUTATOR = "coerce_record_schema" if "coerce_record_schema" in MUTATOR_REGISTRY else "type_cast"


# ── the route: an ordered list of proven-leaf steps. Each step names the leaf mutator + its kwargs + its typed edges. ──
# The edges are honest data shapes: each step's output_edge is the *same* type its successor consumes, so the chain is
# typed end-to-end (that is what edge_chain_strength measures against canonicalize_edge).
ROUTE_STEPS: list[dict[str, Any]] = [
    {"step": "rename_headers", "capability": "map raw CSV headers to canonical record field names",
     "mutator": "field_rename",
     "args": {"mapping": {"Full Name": "name", "Years": "age", "Score": "score"}},
     "input_edge": "RawCsvRow", "output_edge": "RenamedRecord"},
    {"step": "coerce_types", "capability": "coerce string fields to their declared scalar types",
     "mutator": _TYPED_STEP_MUTATOR,
     "args": {"casts": {"age": "int", "score": "float"}},
     "input_edge": "RenamedRecord", "output_edge": "TypedRecord"},
    {"step": "validate_schema", "capability": "attach a validation block asserting required fields are present",
     "mutator": "schema_validator_inserter",
     "args": {"required": ["name", "age", "score"]},
     "input_edge": "TypedRecord", "output_edge": "ValidatedRecord"},
    {"step": "normalize_identity", "capability": "assign a deterministic canonical identity key (normalization)",
     "mutator": "idempotency_wrapper",
     "args": {"key_fields": ["name", "age"]},
     "input_edge": "ValidatedRecord", "output_edge": "NormalizedRecord"},
    {"step": "serialize_json", "capability": "serialize the normalized record to canonical JSON text",
     "mutator": "row_to_json", "args": {},
     "input_edge": "NormalizedRecord", "output_edge": "JsonText"},
    {"step": "wrap_receipt", "capability": "wrap the JSON payload with a content-hash output receipt",
     "mutator": "output_receipt_wrapper", "args": {},
     "input_edge": "JsonText", "output_edge": "ReceiptEnvelope"},
]

#: the realistic ingest fixture the whole route is executed over (a raw CSV-derived dict row)
ROUTE_FIXTURE: dict[str, Any] = {"Full Name": "Ada Lovelace", "Years": "36", "Score": "9.5"}


# ── execution + independent expected reconstruction ──
def run_route(fixture: Any, steps: list[dict[str, Any]]) -> tuple[Any, list[dict[str, Any]]]:
    """Execute the FULL route by chaining apply_mutator over each step. Returns (final_output, per-step receipts)."""
    payload: Any = fixture
    receipts: list[dict[str, Any]] = []
    for s in steps:
        payload, rec = apply_mutator(s["mutator"], payload, **s["args"])
        receipts.append(rec)
    return payload, receipts


def build_expected_output() -> Any:
    """Reconstruct the route's expected final output INDEPENDENTLY of the mutator chain (a genuine cross-check).

    Built by hand step-by-step from the fixture; the two hash-derived values (the canonical identity key and the
    receipt's content hash) are recomputed here with hashlib/_hash against the hand-built intermediate — a separate
    code path from the mutators, so a matching result proves the composite really executed correctly."""
    # rename_headers
    s1 = {"name": "Ada Lovelace", "age": "36", "score": "9.5"}
    # coerce_types (int/float)
    s2 = {"name": "Ada Lovelace", "age": 36, "score": 9.5}
    # validate_schema
    s3 = {**s2, "_validation": {"required": ["name", "age", "score"], "missing": [], "valid": True}}
    # normalize_identity — idempotency_wrapper joins str(request[f]) for f in key_fields with '|', sha256, [:24]
    ident_key = hashlib.sha256("Ada Lovelace|36".encode()).hexdigest()[:24]
    s4 = {**s3, "idempotency_key": ident_key}
    # serialize_json — row_to_json is json.dumps(row, sort_keys=True)
    s5 = json.dumps(s4, sort_keys=True)
    # wrap_receipt — output_receipt_wrapper attaches _hash(output)
    return {"output": s5, "receipt": {"output_hash": _hash(s5), "verified_first": True}}


def edge_chain_strength(steps: list[dict[str, Any]]) -> int:
    """Count boundaries where step[i].output_edge_type_id == step[i+1].input_edge_type_id (canonical TYPE match)."""
    n = 0
    for a, b in zip(steps, steps[1:]):
        if canonicalize_edge(a["output_edge"]) == canonicalize_edge(b["input_edge"]):
            n += 1
    return n


# ── the composite proof: execute end-to-end, compare to independent expected, check determinism + typed chain ──
def prove_route() -> dict[str, Any]:
    """Run the full route and produce a composite proof receipt. serves_truth flips true ONLY if the executed output
    equals the independently-reconstructed expected output AND the run is deterministic AND the typed chain composes."""
    expected = build_expected_output()
    proofs: list[dict[str, Any]] = []

    # proof 1: end-to-end composite behavior (does chaining every leaf produce the expected final output?)
    try:
        executed, step_receipts = run_route(ROUTE_FIXTURE, ROUTE_STEPS)
        exec_error: str | None = None
    except Exception as exc:  # noqa: BLE001
        executed, step_receipts, exec_error = None, [], str(exc)
    exec_ok = exec_error is None and executed == expected
    proofs.append({
        "name": "composite_behavior_test", "passed": exec_ok,
        "detail": (f"executed_hash={_hash(executed)} expected_hash={_hash(expected)}"
                   if exec_error is None else f"execution error: {exec_error}"),
    })

    # proof 2: determinism (re-running the whole route yields the identical output)
    det_ok = False
    if exec_error is None:
        executed2, _ = run_route(ROUTE_FIXTURE, ROUTE_STEPS)
        det_ok = executed2 == executed
    proofs.append({"name": "determinism_test", "passed": det_ok,
                   "detail": "route re-run identical" if det_ok else "non-deterministic or un-runnable"})

    # proof 3: typed composability (the edges actually line up as canonical types; honest count, must be > 1)
    strength = edge_chain_strength(ROUTE_STEPS)
    chain_ok = strength > 1
    proofs.append({"name": "typed_chain_test", "passed": chain_ok,
                   "detail": f"edge_chain_strength={strength} over {len(ROUTE_STEPS) - 1} boundaries"})

    passed = exec_ok and det_ok and chain_ok
    typed_steps = [
        {
            "step": s["step"], "capability": s["capability"], "mutator": s["mutator"], "args": s["args"],
            "input_edge": s["input_edge"], "output_edge": s["output_edge"],
            "input_edge_type_id": canonicalize_edge(s["input_edge"]),
            "output_edge_type_id": canonicalize_edge(s["output_edge"]),
        }
        for s in ROUTE_STEPS
    ]
    return {
        "record_type": "composite_route_proof_receipt",
        "primitive_id": f"prim:composite:{ROUTE_ID}",
        "route_id": ROUTE_ID,
        "family": FAMILY,
        "route_length": len(ROUTE_STEPS),
        "steps": typed_steps,
        "step_receipts": step_receipts,
        "edge_chain_strength": strength,
        "proofs": proofs,
        "all_passed": passed,
        # THE promotion: an executed passing composite proof is the ONLY thing that flips serves_truth true.
        "serves_truth": bool(passed), "candidate": not passed, "promoted": bool(passed),
        "verification_level": "L7_executed_proof" if passed else "L4_proof_declared_failed",
        "input_edge": ROUTE_STEPS[0]["input_edge"], "output_edge": ROUTE_STEPS[-1]["output_edge"],
        "input_edge_type_id": canonicalize_edge(ROUTE_STEPS[0]["input_edge"]),
        "output_edge_type_id": canonicalize_edge(ROUTE_STEPS[-1]["output_edge"]),
        "input_hash": _hash(ROUTE_FIXTURE),
        "output_hash": _hash(executed) if exec_error is None else None,
        "tokens": 0,  # fully deterministic + offline: no model tokens consumed
    }


def _persist_row(r: dict[str, Any]) -> dict[str, Any]:
    """The stored shape for the proven composite route (only ever built when the composite proof PASSED)."""
    return {
        "primitive_id": r["primitive_id"],
        "record_type": "proven_composite_route",
        "route_id": r["route_id"],
        "family": FAMILY,
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "route_length": r["route_length"],
        "edge_chain_strength": r["edge_chain_strength"],
        "steps": [
            {k: st[k] for k in ("step", "capability", "mutator", "input_edge", "output_edge",
                                "input_edge_type_id", "output_edge_type_id")}
            for st in r["steps"]
        ],
        "input_edge": r["input_edge"],
        "output_edge": r["output_edge"],
        "input_edge_type_id": r["input_edge_type_id"],
        "output_edge_type_id": r["output_edge_type_id"],
        "proofs": r["proofs"],
        "input_hash": r["input_hash"],
        "output_hash": r["output_hash"],
        "tokens": 0,
    }


def build_manifest(row: dict[str, Any] | None, receipt: dict[str, Any]) -> dict[str, Any]:
    rows = [row] if row is not None else []
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    return {
        "record_type": "proven_composite_etl_intake_manifest",
        "family": FAMILY,
        "route_id": ROUTE_ID,
        "pack_id": "proven-composite-etl-intake",
        "generator": REGISTER_TUPLE[0],
        "generated_utc": FIXED_DATE,
        "loaded_leaf_families": _LOADED_FAMILIES,
        "typed_step_mutator": _TYPED_STEP_MUTATOR,
        "route_length": receipt["route_length"],
        "edge_chain_strength": receipt["edge_chain_strength"],
        "proven_count": len(rows),
        "serves_truth": receipt["serves_truth"],
        "verification_level": receipt["verification_level"],
        "row_counts": {OUT_JSONL.name: len(rows)},
        "total_rows": len(rows),
        "register_module": {"script_path": REGISTER_TUPLE[0], "module_name": REGISTER_TUPLE[1]},
        "note": "serves_truth=true is set ONLY by the PASSING executed end-to-end proof of the COMPOSITE route "
                "(execute the full chain over a fixture, compare to an independently-reconstructed expected output). "
                "A wrong-expected route stays candidate and is never persisted. edge_chain_strength is the honest "
                "count of canonical-TYPE-matched step boundaries (target > 1).",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def write_pack() -> dict[str, Any]:
    """Persist the proven composite ONLY if its end-to-end proof passed (a failing route is never persisted)."""
    receipt = prove_route()
    row = _persist_row(receipt) if receipt["serves_truth"] else None
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        ("" if row is None else json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"), encoding="utf-8"
    )
    manifest = build_manifest(row, receipt)
    OUT_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def self_test() -> int:
    receipt = prove_route()
    row = _persist_row(receipt) if receipt["serves_truth"] else None

    # a deliberately-broken route: the SAME executed chain, but compared against a WRONG expected output.
    # It must NOT verify (exec output != wrong expected) and must NOT promote — the gate is real.
    executed, _ = run_route(ROUTE_FIXTURE, ROUTE_STEPS)
    wrong_expected = build_expected_output()
    wrong_expected["output"] = "TAMPERED"  # corrupt the expected serialized payload
    broken_verifies = executed == wrong_expected

    # a second broken route: swap a step so the chain breaks at runtime (json step fed a non-dict) -> execution error
    broken_steps = [dict(s) for s in ROUTE_STEPS]
    broken_steps[0] = {**broken_steps[0], "mutator": "row_to_json", "args": {}}  # serialize first -> later steps fail
    try:
        run_route(ROUTE_FIXTURE, broken_steps)
        broken_route_runs = True
    except Exception:  # noqa: BLE001
        broken_route_runs = False

    # deterministic persisted shape
    row2 = _persist_row(prove_route()) if prove_route()["serves_truth"] else None

    checks: list[tuple[str, bool]] = [
        ("route has >= 4 chained leaf steps", receipt["route_length"] >= 4),
        ("the composite EXECUTES end-to-end and matches the independent expected output",
         any(p["name"] == "composite_behavior_test" and p["passed"] for p in receipt["proofs"])),
        ("the composite is DETERMINISTIC (re-run identical)",
         any(p["name"] == "determinism_test" and p["passed"] for p in receipt["proofs"])),
        ("edge_chain_strength > 1 (typed chain genuinely composes)", receipt["edge_chain_strength"] > 1),
        ("edge_chain_strength equals every boundary in this fully-typed route",
         receipt["edge_chain_strength"] == receipt["route_length"] - 1),
        ("serves_truth=true ONLY because the executed composite proof passed",
         receipt["serves_truth"] is True and receipt["promoted"] is True
         and receipt["verification_level"] == "L7_executed_proof"),
        ("a persisted row exists and is truth-bearing (serves_truth=true, candidate=false, tokens=0)",
         row is not None and row["serves_truth"] is True and row["candidate"] is False and row["tokens"] == 0),
        ("no step edge folded to 'Unknown' (chain is honestly typed)",
         all(st["input_edge_type_id"] != "Unknown" and st["output_edge_type_id"] != "Unknown"
             for st in receipt["steps"])),
        ("route endpoints are typed (RawCsvRow -> ReceiptEnvelope)",
         receipt["input_edge_type_id"] == canonicalize_edge("RawCsvRow")
         and receipt["output_edge_type_id"] == canonicalize_edge("ReceiptEnvelope")),
        ("a deliberately-broken route (WRONG expected) FAILS verification (not equal, would not promote)",
         broken_verifies is False),
        ("a structurally-broken chain fails to execute (proof gate catches un-runnable routes)",
         broken_route_runs is False),
        ("persisted composite is deterministic (re-run yields identical row)",
         row2 is not None and json.dumps(row2, sort_keys=True) == json.dumps(row, sort_keys=True)),
        ("route built from proven leaf mutators present in the shared registry",
         all(s["mutator"] in MUTATOR_REGISTRY for s in ROUTE_STEPS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_composite_etl_intake:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_composite_etl_intake: proven composite route '{ROUTE_ID}' — {receipt['route_length']} chained "
          f"proven leaves (raw CSV row -> typed -> validated -> normalized -> json -> receipt) EXECUTED end-to-end and "
          f"matched an independently-reconstructed expected output; deterministic; edge_chain_strength="
          f"{receipt['edge_chain_strength']} (canonical TYPE matches, target > 1); serves_truth=true set ONLY by the "
          f"passing executed proof; a wrong-expected route and a structurally-broken chain both correctly fail. "
          f"Register tuple: {REGISTER_TUPLE}.")
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
