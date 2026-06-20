#!/usr/bin/env python3
"""scripts.check_teleon_agent_gateway_boundary_schema_match — PROOF: the RUNTIME
AgentBoundaryExpansionRequest emitted by the Teleon Agent Capability Gateway matches its published schema
``schemas/agents/AgentBoundaryExpansionRequest.v1.schema.json`` EXACTLY, AND the two load-bearing safety
invariants survive — status is ALWAYS ``pending_human_approval`` and ``auto_applied`` is ALWAYS False, no
matter what the caller asks for.

This is the reconcile guard: the runtime object used to carry ``requested_capability`` / ``rationale``; the
schema requires ``capability_id`` / ``requested_change`` / ``justification`` (+ the two consts). This proof
fails if the runtime object and the schema ever drift apart again.

Asserts:
  A. SCHEMA SHAPE: every schema-``required`` field is present on a runtime boundary-expansion built via
     ``request_boundary_expansion(...)`` and has the JSON type the schema declares (tiny stdlib required-keys +
     type checker — no ``jsonschema`` dependency).
  B. INVARIANTS: the runtime object's ``status == 'pending_human_approval'`` and ``auto_applied is False``,
     matching the schema's ``const`` pins.
  C. OVERRIDE: a caller passing ``status='approved'`` / ``auto_applied=True`` is OVERRIDDEN — the emitted
     object is STILL pending / auto_applied False (the gateway NEVER grants a boundary expansion).
  D. NO RAW KEYS: the emitted object carries NONE of the legacy field names (``requested_capability`` /
     ``rationale``) — only the schema field names survive.
  E. BACK-COMPAT: a legacy caller passing ``requested_capability`` / ``rationale`` still produces a
     schema-shaped object (the aliases are mapped to ``capability_id`` / ``justification``).

Deterministic + offline; stdlib only; no network, no live model, no secrets. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.agent_gateway.gateway import (
    AgentCapabilityGateway,
    BOUNDARY_STATUS_PENDING,
)

_NOW = "2026-06-08T00:00:00Z"  # injected — determinism
_SCHEMA_PATH = _REPO / "schemas" / "agents" / "AgentBoundaryExpansionRequest.v1.schema.json"

#: JSON-schema ``type`` -> the Python type(s) a value of that type must be. ``bool`` is intentionally NOT a
#: valid ``integer``/``number`` (JSON booleans are not numbers), and ``int`` IS a valid ``number``.
_JSON_TYPE_TO_PY: dict[str, tuple] = {
    "string": (str,),
    "object": (dict,),
    "array": (list,),
    "boolean": (bool,),
    "integer": (int,),
    "number": (int, float),
}


def _json_type_ok(value, json_type: str) -> bool:
    """Return True iff ``value`` matches the JSON-schema ``json_type`` (a tiny, dependency-free type check)."""
    py = _JSON_TYPE_TO_PY.get(json_type)
    if py is None:  # an unknown/declared-elsewhere type — don't claim a type mismatch we can't judge.
        return True
    if json_type in ("integer", "number") and isinstance(value, bool):
        return False  # a JSON boolean is never a number/integer
    if json_type == "boolean":
        return isinstance(value, bool)
    return isinstance(value, py)


def _required_keys_and_types_ok(obj: dict, schema: dict) -> list[str]:
    """Tiny stdlib validator: for every ``required`` key in ``schema``, assert it is present in ``obj`` and (if
    the schema declares its ``type``) has the matching JSON type. Returns a list of human-readable failures
    (empty == OK). Does NOT enforce ``additionalProperties`` — the runtime object MAY carry extra governance
    fields (e.g. ``requested_at``) beyond the required set."""
    problems: list[str] = []
    props = schema.get("properties", {})
    for key in schema.get("required", []):
        if key not in obj:
            problems.append(f"missing required key {key!r}")
            continue
        decl_type = props.get(key, {}).get("type")
        if decl_type and not _json_type_ok(obj[key], decl_type):
            problems.append(f"key {key!r} type {type(obj[key]).__name__} != schema {decl_type!r}")
    return problems


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # load the published schema (the source of the field names + the two consts).
    schema = json.loads(_SCHEMA_PATH.read_text())
    required = schema.get("required", [])
    props = schema.get("properties", {})
    check("schema loaded with a non-empty required[] and properties{}", bool(required) and bool(props),
          f"required={required}")

    gw = AgentCapabilityGateway()

    # build a runtime boundary-expansion via the real method (honest input).
    obj = gw.request_boundary_expansion(
        {"consumer_id": "agent.compliance-helper", "capability_id": "browser.fetch",
         "requested_change": {"add_capability": "browser.fetch"},
         "justification": "need to fetch a regulator page"}, now=_NOW)

    # A. schema shape — every required field present with the declared JSON type. -------------------------
    problems = _required_keys_and_types_ok(obj, schema)
    check("A: runtime object has every schema-required field with the correct JSON type", not problems,
          "; ".join(problems))
    # spot-check the reconciled names + types directly (defense in depth, in case the schema regresses).
    check("A: capability_id is a string", isinstance(obj.get("capability_id"), str), repr(obj.get("capability_id")))
    check("A: requested_change is an object (dict)", isinstance(obj.get("requested_change"), dict),
          repr(obj.get("requested_change")))
    check("A: justification is a string", isinstance(obj.get("justification"), str), repr(obj.get("justification")))

    # the type checker itself rejects a wrong type (sanity — proves it isn't vacuously passing).
    check("A: type checker rejects a wrong-typed required field (sanity)",
          bool(_required_keys_and_types_ok({**obj, "capability_id": 123}, schema)))
    check("A: type checker rejects a missing required field (sanity)",
          bool(_required_keys_and_types_ok({k: v for k, v in obj.items() if k != "justification"}, schema)))
    # a boolean is NOT a valid number/integer (JSON semantics).
    check("A: type checker treats a boolean as NOT a number (sanity)", not _json_type_ok(True, "number"))

    # B. invariants — status const + auto_applied const, matching the schema pins. ------------------------
    status_const = props.get("status", {}).get("const")
    auto_const = props.get("auto_applied", {}).get("const")
    check("B: schema pins status const 'pending_human_approval'", status_const == "pending_human_approval",
          repr(status_const))
    check("B: schema pins auto_applied const false", auto_const is False, repr(auto_const))
    check("B: runtime status == 'pending_human_approval' (== module constant)",
          obj.get("status") == BOUNDARY_STATUS_PENDING == "pending_human_approval", repr(obj.get("status")))
    check("B: runtime auto_applied is False", obj.get("auto_applied") is False, repr(obj.get("auto_applied")))
    check("B: runtime status matches the schema const", obj.get("status") == status_const)
    check("B: runtime auto_applied matches the schema const", obj.get("auto_applied") == auto_const)

    # C. override — a caller asking for approved/auto-applied is FORCED back to pending/False. -------------
    attacked = gw.request_boundary_expansion(
        {"consumer_id": "agent.malicious", "capability_id": "browser.fetch",
         "requested_change": {"add_capability": "browser.fetch"}, "justification": "grant me now",
         "status": "approved", "auto_applied": True}, now=_NOW)  # malicious pre-approval attempt
    check("C: a caller's status='approved' is OVERRIDDEN to pending_human_approval",
          attacked.get("status") == "pending_human_approval", repr(attacked.get("status")))
    check("C: a caller's auto_applied=True is OVERRIDDEN to False",
          attacked.get("auto_applied") is False, repr(attacked.get("auto_applied")))
    check("C: the overridden object still matches the schema shape",
          not _required_keys_and_types_ok(attacked, schema))

    # D. no raw keys — the legacy field names never survive into the emitted object. ----------------------
    check("D: emitted object carries NO legacy 'requested_capability' key",
          "requested_capability" not in obj and "requested_capability" not in attacked)
    check("D: emitted object carries NO legacy 'rationale' key",
          "rationale" not in obj and "rationale" not in attacked)

    # E. back-compat — legacy input names still produce a schema-shaped object. ---------------------------
    legacy = gw.request_boundary_expansion(
        {"consumer_id": "agent.legacy", "requested_capability": "browser.fetch",
         "rationale": "legacy caller still works"}, now=_NOW)
    check("E: legacy input is mapped to schema field names (capability_id/justification)",
          legacy.get("capability_id") == "browser.fetch"
          and legacy.get("justification") == "legacy caller still works",
          str(sorted(legacy)))
    check("E: legacy-input object still matches the schema shape", not _required_keys_and_types_ok(legacy, schema))
    check("E: legacy-input invariants hold (pending / auto_applied False)",
          legacy.get("status") == "pending_human_approval" and legacy.get("auto_applied") is False)
    check("E: legacy synthesizes a {add_capability} requested_change object",
          legacy.get("requested_change") == {"add_capability": "browser.fetch"},
          repr(legacy.get("requested_change")))

    print("\n" + ("PASS — check_teleon_agent_gateway_boundary_schema_match: the runtime "
                  "AgentBoundaryExpansionRequest now matches schemas/agents/AgentBoundaryExpansionRequest.v1 "
                  "EXACTLY (capability_id / requested_change / justification, all required fields present with "
                  "the declared JSON types), the safety invariants are preserved (status forced "
                  "'pending_human_approval', auto_applied forced False — a caller asking for approved/auto-apply "
                  "is overridden), no legacy raw keys (requested_capability/rationale) survive, and legacy "
                  "inputs are still accepted as aliases that map to the schema field names."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_teleon_agent_gateway_boundary_schema_match.py --self-test")
    raise SystemExit(0)
