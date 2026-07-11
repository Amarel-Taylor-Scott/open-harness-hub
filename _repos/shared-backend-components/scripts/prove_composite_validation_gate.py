#!/usr/bin/env python3
"""scripts.prove_composite_validation_gate — a PROVEN multi-step COMPOSITE route 'validation_gate' built by CHAINING
already-proven leaf primitives (never a re-implementation).

A single proven leaf is a capability; the product is the COMPOSITE — a governance gate that walks a record batch
through: schema-required check -> in-range check -> enum check -> combine per-record validity -> partition pass/fail
-> extract failure count -> aggregate final verdict. Every stage is executed by `apply_mutator` over PROVEN leaf
mutators imported from the shared registry (vp_schema_required · vp_in_range · vp_enum_member · agg_all_true ·
agg_group_count · dm_merge_defaults · dm_deep_get · vp_max), so the composite is genuinely composed of proven leaves,
not new hand-written logic.

Repo law kept, exactly: `serves_truth=true` is set ONLY by a PASSING executed end-to-end proof (executed_output ==
expected_output AND determinism) — never hand-set; a route with a wrong expected_output stays candidate and is NOT
persisted (this gate is the whole point). ADD-ONLY: this is a NEW file that IMPORTS the shared machinery and the
sibling leaf-family provers (which self-register their mutators on import); it edits NO contract-locked or shared
file, and does NOT register itself in flywheel_proof_modules.py (the register tuple is REPORTED instead). The
composability metric is honest: `edge_chain_strength` = count of adjacent steps whose canonical TYPES line up
(canonicalize_edge(step[i].output_edge) == canonicalize_edge(step[i+1].input_edge)) — it counts real type continuity,
not a claim. Deterministic + offline ONLY: no network, no LLM, no wall-clock (fixed literal timestamp), no RNG.

CLI: --self-test | --write [--date D].
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

# IMPORT the shared machinery — never edit it (ADD-ONLY / flexible-multi-path).
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402
from scripts.mutator_registry import MUTATOR_REGISTRY, _hash, apply_mutator  # noqa: E402

# Import the sibling leaf-family provers so they REGISTER their proven mutators into the shared MUTATOR_REGISTRY on
# import. try/except per family: a missing sibling must never hard-crash this module — we degrade to whatever proven
# mutators are present (base 11 at minimum) so --self-test still runs standalone.
_FAMILY_MODULES = (
    "scripts.prove_leaves_validation_predicate",
    "scripts.prove_leaves_aggregation_reduce",
    "scripts.prove_leaves_dict_mapping",
)
_FAMILIES_LOADED: list[str] = []
for _mod in _FAMILY_MODULES:
    try:
        __import__(_mod)
        _FAMILIES_LOADED.append(_mod)
    except Exception:  # noqa: BLE001 — degrade gracefully to base-11 registry
        pass

FAMILY = "composite_route"
COMPOSITE_ID = "prim:composite:validation_gate"
#: fixed literal timestamp — NEVER wall-clock (repo law: deterministic + offline).
_FIXED_UTC = "2026-07-03"

OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_composite_validation_gate.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_composite_validation_gate.json"

# ── the governance-gate policy (a real config, single-sourced here) ──
GATE_SCHEMA: dict[str, str] = {"id": "str", "score": "int", "status": "str"}
SCORE_LO, SCORE_HI = 0, 10
STATUS_CHOICES: list[str] = ["active", "pending", "closed"]

#: which proven leaf mutators the FULL route needs (present once the families import cleanly)
_REQUIRED_FULL = (
    "vp_schema_required", "vp_in_range", "vp_enum_member",
    "agg_all_true", "agg_group_count", "dm_merge_defaults", "dm_deep_get", "vp_max",
)


def _full_route_available() -> bool:
    return all(name in MUTATOR_REGISTRY for name in _REQUIRED_FULL)


# ── realistic fixtures ──
#: a MIXED batch — two clean records, one out-of-range score, one disallowed status (the gate must REJECT it).
FIXTURE_BATCH: list[dict[str, Any]] = [
    {"id": "r1", "score": 7, "status": "active"},   # schema ok · range ok · enum ok  -> pass
    {"id": "r2", "score": 3, "status": "pending"},  # schema ok · range ok · enum ok  -> pass
    {"id": "r3", "score": 12, "status": "active"},  # score 12 > 10                    -> fail (range)
    {"id": "r4", "score": 5, "status": "archived"}, # 'archived' not in choices        -> fail (enum)
]
#: a CLEAN batch — every record passes (the gate must ACCEPT it). Used by --self-test.
FIXTURE_BATCH_CLEAN: list[dict[str, Any]] = [
    {"id": "r1", "score": 7, "status": "active"},
    {"id": "r2", "score": 3, "status": "pending"},
]

# ── the ROUTE definition (declared steps + their canonical edge types). The executor walks exactly these steps. ──
# fields: id · name · kind(map=per-record / reduce=whole-batch) · mutator(s) · input_edge · output_edge · note
ROUTE_STEPS: list[dict[str, Any]] = [
    {"id": "schema_gate", "name": "schema-required check", "kind": "map", "mutator": "vp_schema_required",
     "input_edge": "RecordBatch", "output_edge": "RecordBatch",
     "note": "annotate each record with a schema-required verdict (required fields + types present)"},
    {"id": "range_check", "name": "in-range check", "kind": "map", "mutator": "vp_in_range",
     "input_edge": "RecordBatch", "output_edge": "RecordBatch",
     "note": "annotate each record with an in-range verdict over 'score'"},
    {"id": "enum_check", "name": "enum-member check", "kind": "map", "mutator": "vp_enum_member",
     "input_edge": "RecordBatch", "output_edge": "RecordBatch",
     "note": "annotate each record with an enum-member verdict over 'status'"},
    {"id": "combine_validity", "name": "combine per-record validity", "kind": "map", "mutator": "agg_all_true",
     "input_edge": "RecordBatch", "output_edge": "RecordBatch",
     "note": "logical-AND each record's three verdicts into a pass/fail label"},
    {"id": "partition_tally", "name": "partition pass/fail", "kind": "reduce", "mutator": "agg_group_count",
     "input_edge": "RecordBatch", "output_edge": "GroupTally",
     "note": "group the batch by pass/fail label -> a partition tally"},
    {"id": "ensure_defaults", "name": "normalize the tally", "kind": "reduce", "mutator": "dm_merge_defaults",
     "input_edge": "GroupTally", "output_edge": "GroupTally",
     "note": "fill absent 'pass'/'fail' buckets with 0 so the tally is total"},
    {"id": "extract_fail", "name": "extract failure count", "kind": "reduce", "mutator": "dm_deep_get",
     "input_edge": "GroupTally", "output_edge": "Number",
     "note": "read the 'fail' bucket count out of the tally"},
    {"id": "final_verdict", "name": "aggregate final verdict", "kind": "reduce", "mutator": "vp_max",
     "input_edge": "Number", "output_edge": "GateVerdict",
     "note": "the batch passes the gate iff failure_count <= 0"},
]


def _canonical_route() -> list[dict[str, Any]]:
    """The route, each step typed with canonical edge type ids (so the composite can itself chain)."""
    out: list[dict[str, Any]] = []
    for s in ROUTE_STEPS:
        out.append({
            **s,
            "input_edge_type_id": canonicalize_edge(s["input_edge"]),
            "output_edge_type_id": canonicalize_edge(s["output_edge"]),
        })
    return out


def edge_chain_strength(route: list[dict[str, Any]]) -> int:
    """The HONEST composability metric: count adjacent steps whose canonical TYPES line up
    (step[i].output_edge_type_id == step[i+1].input_edge_type_id via canonicalize_edge)."""
    return sum(
        1 for i in range(len(route) - 1)
        if route[i]["output_edge_type_id"] == route[i + 1]["input_edge_type_id"]
    )


# ── the EXECUTOR: walk the route end-to-end, every stage driven by apply_mutator over PROVEN leaves ──
def run_route(batch: list[dict[str, Any]], *, schema: dict[str, str] = GATE_SCHEMA,
              lo: int = SCORE_LO, hi: int = SCORE_HI,
              choices: list[str] | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Execute the validation-gate route by CHAINING apply_mutator across proven leaf mutators.

    Returns (final_gate_verdict, trace) where trace records each executed step's mutator, declared edges, canonical
    edge type ids, and the content hash of its output (lineage — nothing is discarded).
    """
    choices = STATUS_CHOICES if choices is None else choices
    route = _canonical_route()
    trace: list[dict[str, Any]] = []
    payload: Any = batch

    def _record(step: dict[str, Any], out: Any) -> None:
        trace.append({
            "step": step["id"], "name": step["name"], "kind": step["kind"], "mutator": step["mutator"],
            "input_edge": step["input_edge"], "output_edge": step["output_edge"],
            "input_edge_type_id": step["input_edge_type_id"], "output_edge_type_id": step["output_edge_type_id"],
            "output_hash": _hash(out),
        })

    # step 1 — schema_gate (per record): apply_mutator(vp_schema_required)
    step = route[0]
    annotated: list[dict[str, Any]] = []
    for rec in payload:
        verdict, _ = apply_mutator("vp_schema_required", rec, schema=schema)
        annotated.append({**rec, "_schema_valid": bool(verdict["valid"])})
    payload = annotated
    _record(step, payload)

    # step 2 — range_check (per record): apply_mutator(vp_in_range) over 'score'
    step = route[1]
    annotated = []
    for rec in payload:
        verdict, _ = apply_mutator("vp_in_range", rec["score"], lo=lo, hi=hi)
        annotated.append({**rec, "_range_valid": bool(verdict["valid"])})
    payload = annotated
    _record(step, payload)

    # step 3 — enum_check (per record): apply_mutator(vp_enum_member) over 'status'
    step = route[2]
    annotated = []
    for rec in payload:
        verdict, _ = apply_mutator("vp_enum_member", rec["status"], choices=choices)
        annotated.append({**rec, "_enum_valid": bool(verdict["valid"])})
    payload = annotated
    _record(step, payload)

    # step 4 — combine_validity (per record): apply_mutator(agg_all_true) over the three verdicts -> pass/fail label
    step = route[3]
    annotated = []
    for rec in payload:
        mini_batch = [{"v": rec["_schema_valid"]}, {"v": rec["_range_valid"]}, {"v": rec["_enum_valid"]}]
        all_valid, _ = apply_mutator("agg_all_true", mini_batch, field="v")
        annotated.append({**rec, "_gate_status": "pass" if all_valid else "fail"})
    payload = annotated
    _record(step, payload)

    # step 5 — partition_tally (reduce): apply_mutator(agg_group_count) by the pass/fail label
    step = route[4]
    tally, _ = apply_mutator("agg_group_count", payload, key="_gate_status")
    payload = tally
    _record(step, payload)

    # step 6 — ensure_defaults (reduce): apply_mutator(dm_merge_defaults) so both buckets exist
    step = route[5]
    payload, _ = apply_mutator("dm_merge_defaults", payload, defaults={"pass": 0, "fail": 0})
    _record(step, payload)

    # step 7 — extract_fail (reduce): apply_mutator(dm_deep_get) -> the failure count
    step = route[6]
    payload, _ = apply_mutator("dm_deep_get", payload, path="fail", default=0)
    _record(step, payload)

    # step 8 — final_verdict (reduce): apply_mutator(vp_max) -> batch passes iff failure_count <= 0
    step = route[7]
    payload, _ = apply_mutator("vp_max", payload, maximum=0)
    _record(step, payload)

    return payload, trace


