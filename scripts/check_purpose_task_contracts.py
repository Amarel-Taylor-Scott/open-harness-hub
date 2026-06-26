#!/usr/bin/env python3
"""scripts.check_purpose_task_contracts — PROOF: the PurposeTaskSpec contract is real + governs the PurposeTask PoC.

Asserts: the schema loads; a valid spec validates; invalid specs FAIL (missing required · bad schema_version
enum · wrong type); the contract registry covers PurposeTaskSpec; and a PROVISIONED PoC spec (from
src.baltor.purpose_tasks.provision) validates against the contract — so what the PoC actually runs is contract-bound.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from scripts.runtime import schema_validator as sv
from src.baltor import purpose_tasks as ct

_REF = "purpose_tasks/PurposeTaskSpec"
_NOW = "2026-06-06T00:00:00Z"


def _valid_spec():
    return {
        "schema_version": "PurposeTaskSpec",
        "task_id": "purpose_tasks.demo@v1",
        "purpose": "Pull X from a source.",
        "capability_slot": "fetch_demo",
        "input_contract": "DemoQuery",
        "output_contract": "DemoRecord",
        "success_criteria": {"max_cost": 5.0, "min_source_handles": 1},
        "promotion_criteria": {"cost_tolerance": 0.0},
        "connected_to": ["demo.consumer"],
        "defined_at": _NOW,
    }


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # schema loads
    try:
        schema = sv.load_schema(_REF)
        check("PurposeTaskSpec schema loads", schema.get("$id") == _REF)
    except Exception as e:
        check("PurposeTaskSpec schema loads", False, str(e)); schema = {}

    # valid spec validates
    check("a valid PurposeTaskSpec validates (no errors)", sv.validate_ref(_valid_spec(), _REF) == [],
          str(sv.validate_ref(_valid_spec(), _REF)[:3]))

    # invalid specs FAIL
    missing = _valid_spec(); del missing["capability_slot"]
    check("missing required field FAILS validation", sv.validate_ref(missing, _REF) != [])
    badver = _valid_spec(); badver["schema_version"] = "NotAPurposeTaskSpec"
    check("bad schema_version enum FAILS validation", sv.validate_ref(badver, _REF) != [])
    badtype = _valid_spec(); badtype["success_criteria"] = "not-an-object"
    check("wrong type (success_criteria) FAILS validation", sv.validate_ref(badtype, _REF) != [])

    # registry covers it
    reg = json.loads((Path(_REPO) / "architecture" / "contract_registry.json").read_text())
    names = {(e.get("name"), e.get("version")) for v in reg.values() if isinstance(v, list) for e in v if isinstance(e, dict)}
    check("contract registry covers PurposeTaskSpec v1", ("PurposeTaskSpec", "v1") in names)

    # the PROVISIONED PoC spec is contract-valid (what the PoC actually runs)
    poc_reg = {"fetch_demo": [
        {"impl_id": "impl.a", "priority": 70, "handler": lambda _i: {"output": {}, "output_contract": "DemoRecord", "cost": 1.0, "source_handles": ["h"]}},
        {"impl_id": "impl.b", "priority": 60, "handler": lambda _i: {"output": {}, "output_contract": "DemoRecord", "cost": 1.0, "source_handles": ["h"]}},
    ]}
    provisioned = ct.provision(_valid_spec(), poc_reg)
    errs = sv.validate_ref(provisioned, _REF)
    check("a PROVISIONED PurposeTask spec validates (current_impl_id/alternatives/rollback_target are contract-shaped)",
          errs == [], str(errs[:3]))

    print("\n" + ("PASS — check_purpose_task_contracts: PurposeTaskSpec is a real, registered contract; valid specs "
                  "pass, invalid specs fail, and the provisioned PoC spec is contract-bound."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_purpose_task_contracts.py --self-test")
    raise SystemExit(0)
