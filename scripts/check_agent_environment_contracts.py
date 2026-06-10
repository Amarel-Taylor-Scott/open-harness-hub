#!/usr/bin/env python3
"""scripts.check_agent_environment_contracts — PROOF: the P0 CONTRACTS for the Environment + Reward Spine are
real. The spine is the local-first, governed agent-eval layer that MEASURES agents/runtimes (Repo2RLEnv /
Harbor / OpenEnv-style environments are CANDIDATES behind it). A benchmark/reward result is EVIDENCE, never a
promotion authority, and the agent/LLM output is never truth.

Asserts:
  A. SCHEMAS EXIST + WELL-FORMED: all 7 environment contracts are valid JSON and each carries $id (matching its
     filename), title, type:object, properties, required, and additionalProperties:false.
  B. OUTPUT != TRUTH: the result/receipt/reward contracts pin the governance flag to const false —
     EnvironmentRunResult.serves_truth=false, RewardResult.is_truth=false (and EnvironmentProviderNode /
     RewardProviderNode also pin serves_truth=false). An environment run / reward score can never be served truth.
  C. CANDIDATE-FIRST: EnvironmentProviderNode and RewardProviderNode status enums include BOTH candidate and
     reference (nodes are not born "active"); the enum is not the single value "active".
  D. REGISTERED: all 7 contracts are registered in architecture/contract_registry.json with the matching schema path.
  E. FIXTURES VALIDATE: a tiny in-proof fixture for each of the 7 satisfies its required-field presence + declared
     top-level types, checked by a minimal stdlib validator (no jsonschema dependency).

Deterministic + offline. stdlib only. Exit 0/1. No raw keys/secrets.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_SCHEMA_DIR = _REPO / "schemas" / "environments"

# The 7 P0 contracts of the Environment + Reward Spine, in load order.
_CONTRACTS = [
    "EnvironmentRunRequest",
    "EnvironmentRunResult",
    "EnvironmentRunReceipt",
    "RewardSpec",
    "RewardResult",
    "EnvironmentProviderNode",
    "RewardProviderNode",
]

# JSON-Schema "type" -> Python types, for the minimal stdlib validator.
_JSON_TYPE_TO_PY = {
    "object": (dict,),
    "array": (list,),
    "string": (str,),
    # NOTE: bool is a subclass of int in Python; we special-case "integer"/"number" below to exclude bools.
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
    """A tiny required-keys + top-level type validator. Returns a list of human-readable problems.

    Intentionally NOT a full JSON-Schema engine — just enough to prove the fixtures satisfy each contract's
    required fields and that each present, typed property matches its declared `type` (handling the `[a, b]`
    union and `const` forms used by these schemas).
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
    return problems