# ── expected outputs (computed here as literals so the proof is a REAL correctness check, not a tautology) ──
#: the MIXED batch has 2 failures -> vp_max(2, maximum=0) verdict is INVALID (the gate correctly REJECTS the batch).
EXPECTED_MIXED: dict[str, Any] = {"check": "max", "valid": False, "value": 2, "maximum": 0}
#: the CLEAN batch has 0 failures -> vp_max(0, maximum=0) verdict is VALID (the gate ACCEPTS the batch).
EXPECTED_CLEAN: dict[str, Any] = {"check": "max", "valid": True, "value": 0, "maximum": 0}


def prove_composite(batch: list[dict[str, Any]], expected: dict[str, Any]) -> dict[str, Any]:
    """Execute the FULL route end-to-end and PROVE it: executed_output == expected_output AND determinism.

    serves_truth flips false->true ONLY when every sub-proof passes (repo law). A wrong `expected` -> exec_pass False
    -> stays candidate, never promoted.
    """
    route = _canonical_route()
    strength = edge_chain_strength(route)
    proofs: list[dict[str, Any]] = []

    try:
        out1, trace1 = run_route(batch)
    except Exception as exc:  # noqa: BLE001
        return {
            "record_type": "composite_proof_receipt", "composite_id": COMPOSITE_ID, "serves_truth": False,
            "candidate": True, "promoted": False, "route_length": len(route), "edge_chain_strength": strength,
            "proofs": [{"name": "execution", "passed": False, "error": str(exc)}], "tokens": 0,
        }

    # proof 1: end-to-end correctness of the COMPOSITE (executed final verdict == expected)
    exec_ok = out1 == expected
    proofs.append({"name": "composite_end_to_end", "passed": exec_ok,
                   "detail": f"output_hash={_hash(out1)} expected_hash={_hash(expected)}"})

    # proof 2: determinism (re-run yields identical final output AND identical step trace)
    out2, trace2 = run_route(batch)
    det_ok = (out2 == out1) and (
        [t["output_hash"] for t in trace2] == [t["output_hash"] for t in trace1])
    proofs.append({"name": "determinism", "passed": det_ok,
                   "detail": "re-run identical (final + full step trace)" if det_ok else "non-deterministic!"})

    # proof 3: real composability — canonical edge types line up across adjacent steps (target > 1)
    chain_ok = strength > 1
    proofs.append({"name": "edge_chain_strength_gt_1", "passed": chain_ok,
                   "detail": f"edge_chain_strength={strength} over {len(route)} steps"})

    passed = exec_ok and det_ok and chain_ok
    return {
        "record_type": "composite_proof_receipt", "composite_id": COMPOSITE_ID, "family": FAMILY,
        "capability": "governance validation gate over a record batch (schema -> range -> enum -> partition -> verdict)",
        "route": trace1, "route_length": len(route), "edge_chain_strength": strength,
        "proofs": proofs, "all_passed": passed,
        # THE promotion: an executed passing end-to-end proof is the ONLY thing that flips serves_truth true.
        "serves_truth": bool(passed), "candidate": not passed, "promoted": bool(passed),
        "verification_level": "L7_executed_composite_proof" if passed else "L4_composite_proof_failed",
        "input_hash": _hash(batch), "output_hash": _hash(out1), "tokens": 0,
        "families_loaded": list(_FAMILIES_LOADED),
    }


