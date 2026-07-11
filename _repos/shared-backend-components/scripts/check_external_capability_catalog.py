#!/usr/bin/env python3
"""scripts.check_external_capability_catalog — proof (C35): the External Capability Catalog is well-formed and
builds ON data/backend-tools.yaml. Every slot has the required fields + valid status/health; the 13 verified
backend-tool keys are all represented; the self-evolving-agent slots (eval_harness/code_review/skill_memory =
adoptable, agent_runtime = foil, self_improvement_research = reference) are present; foil/reference cards carry
a do-not-adopt-as-runtime note; and the catalog declares its owning registry.

CLI: python3 _repos/shared-backend-components/scripts/check_external_capability_catalog.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from src.baltor.runtime.registry.capability_registry import CapabilityRegistry  # noqa: E402

#: self-evolving-agent slots earned from research/external-tools/self-evolving-coding-agents.md
_SELF_EVOLVING = {"eval_harness": "active", "code_review": "active", "skill_memory": "candidate",
                  "agent_runtime": "foil", "self_improvement_research": "reference"}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    reg = CapabilityRegistry()

    problems = reg.validate_catalog()
    check("catalog passes structural validation (fields/status/health/foil-notes)", problems == [], str(problems[:6]))

    uncovered = reg.covers_backend_tool_keys()
    check("all 13 backend-tools.yaml capability keys are represented as slots", uncovered == [], str(uncovered))

    slots = set(reg.slot_names())
    missing_se = [s for s in _SELF_EVOLVING if s not in slots]
    check("the self-evolving-agent slots are present", missing_se == [], str(missing_se))
    bad_se_status = [f"{s}={reg.get_by_capability_slot(s)['status']}!={want}"
                     for s, want in _SELF_EVOLVING.items() if s in slots and reg.get_by_capability_slot(s)["status"] != want]
    check("self-evolving slots carry the intended status (foil/reference/adoptable)", bad_se_status == [], str(bad_se_status))

    # the foil/reference slots must declare do-not-adopt-as-runtime on every card (validate_catalog enforces too)
    foil = reg.get_by_capability_slot("agent_runtime")
    check("agent_runtime is a FOIL with do-not-adopt cards",
          foil["status"] == "foil" and all(a.get("do_not_adopt_as_runtime") for a in foil["adapters"]))

    from src.baltor.runtime.registry.capability_registry import load_catalog
    catalog = load_catalog()
    check("catalog declares its owning registry", catalog.get("owner_registry") == "_repos/baltor/backend/src/baltor/runtime/registry/capability_registry.py")
    check("catalog declares approved adapter paths", len(catalog.get("approved_adapter_paths", [])) >= 1)
    check("every adoptable slot ships a working stub adapter (stdlib-only runtime)",
          all(any(a.get("role") == "stub" for a in s["adapters"]) for s in reg.slots() if s["status"] in ("active", "candidate")))

    print(f"\n{'PASS — check_external_capability_catalog: catalog valid, builds on the 13 backend-tool keys, self-evolving slots present, foils flagged, registry-owned.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: external capability catalog.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
