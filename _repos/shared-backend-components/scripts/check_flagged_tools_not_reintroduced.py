#!/usr/bin/env python3
"""scripts.check_flagged_tools_not_reintroduced — proof (C35): the do-not-reintroduce names from the verified
seed (data/backend-tools.yaml `flagged:` block — the single source) never appear as an ADOPTED adapter
(primary/fallback/stub) in the capability catalog, and the catalog's quarantined_providers list mirrors that
flagged block exactly (a drift check). Self-evolving multi-agent runtimes are recorded as FOILS, not deps.

This is the verify-first rule turned into a wall: a hallucinated/decayed/mislabeled tool cannot sneak back in.

CLI: python3 _repos/shared-backend-components/scripts/check_flagged_tools_not_reintroduced.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from src.baltor.runtime.registry.capability_registry import CapabilityRegistry, flagged_tool_names, load_catalog  # noqa: E402


def _base(name: str) -> str:
    return name.split("(")[0].strip().lower()


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    flagged = flagged_tool_names()
    check("the verified seed lists the flagged do-not-reintroduce tools", len(flagged) >= 6, str(flagged))

    reg = CapabilityRegistry()
    adopted = reg.adopted_flagged_tools()
    check("no flagged tool appears as an adopted (primary/fallback/stub) adapter", adopted == [], str(adopted))

    # the catalog records the rejection explicitly and mirrors the seed (no drift)
    catalog = load_catalog()
    quarantined = catalog.get("quarantined_providers", [])
    q_names = {_base(q.get("name", "")) for q in quarantined}
    f_names = {_base(n) for n in flagged}
    check("quarantined_providers mirrors the flagged block exactly (no drift)", q_names == f_names,
          f"only-in-catalog={q_names - f_names} only-in-seed={f_names - q_names}")
    check("every quarantined provider records a reason", all(q.get("reason") for q in quarantined))

    # the self-evolving multi-agent runtimes are kept as FOILS (research positioning), never adopted
    foil = reg.get_by_capability_slot("agent_runtime")
    check("self-evolving agent runtimes are recorded as a FOIL slot (do-not-adopt)",
          foil["status"] == "foil" and all(a.get("do_not_adopt_as_runtime") for a in foil["adapters"]))

    print(f"\n{'PASS — check_flagged_tools_not_reintroduced: no flagged tool is adopted; quarantined_providers mirrors the verified seed; self-evolving runtimes stay foils.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: flagged tools not reintroduced.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
