#!/usr/bin/env python3
"""scripts.check_teleon_agent_gateway_contracts — PROOF: the P0 governed CONTRACTS for the Teleon Agent
Capability Gateway are real. Teleon serves AI AGENTS as customers: agents call stable, deterministic,
receipt-backed CapabilityTasks instead of burning frontier tokens re-solving repeatable workflows. MCP
connects agents to tools; Teleon turns tools into governed capabilities. Law: agents ASK, Teleon EXECUTES,
Baltor governs truth; an agent/LLM output is NEVER truth; an agent cannot self-expand its own boundary;
deterministic-first.

Asserts:
  A. SCHEMAS EXIST + WELL-FORMED: all 6 gateway contracts are valid JSON and each carries $id (matching its
     filename, agents/<Name>), title, type:object, properties, required, additionalProperties:false, and a
     non-empty description.
  B. OUTPUT != TRUTH: AgentCapabilityRunResult.serves_truth is pinned const false — a capability result is
     governed evidence under Baltor's rail, never self-asserted, promotable truth.
  C. NO SELF-BOUNDARY-EXPANSION: AgentBoundaryExpansionRequest.status is pinned const
     "pending_human_approval" and .auto_applied is pinned const false — the one channel to widen a boundary
     is a request held for a human, never an action an agent applies to itself.
  D. DETERMINISTIC-FIRST GOVERNANCE: AgentCapabilityCard carries deterministic_first + llm_fallback_allowed +
     receipt_required (the token-saving ladder runs deterministic/cache/API before any LLM, LLM is gated, and
     a receipt can be forced).
  E. REGISTERED: all 6 contracts are registered in _repos/shared-backend-components/architecture/contract_registry.json with the matching
     schema path.
  F. FIXTURES VALIDATE: a tiny in-proof fixture for each of the 6 satisfies its required-field presence +
     declared top-level types + const/enum constraints, checked by a minimal stdlib validator (no jsonschema
     dependency). Negative controls bite: a dropped required field fails; a fixture flipping
     AgentCapabilityRunResult.serves_truth=true is REJECTED; and a fixture flipping
     AgentBoundaryExpansionRequest.auto_applied=true (an agent self-expanding its boundary) is REJECTED.

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

# The 6 P0 contracts of the Teleon Agent Capability Gateway, in load order.
_CONTRACTS = [
    "AgentCapabilityConsumer",
    "AgentCapabilityCard",
    "AgentCapabilityRunRequest",
    "AgentCapabilityRunResult",
    "AgentCapabilityReceipt",
    "AgentBoundaryExpansionRequest",
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
    union, `const`, `enum`, and array-item `pattern` forms used by these schemas). `const`/`enum` enforcement
    is the load-bearing part: it is how flipping serves_truth/auto_applied to True is caught."""
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
        if "pattern" in spec and isinstance(value, str) and not re.search(spec["pattern"], value):
            problems.append(f"key {key}: value {value!r} does not match pattern {spec['pattern']!r}")
        items = spec.get("items")
        if isinstance(items, dict) and "pattern" in items and isinstance(value, list):
            for i, item in enumerate(value):
                if not (isinstance(item, str) and re.search(items["pattern"], item)):
                    problems.append(
                        f"key {key}[{i}]: value {item!r} does not match item pattern {items['pattern']!r}")
    return problems


