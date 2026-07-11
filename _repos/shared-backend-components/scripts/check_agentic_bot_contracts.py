#!/usr/bin/env python3
"""scripts.check_agentic_bot_contracts — PROOF: the P1A governed RUN CONTRACTS for the shared agentic-bot
plane are real. This is the request/result/receipt + policy contract layer ABOVE the agent-runtime port
(_repos/teleon/backend/src/teleon/agents/agent_runtime_provider.py); OpenClaw/Hermes-style runtimes are CANDIDATES behind it, and
the deterministic local emulator is the correctness invariant. Law: agents PROPOSE, Baltor DISPOSES; an
agent/tool/skill output is NEVER truth; candidate != active.

Asserts:
  A. SCHEMAS EXIST + WELL-FORMED: all 8 agent contracts are valid JSON and each carries $id (matching its
     filename), title, type:object, properties, required, additionalProperties:false, and a non-empty description.
  B. OUTPUT != TRUTH: AgentRunResult.serves_truth, AgentProviderUnavailableResult.serves_truth +
     .consumable, and AgentMemoryPolicy.cross_tenant are all pinned const false; the run output / an
     unavailable result / cross-tenant memory can never be served, consumed, or crossed.
  C. SKILL + SECRET GOVERNANCE: AgentSkillPolicy pins agent_created_skills_status const "candidate" and
     carries requires_eval_before_active (agent-created skills are never born active); AgentRunReceipt's
     secret_refs_used items use the env:// pattern (REFERENCES only — never secret values).
  D. REGISTERED: all 8 contracts are registered in _repos/shared-backend-components/architecture/contract_registry.json with the matching
     schema path.
  E. FIXTURES VALIDATE: a tiny in-proof fixture for each of the 8 satisfies its required-field presence +
     declared top-level types, checked by a minimal stdlib validator (no jsonschema dependency). Negative
     controls bite: a dropped required field fails; a flipped const-false flag fails; and an AgentRunReceipt
     fixture carrying a real-LOOKING key value (assembled at runtime so the literal never appears in source)
     is REJECTED because secret_refs_used must be env:// references, not values.

Deterministic + offline. stdlib only. Exit 0/1. No raw keys/secrets.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import re
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_SCHEMA_DIR = _resource("schemas") / "agents"

# The 8 P1A run contracts of the shared agentic-bot plane, in load order.
_CONTRACTS = [
    "AgentRunRequest",
    "AgentRunResult",
    "AgentRunReceipt",
    "AgentToolPolicy",
    "AgentSkillPolicy",
    "AgentSandboxPolicy",
    "AgentMemoryPolicy",
    "AgentProviderUnavailableResult",
]

# The env:// reference scheme secret_refs_used / runtime_ref must use (REFERENCES only, never values).
_ENV_REF_PATTERN = "^env://"

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
    union, `const`, `enum`, and array-item `pattern` forms used by these schemas). Array-item `pattern` is
    enforced so a receipt's secret_refs_used must be env:// references (a real key value is rejected)."""
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
        # scalar-level pattern (e.g. runtime_ref must be env://…), skipping null for nullable refs.
        if "pattern" in spec and isinstance(value, str) and not re.search(spec["pattern"], value):
            problems.append(f"key {key}: value {value!r} does not match pattern {spec['pattern']!r}")
        # array-item pattern (e.g. secret_refs_used items must each be env://… references, never values).
        items = spec.get("items")
        if isinstance(items, dict) and "pattern" in items and isinstance(value, list):
            for i, item in enumerate(value):
                if not (isinstance(item, str) and re.search(items["pattern"], item)):
                    problems.append(
                        f"key {key}[{i}]: value {item!r} does not match item pattern {items['pattern']!r}")
    return problems