def _persist_row(r: dict[str, Any]) -> dict[str, Any]:
    """The workable persisted composite row (route steps + edges + proofs for lineage). serves_truth=true here is
    CORRECT — it is only ever reached from a receipt whose executed end-to-end proof PASSED."""
    return {
        "record_type": "proven_composite_route",
        "composite_id": r["composite_id"],
        "family": FAMILY,
        "capability": r["capability"],
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_composite_proof",
        "route_length": r["route_length"],
        "edge_chain_strength": r["edge_chain_strength"],
        "route": r["route"],
        "proofs": r["proofs"],
        "input_hash": r["input_hash"],
        "output_hash": r["output_hash"],
        "tokens": 0,
        "generated_utc": _FIXED_UTC,
    }


def build_manifest(row: dict[str, Any] | None) -> dict[str, Any]:
    import hashlib
    rows = [row] if row else []
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    return {
        "record_type": "proven_composite_validation_gate_manifest",
        "pack_id": "proven-composite-validation-gate", "family": FAMILY,
        "generator": "scripts/prove_composite_validation_gate.py",
        "generated_utc": _FIXED_UTC,
        "composite_ids": sorted(r["composite_id"] for r in rows),
        "proven_count": len(rows),
        "route_length": row["route_length"] if row else 0,
        "edge_chain_strength": row["edge_chain_strength"] if row else 0,
        "verification_level": "L7_executed_composite_proof",
        "row_counts": {OUT_JSONL.name: len(rows)},
        "total_rows": len(rows),
        "note": "serves_truth=true is set ONLY by a PASSING executed end-to-end composite proof (prove_composite): "
                "the full route is chained via apply_mutator over PROVEN leaf mutators and the final gate verdict is "
                "asserted equal to a literal expected. A route with a wrong expected stays candidate and is NEVER "
                "persisted. edge_chain_strength counts adjacent steps whose canonical edge TYPES line up.",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def write_pack() -> dict[str, Any]:
    receipt = prove_composite(FIXTURE_BATCH, EXPECTED_MIXED)
    row = _persist_row(receipt) if receipt["serves_truth"] is True else None
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # ONLY persist a proven composite (serves_truth=true). If the proof failed, persist nothing (empty pack).
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in ([row] if row else [])),
        encoding="utf-8")
    manifest = build_manifest(row)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    route = _canonical_route()
    strength = edge_chain_strength(route)

    # PRIMARY proof: the mixed batch (2 violations) -> the composite correctly produces an INVALID gate verdict.
    receipt = prove_composite(FIXTURE_BATCH, EXPECTED_MIXED)
    # SECONDARY proof: a clean batch (0 violations) -> the composite correctly produces a VALID gate verdict.
    clean_out, _ = run_route(FIXTURE_BATCH_CLEAN)
    # NEGATIVE proof: a deliberately-broken route (wrong expected) MUST fail and stay candidate (the gate is real).
    broken_expected = {"check": "max", "valid": True, "value": 0, "maximum": 0}  # wrong for the mixed batch
    broken = prove_composite(FIXTURE_BATCH, broken_expected)

    full = _full_route_available()

    checks: list[tuple[str, bool]] = [
        ("the full route needs proven leaves that are present (families self-registered on import)", full),
        ("route has multiple steps (a real composite, not a single leaf)", len(route) >= 5),
        ("edge_chain_strength > 1 (adjacent canonical edge TYPES line up)", strength > 1),
        ("mixed-batch composite proof PASSED end-to-end (executed == expected)",
         receipt["proofs"][0]["passed"] is True),
        ("mixed-batch composite is PROMOTED: serves_truth=true ONLY via the passing executed proof",
         receipt["serves_truth"] is True and receipt["promoted"] is True
         and receipt["verification_level"] == "L7_executed_composite_proof"),
        ("every sub-proof (end-to-end + determinism + chain) passed", all(p["passed"] for p in receipt["proofs"])),
        ("the persisted composite carries edge_chain_strength == the measured value",
         _persist_row(receipt)["edge_chain_strength"] == strength),
        ("determinism: re-running the route yields an identical final verdict",
         run_route(FIXTURE_BATCH)[0] == run_route(FIXTURE_BATCH)[0]),
        ("the gate correctly REJECTS the mixed batch (final verdict invalid)", receipt["output_hash"] == _hash(EXPECTED_MIXED)),
        ("the gate correctly ACCEPTS the clean batch (final verdict valid)", clean_out == EXPECTED_CLEAN),
        ("a deliberately-broken route (wrong expected) FAILS and stays CANDIDATE (never promoted)",
         broken["serves_truth"] is False and broken["promoted"] is False and broken["proofs"][0]["passed"] is False),
        ("every route step is typed with non-null canonical edge type ids",
         all(s["input_edge_type_id"] and s["output_edge_type_id"] for s in route)),
        ("the whole route is chained via apply_mutator over the shared MUTATOR_REGISTRY",
         all(s["mutator"] in MUTATOR_REGISTRY for s in route)),
        ("composite tokens == 0 (deterministic + offline, no LLM)", receipt["tokens"] == 0),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_composite_validation_gate:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_composite_validation_gate: composite route 'validation_gate' PROVEN end-to-end — "
          f"{len(route)} steps chained via apply_mutator over PROVEN leaf mutators "
          f"(schema -> range -> enum -> combine -> partition -> extract -> verdict), edge_chain_strength={strength} "
          f"(>1, adjacent canonical edge types line up), executed_output == expected_output on a mixed batch (gate "
          f"REJECTS) and a clean batch (gate ACCEPTS), deterministic, tokens=0. serves_truth=true set ONLY by the "
          f"passing executed proof; a wrong-expected route correctly stays candidate.")
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