def _fixtures() -> dict[str, dict]:
    """A tiny, valid in-proof FIXTURE for each of the 6 contracts (required fields present, correct types,
    governance flags pinned correctly, secret refs as env:// references). These are evidence the contracts
    are instantiable — no result is served truth, no boundary is self-expanded, every secret is a reference."""
    boundary_policy = {
        "can_self_expand": False,
        "requires_human_for_boundary_change": True,
        "max_cost_per_run": {"unit": "usd", "amount": 0.01},
        "allowed_domains": ["consumerfinance.gov"],
    }
    secret_policy = {"refs": ["env://OPENAI_API_KEY_REF", "env://BALTOR_GATEWAY_TOKEN_REF"]}
    return {
        "AgentCapabilityConsumer": {
            "consumer_id": "consumer.claude-code-demo",
            "kind": "claude_code",
            "allowed_capabilities": ["cfpb.deadline.verify", "utility.hash"],
            "forbidden_tools": ["shell.exec", "fs.write"],
            "boundary_policy": boundary_policy,
            "secret_policy": secret_policy,
        },
        "AgentCapabilityCard": {
            "capability_id": "cfpb.deadline.verify",
            "purpose": "Return the governed CFPB response-deadline for a complaint type so the agent does not re-derive it.",
            "input_contract": {"type": "object", "properties": {"complaint_type": {"type": "string"}}},
            "output_contract": {"type": "object", "properties": {"deadline": {"type": "string"}}},
            "allowed_use": ["operational_reference"],
            "forbidden_use": ["legal_advice", "auto_promote_to_truth"],
            "expected_cost": {"unit": "usd", "typical": 0.0, "max": 0.001, "metric": "per_successful_run"},
            "expected_latency": {"unit": "ms", "p50": 5, "p95": 25},
            "freshness_policy": {"max_age": "24h", "cdc": True, "revocation_handled": True},
            "policy_notes": "Operational reference only; signer-accountable; not legal advice.",
            "deterministic_first": True,
            "llm_fallback_allowed": False,
            "receipt_required": True,
        },
        "AgentCapabilityRunRequest": {
            "request_id": "creq-0001",
            "consumer_id": "consumer.claude-code-demo",
            "capability_id": "cfpb.deadline.verify",
            "payload": {"complaint_type": "billing_error"},
            "input_ref": None,
            "allowed_use": ["operational_reference"],
            "max_cost": {"unit": "usd", "amount": 0.001},
            "freshness_requirement": {"max_age": "24h"},
            "require_receipt": True,
            "idempotency_key": "idem-creq-0001",
        },
        "AgentCapabilityRunResult": {
            "request_id": "creq-0001",
            "capability_id": "cfpb.deadline.verify",
            "status": "verified",
            "output": {"deadline": "10 business days"},
            "source_handles": ["ctx://tenant/baltor/source/cfpb#field.response_deadline"],
            "held_out": [{"value": "30 days", "reason": "superseded prior guidance — kept separate, not served"}],
            "receipt_id": "crcpt-0001",
            "fallback_used": None,
            "tokens_saved_estimate": 1800,
            "serves_truth": False,
            "allowed_use": ["operational_reference"],
        },
        "AgentCapabilityReceipt": {
            "receipt_id": "crcpt-0001",
            "request_id": "creq-0001",
            "capability_id": "cfpb.deadline.verify",
            "consumer_id": "consumer.claude-code-demo",
            "input_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "output_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
            "runtime_path": "deterministic",
            "backend": "local_function@v1",
            "cost_estimate": {"unit": "usd", "amount": 0.0},
            "started_at": "2026-01-01T00:00:00Z",
            "completed_at": "2026-01-01T00:00:01Z",
            "policy_checks": {
                "capability_allowed": True,
                "no_forbidden_tool_used": True,
                "secrets_refs_only": True,
                "deterministic_first_honored": True,
                "llm_fallback_within_policy": True,
                "cost_within_max": True,
                "freshness_met": True,
                "no_self_boundary_expansion": True,
            },
        },
        "AgentBoundaryExpansionRequest": {
            "request_id": "bexp-0001",
            "consumer_id": "consumer.claude-code-demo",
            "capability_id": "tariff.hs.classify.reference",
            "requested_change": {"add_capability": "tariff.hs.classify.reference"},
            "justification": "Agent repeatedly needs HS-code reference classification; requests gateway access.",
            "status": "pending_human_approval",
            "auto_applied": False,
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

    check("A: all 6 gateway schema files present + valid JSON", len(schemas) == len(_CONTRACTS),
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

    # ---- B. output != truth -------------------------------------------------------------
    if "AgentCapabilityRunResult" in schemas:
        check("B: AgentCapabilityRunResult.serves_truth pinned const false (a capability result is governed "
              "evidence, never self-asserted truth)",
              schemas["AgentCapabilityRunResult"]["properties"].get("serves_truth", {}).get("const") is False)

    # ---- C. no self-boundary-expansion (the agents-cannot-self-expand law) ---------------
    if "AgentBoundaryExpansionRequest" in schemas:
        bep = schemas["AgentBoundaryExpansionRequest"]["properties"]
        check("C: AgentBoundaryExpansionRequest.status pinned const 'pending_human_approval' (held for a human)",
              bep.get("status", {}).get("const") == "pending_human_approval")
        check("C: AgentBoundaryExpansionRequest.auto_applied pinned const false (an agent cannot self-expand "
              "its boundary)",
              bep.get("auto_applied", {}).get("const") is False)

    # ---- D. deterministic-first governance on the capability card -----------------------
    if "AgentCapabilityCard" in schemas:
        card = schemas["AgentCapabilityCard"]
        card_props = card["properties"]
        card_required = card.get("required", [])
        for field in ("deterministic_first", "llm_fallback_allowed", "receipt_required"):
            check(f"D: AgentCapabilityCard carries {field} (present + required)",
                  field in card_props and field in card_required)
        # deterministic_first is an invariant — pinned const true (the ladder always runs deterministic-first).
        check("D: AgentCapabilityCard.deterministic_first pinned const true (deterministic-first is an invariant)",
              card_props.get("deterministic_first", {}).get("const") is True)

    # ---- E. registered in the contract registry ----------------------------------------
    registry = json.loads((_resource("architecture") / "contract_registry.json").read_text())
    registry_blob = json.dumps(registry)
    for name in _CONTRACTS:
        check(f"E: {name} registered in contract_registry.json",
              f"schemas/agents/{name}.schema.json" in registry_blob)

    # ---- F. fixtures validate against their contracts (minimal stdlib validator) --------
    fixtures = _fixtures()
    check("F: a fixture exists for each of the 6 contracts", set(fixtures) == set(_CONTRACTS),
          f"fixtures={sorted(fixtures)}")
    for name in _CONTRACTS:
        if name not in schemas or name not in fixtures:
            continue
        problems = _validate_minimal(fixtures[name], schemas[name])
        check(f"F: fixture[{name}] satisfies required fields + types + const/enum (minimal validator)",
              not problems, "; ".join(problems))

    # Negative control: dropping a required field MUST be detected (proves the validator bites).
    if "AgentCapabilityRunResult" in schemas:
        broken = dict(fixtures["AgentCapabilityRunResult"])
        broken.pop("source_handles", None)
        check("F: negative control — dropping a required field is detected by the validator",
              bool(_validate_minimal(broken, schemas["AgentCapabilityRunResult"])))

        # Negative control (load-bearing #1): flipping serves_truth to True violates const false.
        flipped_truth = dict(fixtures["AgentCapabilityRunResult"])
        flipped_truth["serves_truth"] = True
        check("F: negative control — a result with serves_truth=true is REJECTED (output is never truth)",
              bool(_validate_minimal(flipped_truth, schemas["AgentCapabilityRunResult"])))

    # Negative control (load-bearing #2): an agent self-expanding its boundary (auto_applied=true) is rejected.
    if "AgentBoundaryExpansionRequest" in schemas:
        self_expand = dict(fixtures["AgentBoundaryExpansionRequest"])
        self_expand["auto_applied"] = True
        check("F: negative control — a boundary request with auto_applied=true is REJECTED (no self-expansion)",
              bool(_validate_minimal(self_expand, schemas["AgentBoundaryExpansionRequest"])))
        # And an auto-approved status is rejected too.
        auto_approved = dict(fixtures["AgentBoundaryExpansionRequest"])
        auto_approved["status"] = "approved"
        check("F: negative control — a boundary request with status!=pending_human_approval is REJECTED",
              bool(_validate_minimal(auto_approved, schemas["AgentBoundaryExpansionRequest"])))

    print("\n" + ("PASS — check_teleon_agent_gateway_contracts: the 6 P0 Teleon Agent Capability Gateway "
                  "contracts exist, are well-formed (additionalProperties:false), are registered, and encode "
                  "agents-ASK-Teleon-EXECUTES (Consumer/Card/RunRequest/RunResult/Receipt/BoundaryExpansion), "
                  "output!=truth (AgentCapabilityRunResult.serves_truth const false), no-self-boundary-expansion "
                  "(AgentBoundaryExpansionRequest.status const 'pending_human_approval' + auto_applied const "
                  "false), and deterministic-first (AgentCapabilityCard deterministic_first const true + "
                  "llm_fallback_allowed + receipt_required). Fixtures validate under a stdlib-only "
                  "required-keys + type + const/enum check; flipping serves_truth or auto_applied is rejected."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_teleon_agent_gateway_contracts.py --self-test")
    raise SystemExit(0)