def _fixtures() -> dict[str, dict]:
    """A tiny, valid in-proof FIXTURE for each of the 8 contracts (required fields present, correct types,
    governance flags pinned to false, secret refs as env:// references). These are evidence the contracts are
    instantiable — none is served truth; every secret is a reference, never a value."""
    sandbox_policy = {
        "required": True,
        "isolation_level": "container",
        "network_policy": "deny",
        "no_host_exec_by_default": True,
    }
    memory_policy = {"scope": "tenant", "cross_tenant": False, "writes_allowed": False}
    secret_policy = {"refs": ["env://OPENAI_API_KEY_REF", "env://ANTHROPIC_API_KEY_REF"]}
    return {
        "AgentRunRequest": {
            "schema_version": "v1",
            "run_id": "arun-0001",
            "product_id": "baltor",
            "tenant_id": "tenant-demo",
            "agent_profile_id": "profile.bounded-researcher",
            "harness_provider": "local_emulator@v1",
            "input_ref": "ctx://tenant/tenant-demo/source/sid#task.0001",
            "input": None,
            "allowed_tools": ["http.get", "fs.read"],
            "allowed_skills": ["skill.summarize"],
            "forbidden_tools": ["fs.write", "shell.exec"],
            "sandbox_policy": sandbox_policy,
            "secret_policy": secret_policy,
            "memory_policy": memory_policy,
            "max_steps": 25,
            "timeout_ms": 60000,
            "require_receipt": True,
        },
        "AgentRunResult": {
            "run_id": "arun-0001",
            "status": "succeeded",
            "output": {"answer": "candidate proposal — measured, never served"},
            "output_ref": None,
            "output_contract_valid": True,
            "tool_calls": [{"tool": "http.get", "ok": True}],
            "skills_loaded": ["skill.summarize"],
            "sandbox_events": [{"event": "network_blocked", "target": "example.com"}],
            "policy_violations": [],
            "receipt_id": "arcpt-0001",
            "serves_truth": False,
        },
        "AgentRunReceipt": {
            "receipt_id": "arcpt-0001",
            "run_id": "arun-0001",
            "product_id": "baltor",
            "tenant_id": "tenant-demo",
            "harness_provider": "local_emulator@v1",
            "agent_profile_id": "profile.bounded-researcher",
            "input_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "output_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
            "tools_used": ["http.get"],
            "skills_loaded": ["skill.summarize"],
            "secret_refs_used": ["env://OPENAI_API_KEY_REF"],
            "sandbox_policy": sandbox_policy,
            "memory_policy": memory_policy,
            "policy_checks": {
                "tools_allowlisted": True,
                "no_forbidden_tool_used": True,
                "sandbox_enforced": True,
                "secrets_refs_only": True,
                "no_cross_tenant_memory": True,
                "steps_bounded": True,
                "timeout_enforced": True,
            },
            "started_at": "2026-01-01T00:00:00Z",
            "completed_at": "2026-01-01T00:00:01Z",
        },
        "AgentToolPolicy": {
            "allowlist": ["http.get", "fs.read"],
            "denylist": ["shell.exec"],
            "requires_sandbox": True,
            "elevated_requires_approval": True,
        },
        "AgentSkillPolicy": {
            "allowlist": ["skill.summarize"],
            "progressive_disclosure": True,
            "agent_created_skills_status": "candidate",
            "requires_eval_before_active": True,
        },
        "AgentSandboxPolicy": dict(sandbox_policy),
        "AgentMemoryPolicy": dict(memory_policy),
        "AgentProviderUnavailableResult": {
            "provider_id": "openclaw@candidate",
            "reason": "candidate agent runtime not imported/executed (owner-gated)",
            "runtime_ref": "env://OPENCLAW_RUNTIME_REF",
            "consumable": False,
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
        path = _SCHEMA_DIR / f"{name}.schema.json"
        if not path.exists():
            check(f"A: schema file exists: {name}", False, str(path))
            continue
        try:
            schemas[name] = json.loads(path.read_text())
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            check(f"A: schema is valid JSON: {name}", False, str(exc))

    check("A: all 8 agent schema files present + valid JSON", len(schemas) == len(_CONTRACTS),
          f"loaded {sorted(schemas)}")

    for name, schema in schemas.items():
        keys_ok = all(k in schema for k in ("$id", "title", "type", "properties", "required", "additionalProperties"))
        shape_ok = (
            schema.get("$id") == f"agents/{name}"
            and schema.get("title") == f"{name}"
            and schema.get("type") == "object"
            and schema.get("additionalProperties") is False
            and isinstance(schema.get("properties"), dict)
            and isinstance(schema.get("required"), list)
            and isinstance(schema.get("description"), str) and schema.get("description")
        )
        check(f"A: {name} has $id/title/type/properties/required/additionalProperties:false (+description)",
              keys_ok and shape_ok,
              json.dumps({k: schema.get(k) for k in ("$id", "title", "type", "additionalProperties")}))

    # ---- B. output != truth (governance flags pinned to const false) --------------------
    if "AgentRunResult" in schemas:
        check("B: AgentRunResult.serves_truth pinned const false (an agent run is a proposal, never served truth)",
              schemas["AgentRunResult"]["properties"].get("serves_truth", {}).get("const") is False)
    if "AgentProviderUnavailableResult" in schemas:
        unp = schemas["AgentProviderUnavailableResult"]["properties"]
        check("B: AgentProviderUnavailableResult.serves_truth pinned const false",
              unp.get("serves_truth", {}).get("const") is False)
        check("B: AgentProviderUnavailableResult.consumable pinned const false (no usable output)",
              unp.get("consumable", {}).get("const") is False)
    if "AgentMemoryPolicy" in schemas:
        check("B: AgentMemoryPolicy.cross_tenant pinned const false (cross-tenant memory is forbidden)",
              schemas["AgentMemoryPolicy"]["properties"].get("cross_tenant", {}).get("const") is False)
    if "AgentRunReceipt" in schemas:
        # The receipt is provenance — it attests the OUTPUT by hash, never carrying a served output field.
        rcpt_props = schemas["AgentRunReceipt"]["properties"]
        check("B: AgentRunReceipt attests output by HASH (output_hash present; no served output field)",
              "output_hash" in rcpt_props and "output" not in rcpt_props)

    # ---- C. skill + secret governance ---------------------------------------------------
    if "AgentSkillPolicy" in schemas:
        sk = schemas["AgentSkillPolicy"]["properties"]
        check("C: AgentSkillPolicy.agent_created_skills_status pinned const 'candidate' (never born active)",
              sk.get("agent_created_skills_status", {}).get("const") == "candidate")
        check("C: AgentSkillPolicy carries requires_eval_before_active (eval gate before active)",
              "requires_eval_before_active" in sk
              and "requires_eval_before_active" in schemas["AgentSkillPolicy"].get("required", []))
    if "AgentRunReceipt" in schemas:
        sru = schemas["AgentRunReceipt"]["properties"].get("secret_refs_used", {})
        item_pattern = (sru.get("items") or {}).get("pattern")
        check("C: AgentRunReceipt.secret_refs_used items use the env:// pattern (REFERENCES only, never values)",
              item_pattern == _ENV_REF_PATTERN, f"item pattern={item_pattern!r}")
    if "AgentProviderUnavailableResult" in schemas:
        rr = schemas["AgentProviderUnavailableResult"]["properties"].get("runtime_ref", {})
        check("C: AgentProviderUnavailableResult.runtime_ref uses the env:// pattern (a ref, never a value)",
              rr.get("pattern") == _ENV_REF_PATTERN, f"pattern={rr.get('pattern')!r}")

    # ---- D. registered in the contract registry ----------------------------------------
    registry = json.loads((_resource("architecture") / "contract_registry.json").read_text())
    registry_blob = json.dumps(registry)
    for name in _CONTRACTS:
        check(f"D: {name} registered in contract_registry.json",
              f"schemas/agents/{name}.schema.json" in registry_blob)

    # ---- E. fixtures validate against their contracts (minimal stdlib validator) --------
    fixtures = _fixtures()
    check("E: a fixture exists for each of the 8 contracts", set(fixtures) == set(_CONTRACTS),
          f"fixtures={sorted(fixtures)}")
    for name in _CONTRACTS:
        if name not in schemas or name not in fixtures:
            continue
        problems = _validate_minimal(fixtures[name], schemas[name])
        check(f"E: fixture[{name}] satisfies required fields + types (minimal validator)", not problems,
              "; ".join(problems))

    # Negative control: a fixture missing a required field MUST fail the validator (proves the validator bites).
    if "AgentRunResult" in schemas:
        broken = dict(fixtures["AgentRunResult"])
        broken.pop("serves_truth", None)
        check("E: negative control — dropping a required field is detected by the validator",
              bool(_validate_minimal(broken, schemas["AgentRunResult"])))
        flipped = dict(fixtures["AgentRunResult"])
        flipped["serves_truth"] = True
        check("E: negative control — flipping serves_truth to True violates const false",
              bool(_validate_minimal(flipped, schemas["AgentRunResult"])))
    if "AgentMemoryPolicy" in schemas:
        flipped_mem = dict(fixtures["AgentMemoryPolicy"])
        flipped_mem["cross_tenant"] = True
        check("E: negative control — flipping cross_tenant to True violates const false",
              bool(_validate_minimal(flipped_mem, schemas["AgentMemoryPolicy"])))

    # Negative control (the load-bearing one): an AgentRunReceipt carrying a real-LOOKING key VALUE in
    # secret_refs_used is REJECTED — those must be env:// references, never values. The key literal is
    # ASSEMBLED at runtime so it never appears in source (keeps the secret-hygiene scanner happy).
    if "AgentRunReceipt" in schemas:
        fake_key = "sk-" + "x" * 16  # assembled; not a literal in source
        leaked = dict(fixtures["AgentRunReceipt"])
        leaked["secret_refs_used"] = [fake_key]
        leak_problems = _validate_minimal(leaked, schemas["AgentRunReceipt"])
        check("E: negative control — a receipt with a real-looking key VALUE (not an env:// ref) is REJECTED",
              bool(leak_problems), "; ".join(leak_problems) or "validator did not reject the leaked value")

    print("\n" + ("PASS — check_agentic_bot_contracts: the 8 P1A agentic-bot run contracts exist, are well-formed "
                  "(additionalProperties:false), are registered, and enforce agents-PROPOSE-never-truth "
                  "(AgentRunResult.serves_truth / AgentProviderUnavailableResult.serves_truth+consumable / "
                  "AgentMemoryPolicy.cross_tenant pinned const false), candidate-only agent skills "
                  "(agent_created_skills_status const 'candidate' + eval-before-active), and secret-REFS-only "
                  "(secret_refs_used / runtime_ref env:// pattern — a key VALUE is rejected). Fixtures validate "
                  "under a stdlib-only required-keys + type + pattern check."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_agentic_bot_contracts.py --self-test")
    raise SystemExit(0)
