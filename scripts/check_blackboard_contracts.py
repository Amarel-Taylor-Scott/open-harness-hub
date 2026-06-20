#!/usr/bin/env python3
"""scripts.check_blackboard_contracts — PROOF: the P0 CONTRACTS for the GOVERNED blackboard spine are real.

The blackboard is durable, typed analytical STATE for stateful swarms: bounded workers post signals,
observations, gaps, calculations, analyses and a synthesis across iterations onto one shared, tenant-scoped
workspace. Teleon RUNS the blackboard as a runtime substrate; Baltor GOVERNS what (if anything) becomes
served truth. Load-bearing law, encoded in the schemas as const/enum constraints:

  - blackboard/swarm output is NEVER served truth (serves_truth pinned const false on the entry envelope and
    on Analysis / Synthesis / the Baltor governance wrapper);
  - every claim carries PROVENANCE (an observation's source_refs is required + non-empty; sources are stable
    ctx:// / doc#section handles; receipts attest worker turns by hash);
  - held-out items stay SEPARATE (Synthesis.held_out preserves minority/rejected items; compression may never
    drop them);
  - benchmark != promotion, candidate != active (ConvergenceReport is an operational verdict; promotion is a
    separate, explicitly gated Baltor decision via GovernedBlackboardEntry.promotion_eligible).

Asserts:
  A. SCHEMAS EXIST + WELL-FORMED: all 13 blackboard contracts are valid JSON and each carries $id (matching its
     filename: blackboard/<Name>.v1), title, type:object, properties, required, additionalProperties:false (+description).
  B. OUTPUT != TRUTH: serves_truth pinned const false on BlackboardEntry, BlackboardAnalysis, BlackboardSynthesis,
     and GovernedBlackboardEntry. A swarm entry / analysis / synthesis / governed wrapper can never be served truth.
  C. PROVENANCE REQUIRED: BlackboardObservation.source_refs is required AND non-empty (minItems >= 1); a sourceless
     observation is rejected. BlackboardSourceRef.handle is a ctx:// or doc#section handle (pattern), never free text.
  D. HELD-OUT SEPARATE: BlackboardSynthesis carries both held_out and source_handles (winner keeps lineage to losers
     and to upstream provenance).
  E. BALTOR GOVERNANCE: GovernedBlackboardEntry.claim_status enum includes candidate + verified + conflicting +
     held_out + stale, and promotion_eligible exists (the explicit, auditable promotion gate).
  F. COMPRESSION PRESERVES HANDLES: BlackboardCompressionReport pins source_handles_preserved AND held_out_preserved
     to const true — compression never drops provenance handles or held-out items.
  G. REGISTERED: all 13 contracts are registered in architecture/contract_registry.json with the matching schema path.
  H. FIXTURES VALIDATE: a tiny in-proof fixture for each of the 13 satisfies required-field presence + declared
     top-level types + const/enum constraints, checked by a minimal stdlib validator (no jsonschema dependency).
  I. NEGATIVE CONTROLS: flipping serves_truth to True (on an entry) OR dropping the lone source_ref from an
     Observation (emptying a required non-empty array) is REJECTED by the validator (proves the constraints bite).

Deterministic + offline. stdlib only. Exit 0/1. No raw keys/secrets.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_SCHEMA_DIR = _REPO / "schemas" / "blackboard"

# The 13 P0 contracts of the governed blackboard spine, in load order.
_CONTRACTS = [
    "Blackboard",
    "BlackboardEntry",
    "BlackboardSignal",
    "BlackboardObservation",
    "BlackboardGap",
    "BlackboardCalculation",
    "BlackboardAnalysis",
    "BlackboardSynthesis",
    "BlackboardSourceRef",
    "BlackboardWorkerReceipt",
    "BlackboardConvergenceReport",
    "BlackboardCompressionReport",
    "GovernedBlackboardEntry",
]

# Entries whose serves_truth flag must be pinned const false (output != truth).
_SERVES_TRUTH_FALSE = [
    "BlackboardEntry",
    "BlackboardAnalysis",
    "BlackboardSynthesis",
    "GovernedBlackboardEntry",
]

# JSON-Schema "type" -> Python types, for the minimal stdlib validator.
_JSON_TYPE_TO_PY = {
    "object": (dict,),
    "array": (list,),
    "string": (str,),
    # NOTE: bool is a subclass of int in Python; "integer"/"number" special-case below to exclude bools.
    "integer": (int,),
    "number": (int, float),
    "boolean": (bool,),
    "null": (type(None),),
}


def _py_type_ok(value, json_type: str) -> bool:
    """Minimal type check for one JSON-Schema scalar/compound type (no jsonschema dependency)."""
    if json_type in ("integer", "number") and isinstance(value, bool):
        return False  # a bool is not a number for our purposes
    return isinstance(value, _JSON_TYPE_TO_PY.get(json_type, ()))


def _validate_minimal(instance: dict, schema: dict) -> list[str]:
    """A tiny required-keys + top-level type + const/enum/minItems validator. Returns human-readable problems.

    Intentionally NOT a full JSON-Schema engine — just enough to prove the fixtures satisfy each contract's
    required fields, that each present typed property matches its declared `type` (handling the `[a, b]` union),
    that `const`/`enum` constraints hold, and that a `minItems` on an array is enforced (so the
    provenance-required Observation bites when its source_refs is emptied).
    """
    problems: list[str] = []
    if not isinstance(instance, dict):
        return ["instance is not an object"]

    for key in schema.get("required", []):
        if key not in instance:
            problems.append(f"missing required key: {key}")

    props = schema.get("properties", {})
    if schema.get("additionalProperties") is False:
        for key in instance:
            if key not in props:
                problems.append(f"additionalProperties:false but extra key present: {key}")

    for key, value in instance.items():
        spec = props.get(key)
        if not isinstance(spec, dict):
            continue
        declared = spec.get("type")
        if declared is not None:
            types = declared if isinstance(declared, list) else [declared]
            if not any(_py_type_ok(value, t) for t in types):
                problems.append(f"key {key}: value {value!r} not of type {declared}")
        if "const" in spec and value != spec["const"]:
            problems.append(f"key {key}: value {value!r} != const {spec['const']!r}")
        if "enum" in spec and value not in spec["enum"]:
            problems.append(f"key {key}: value {value!r} not in enum {spec['enum']}")
        if "minItems" in spec and isinstance(value, list) and len(value) < spec["minItems"]:
            problems.append(f"key {key}: array len {len(value)} < minItems {spec['minItems']}")
    return problems


def _fixtures() -> dict[str, dict]:
    """A tiny, valid in-proof FIXTURE for each of the 13 contracts (required fields present, correct types,
    governance flags pinned correctly). These are evidence the contracts are instantiable — none is served truth."""
    return {
        "Blackboard": {
            "blackboard_id": "bb-0001",
            "task": "Determine the effective date and scope of sanction X",
            "tenant_scope": "tenant-demo",
            "created_at": "2026-01-01T00:00:00Z",
            "status": "open",
            "entry_count": 6,
            "iteration": 2,
        },
        "BlackboardEntry": {
            "entry_id": "e-0001",
            "blackboard_id": "bb-0001",
            "kind": "observation",
            "author_worker_id": "w.observer",
            "iteration": 1,
            "source_refs": ["src-0001"],
            "serves_truth": False,
            "created_at": "2026-01-01T00:00:01Z",
        },
        "BlackboardSignal": {
            "entry_id": "e-sig-0001",
            "blackboard_id": "bb-0001",
            "question": "What is the sanction's effective date?",
            "priority": 10,
        },
        "BlackboardObservation": {
            "entry_id": "e-0001",
            "blackboard_id": "bb-0001",
            "statement": "The sanction took effect on 2026-01-15 per the official register.",
            "source_refs": ["src-0001"],
            "confidence": 0.92,
        },
        "BlackboardGap": {
            "entry_id": "e-gap-0001",
            "blackboard_id": "bb-0001",
            "missing": "The list of named entities under the sanction.",
            "why_it_matters": "Scope cannot be computed without the entity list.",
            "status": "open",
        },
        "BlackboardCalculation": {
            "entry_id": "e-calc-0001",
            "blackboard_id": "bb-0001",
            "formula": "sum(exposure_i for i in named_entities)",
            "inputs": ["e-0001", "e-0002"],
            "result": "12450000",
            "checked": True,
        },
        "BlackboardAnalysis": {
            "entry_id": "e-an-0001",
            "blackboard_id": "bb-0001",
            "claim": "Total exposure exceeds the reporting threshold.",
            "supporting_entry_ids": ["e-calc-0001", "e-0001"],
            "serves_truth": False,
        },
        "BlackboardSynthesis": {
            "entry_id": "e-syn-0001",
            "blackboard_id": "bb-0001",
            "answer": "Sanction X is effective 2026-01-15; exposure exceeds the threshold (candidate answer).",
            "supporting_entry_ids": ["e-an-0001", "e-0001"],
            "held_out": ["e-0007-minority-reading"],
            "source_handles": ["ctx://tenant/tenant-demo/source/sid#record/r1", "doc#register.section-3"],
            "serves_truth": False,
        },
        "BlackboardSourceRef": {
            "source_id": "src-0001",
            "handle": "ctx://tenant/tenant-demo/source/sid#record/r1",
            "authority_rank": 90,
            "retrieved_at": "2026-01-01T00:00:00Z",
        },
        "BlackboardWorkerReceipt": {
            "receipt_id": "rcpt-0001",
            "blackboard_id": "bb-0001",
            "worker_id": "w.observer",
            "worker_kind": "observer",
            "entries_written": ["e-0001"],
            "input_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "output_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
            "llm_route_receipt_ref": "env://OPENHARNESS_LLM_ROUTE_RECEIPT",
            "started_at": "2026-01-01T00:00:00Z",
            "completed_at": "2026-01-01T00:00:01Z",
        },
        "BlackboardConvergenceReport": {
            "blackboard_id": "bb-0001",
            "iterations": 3,
            "open_gaps": 0,
            "closed_gaps": 4,
            "converged": True,
            "reason": "converged",
        },
        "BlackboardCompressionReport": {
            "blackboard_id": "bb-0001",
            "entries_before": 42,
            "entries_after": 9,
            "source_handles_preserved": True,
            "held_out_preserved": True,
            "fidelity_note": "Merged duplicate observations; kept all source handles + held-out minority readings; raw entries rehydratable.",
        },
        "GovernedBlackboardEntry": {
            "entry_id": "e-syn-0001",
            "blackboard_id": "bb-0001",
            "authority_rank": 90,
            "claim_status": "candidate",
            "verification_status": "needs_review",
            "held_out_reason": "",
            "freshness_policy": "recheck_on_register_update",
            "temporal_validity": "2026-01-15/..",
            "tenant_scope": "tenant-demo",
            "promotion_eligible": False,
            "receipt_refs": ["rcpt-0001"],
            "source_handles": ["ctx://tenant/tenant-demo/source/sid#record/r1"],
            "serves_truth": False,
        },
    }


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    # ---- A. schemas exist + well-formed -------------------------------------------------
    schemas: dict[str, dict] = {}
    for name in _CONTRACTS:
        path = _SCHEMA_DIR / f"{name}.v1.schema.json"
        if not path.exists():
            check(f"A: schema file exists: {name}", False, str(path))
            continue
        try:
            schemas[name] = json.loads(path.read_text())
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            check(f"A: schema is valid JSON: {name}", False, str(exc))

    check("A: all 13 blackboard schema files present + valid JSON", len(schemas) == len(_CONTRACTS),
          f"loaded {sorted(schemas)}")

    for name, schema in schemas.items():
        keys_ok = all(k in schema for k in ("$id", "title", "type", "properties", "required", "additionalProperties"))
        shape_ok = (
            schema.get("$id") == f"blackboard/{name}.v1"
            and schema.get("title") == f"{name}.v1"
            and schema.get("type") == "object"
            and schema.get("additionalProperties") is False
            and isinstance(schema.get("properties"), dict)
            and isinstance(schema.get("required"), list)
            and isinstance(schema.get("description"), str) and schema.get("description")
        )
        check(f"A: {name} has $id/title/type/properties/required/additionalProperties:false (+description)",
              keys_ok and shape_ok,
              json.dumps({k: schema.get(k) for k in ("$id", "title", "type", "additionalProperties")}))

    # ---- B. output != truth (serves_truth pinned const false) ---------------------------
    for name in _SERVES_TRUTH_FALSE:
        if name in schemas:
            const = schemas[name]["properties"].get("serves_truth", {}).get("const")
            check(f"B: {name}.serves_truth pinned const false (swarm/blackboard output is never served truth)",
                  const is False, repr(const))

    # ---- C. provenance required (observation source_refs + source handle form) ----------
    if "BlackboardObservation" in schemas:
        obs = schemas["BlackboardObservation"]
        sr = obs["properties"].get("source_refs", {})
        check("C: BlackboardObservation.source_refs is REQUIRED",
              "source_refs" in obs.get("required", []))
        check("C: BlackboardObservation.source_refs is non-empty (minItems >= 1) — sourceless observation rejected",
              isinstance(sr.get("minItems"), int) and sr.get("minItems") >= 1, repr(sr.get("minItems")))
    if "BlackboardSourceRef" in schemas:
        handle = schemas["BlackboardSourceRef"]["properties"].get("handle", {})
        pat = handle.get("pattern", "")
        check("C: BlackboardSourceRef.handle constrained to a ctx:// or doc# handle (not free text)",
              "ctx://" in pat and "doc#" in pat, repr(pat))

    # ---- D. held-out stays separate (synthesis keeps held_out + source_handles) ---------
    if "BlackboardSynthesis" in schemas:
        syn_props = schemas["BlackboardSynthesis"]["properties"]
        syn_req = schemas["BlackboardSynthesis"].get("required", [])
        check("D: BlackboardSynthesis has held_out (winner keeps lineage to losers)",
              "held_out" in syn_props and "held_out" in syn_req)
        check("D: BlackboardSynthesis has source_handles (answer keeps upstream provenance)",
              "source_handles" in syn_props and "source_handles" in syn_req)

    # ---- E. Baltor governance (claim_status enum + promotion gate) ----------------------
    if "GovernedBlackboardEntry" in schemas:
        gov = schemas["GovernedBlackboardEntry"]["properties"]
        enum = gov.get("claim_status", {}).get("enum", [])
        needed = {"candidate", "verified", "conflicting", "held_out", "stale"}
        check("E: GovernedBlackboardEntry.claim_status enum includes candidate/verified/conflicting/held_out/stale",
              needed.issubset(set(enum)), str(enum))
        check("E: GovernedBlackboardEntry.promotion_eligible exists (the explicit, auditable promotion gate)",
              "promotion_eligible" in gov
              and "promotion_eligible" in schemas["GovernedBlackboardEntry"].get("required", []))

    # ---- F. compression preserves handles + held-out (const true) -----------------------
    if "BlackboardCompressionReport" in schemas:
        comp = schemas["BlackboardCompressionReport"]["properties"]
        check("F: BlackboardCompressionReport.source_handles_preserved pinned const true (compression keeps handles)",
              comp.get("source_handles_preserved", {}).get("const") is True)
        check("F: BlackboardCompressionReport.held_out_preserved pinned const true (compression keeps held-out items)",
              comp.get("held_out_preserved", {}).get("const") is True)

    # ---- G. registered in the contract registry ----------------------------------------
    registry = json.loads((_REPO / "architecture" / "contract_registry.json").read_text())
    registry_blob = json.dumps(registry)
    for name in _CONTRACTS:
        check(f"G: {name}.v1 registered in contract_registry.json",
              f"schemas/blackboard/{name}.v1.schema.json" in registry_blob)

    # ---- H. fixtures validate against their contracts (minimal stdlib validator) --------
    fixtures = _fixtures()
    check("H: a fixture exists for each of the 13 contracts", set(fixtures) == set(_CONTRACTS),
          f"fixtures={sorted(fixtures)}")
    for name in _CONTRACTS:
        if name not in schemas or name not in fixtures:
            continue
        problems = _validate_minimal(fixtures[name], schemas[name])
        check(f"H: fixture[{name}] satisfies required fields + types + const/enum (minimal validator)", not problems,
              "; ".join(problems))

    # ---- I. negative controls (the constraints must bite) -------------------------------
    # I.1 flipping serves_truth=True on an entry MUST fail const false.
    if "BlackboardEntry" in schemas:
        flipped = dict(fixtures["BlackboardEntry"])
        flipped["serves_truth"] = True
        check("I: negative control — flipping BlackboardEntry.serves_truth to True violates const false",
              bool(_validate_minimal(flipped, schemas["BlackboardEntry"])))
    # I.2 emptying a required non-empty source_refs on an Observation MUST fail minItems.
    if "BlackboardObservation" in schemas:
        sourceless = dict(fixtures["BlackboardObservation"])
        sourceless["source_refs"] = []
        check("I: negative control — dropping the source_ref from an Observation (empty source_refs) is rejected",
              bool(_validate_minimal(sourceless, schemas["BlackboardObservation"])))
    # I.3 (belt + suspenders) dropping a required field MUST fail (validator bites at all).
    if "BlackboardSynthesis" in schemas:
        broken = dict(fixtures["BlackboardSynthesis"])
        broken.pop("held_out", None)
        check("I: negative control — dropping a required field (Synthesis.held_out) is detected",
              bool(_validate_minimal(broken, schemas["BlackboardSynthesis"])))

    # ---- no raw keys in this proof (handles/env-refs only) ------------------------------
    # Tokens are assembled at runtime so this detector does not match its OWN source; it still
    # scans for the real concatenated key prefixes anywhere else in the file.
    src = Path(__file__).read_text()
    suspicious = ("s" + "k-", "AK" + "IA", "gh" + "p_", "AI" + "za")
    offenders = [tok for tok in suspicious if src.count(tok) > 0]
    check("J: proof source contains no raw API-key-like literals (handles/env-refs only)",
          not offenders, f"matched {offenders}")

    print("\n" + ("PASS — check_blackboard_contracts: the 13 P0 governed-blackboard contracts exist, are well-formed "
                  "(additionalProperties:false), are registered, and encode the governance law — output != truth "
                  "(serves_truth const false on Entry/Analysis/Synthesis/GovernedBlackboardEntry); provenance required "
                  "(Observation.source_refs non-empty; SourceRef.handle a ctx://|doc# handle); held-out kept separate "
                  "(Synthesis.held_out + source_handles); Baltor governance (GovernedBlackboardEntry.claim_status incl. "
                  "candidate/verified/conflicting/held_out/stale + promotion_eligible gate); compression preserves handles "
                  "+ held-out (const true). Fixtures validate and negative controls (serves_truth=True / emptied "
                  "source_refs) are rejected by a stdlib-only validator."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_blackboard_contracts.py --self-test")
    raise SystemExit(0)