def _fixtures() -> dict[str, dict]:
    """A tiny, valid in-proof FIXTURE for each of the 7 contracts (required fields present, correct types,
    governance flags pinned to false). These are evidence the contracts are instantiable — none is served truth."""
    return {
        "EnvironmentRunRequest": {
            "schema_version": "v1",
            "run_id": "run-0001",
            "environment_id": "env.local-golden-path",
            "agent_id": "agent.under-test",
            "tenant_id": "tenant-demo",
            "input_ref": "ctx://tenant/tenant-demo/source/sid#task.0001",
            "input": None,
            "max_steps": 25,
            "timeout_ms": 60000,
            "reward_spec_id": "reward.deterministic.0001",
            "require_receipt": True,
        },
        "EnvironmentRunResult": {
            "run_id": "run-0001",
            "environment_id": "env.local-golden-path",
            "status": "succeeded",
            "output": {"answer": "candidate output — measured, never served"},
            "output_ref": None,
            "steps_taken": 7,
            "reward_result_id": "rr-0001",
            "receipt_id": "rcpt-0001",
            "serves_truth": False,
        },
        "EnvironmentRunReceipt": {
            "receipt_id": "rcpt-0001",
            "run_id": "run-0001",
            "environment_id": "env.local-golden-path",
            "agent_id": "agent.under-test",
            "tenant_id": "tenant-demo",
            "input_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "output_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
            "reward_result_id": "rr-0001",
            "started_at": "2026-01-01T00:00:00Z",
            "completed_at": "2026-01-01T00:00:01Z",
            "policy_checks": {
                "network_denied": True,
                "secrets_denied": True,
                "steps_bounded": True,
                "timeout_enforced": True,
                "local_equivalent_used": True,
            },
        },
        "RewardSpec": {
            "reward_spec_id": "reward.deterministic.0001",
            "kind": "deterministic_check",
            "checks": [{"check_id": "c1", "weight": 1.0, "assertion": "output.answer is non-empty"}],
            "max_score": 1.0,
            "requires_execution": False,
        },
        "RewardResult": {
            "reward_result_id": "rr-0001",
            "reward_spec_id": "reward.deterministic.0001",
            "run_id": "run-0001",
            "score": 1.0,
            "max_score": 1.0,
            "passed": True,
            "breakdown": [{"check_id": "c1", "points": 1.0, "max_points": 1.0, "passed": True, "detail": "ok"}],
            "is_truth": False,
        },
        "EnvironmentProviderNode": {
            "provider_id": "env.local-golden-path",
            "name": "local-golden-path",
            "status": "candidate",
            "requires_docker": False,
            "requires_network": False,
            "local_equivalent": "env.local-golden-path",
            "serves_truth": False,
        },
        "RewardProviderNode": {
            "provider_id": "reward.local-deterministic-checker",
            "name": "local-deterministic-checker",
            "status": "candidate",
            "deterministic": True,
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

    check("A: all 7 environment schema files present + valid JSON", len(schemas) == len(_CONTRACTS),
          f"loaded {sorted(schemas)}")

    for name, schema in schemas.items():
        keys_ok = all(k in schema for k in ("$id", "title", "type", "properties", "required", "additionalProperties"))
        shape_ok = (
            schema.get("$id") == f"environments/{name}.v1"
            and schema.get("title") == f"{name}.v1"
            and schema.get("type") == "object"
            and schema.get("additionalProperties") is False
            and isinstance(schema.get("properties"), dict)
            and isinstance(schema.get("required"), list)
            and isinstance(schema.get("description"), str) and schema.get("description")
        )
        check(f"A: {name} has $id/title/type/properties/required/additionalProperties:false (+description)",
              keys_ok and shape_ok, json.dumps({k: schema.get(k) for k in ("$id", "title", "type", "additionalProperties")}))

    # ---- B. output != truth (governance flags pinned to const false) --------------------
    if "EnvironmentRunResult" in schemas:
        check("B: EnvironmentRunResult.serves_truth pinned const false (run output is never served truth)",
              schemas["EnvironmentRunResult"]["properties"].get("serves_truth", {}).get("const") is False)
    if "RewardResult" in schemas:
        check("B: RewardResult.is_truth pinned const false (a reward score is evidence, not authority)",
              schemas["RewardResult"]["properties"].get("is_truth", {}).get("const") is False)
    if "EnvironmentRunReceipt" in schemas:
        # The receipt is provenance — it has no truth-bearing field; the OUTPUT it attests is hashed, never served.
        rcpt_props = schemas["EnvironmentRunReceipt"]["properties"]
        check("B: EnvironmentRunReceipt attests output by HASH (output_hash present; not a served output field)",
              "output_hash" in rcpt_props and "output" not in rcpt_props)
    for node in ("EnvironmentProviderNode", "RewardProviderNode"):
        if node in schemas:
            check(f"B: {node}.serves_truth pinned const false",
                  schemas[node]["properties"].get("serves_truth", {}).get("const") is False)

    # ---- C. candidate-first provider nodes ---------------------------------------------
    for node in ("EnvironmentProviderNode", "RewardProviderNode"):
        if node in schemas:
            enum = schemas[node]["properties"].get("status", {}).get("enum", [])
            check(f"C: {node}.status enum includes candidate + reference (NOT only 'active')",
                  "candidate" in enum and "reference" in enum and enum != ["active"], str(enum))

    # ---- D. registered in the contract registry ----------------------------------------
    registry = json.loads((_REPO / "architecture" / "contract_registry.json").read_text())
    registry_blob = json.dumps(registry)
    for name in _CONTRACTS:
        check(f"D: {name}.v1 registered in contract_registry.json",
              f"schemas/environments/{name}.v1.schema.json" in registry_blob)

    # ---- E. fixtures validate against their contracts (minimal stdlib validator) --------
    fixtures = _fixtures()
    check("E: a fixture exists for each of the 7 contracts", set(fixtures) == set(_CONTRACTS),
          f"fixtures={sorted(fixtures)}")
    for name in _CONTRACTS:
        if name not in schemas or name not in fixtures:
            continue
        problems = _validate_minimal(fixtures[name], schemas[name])
        check(f"E: fixture[{name}] satisfies required fields + types (minimal validator)", not problems,
              "; ".join(problems))

    # Negative control: a fixture missing a required field MUST fail the validator (proves the validator bites).
    if "RewardResult" in schemas:
        broken = dict(fixtures["RewardResult"])
        broken.pop("is_truth", None)
        check("E: negative control — dropping a required field is detected by the validator",
              bool(_validate_minimal(broken, schemas["RewardResult"])))
        # A const-false flag flipped to True MUST fail.
        flipped = dict(fixtures["RewardResult"])
        flipped["is_truth"] = True
        check("E: negative control — flipping is_truth to True violates const false",
              bool(_validate_minimal(flipped, schemas["RewardResult"])))

    print("\n" + ("PASS — check_agent_environment_contracts: the 7 P0 Environment + Reward Spine contracts exist, "
                  "are well-formed (additionalProperties:false), are registered, and enforce output != truth "
                  "(EnvironmentRunResult.serves_truth / RewardResult.serves-as-evidence is_truth pinned const false; "
                  "provider nodes are candidate-first and never serve truth). Fixtures validate under a stdlib-only "
                  "required-keys + type check."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_agent_environment_contracts.py --self-test")
    raise SystemExit(0)
