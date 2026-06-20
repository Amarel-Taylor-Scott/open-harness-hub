#!/usr/bin/env python3
"""scripts.check_provider_replacement_matrix — proof (C35): the replacement matrix covers exactly the catalog
slots, and every adoptable (active|candidate) slot declares a primary candidate + a fallback-or-stub + at least
one contract test. This is replaceability made into a failing check: if an upstream repo dies, the documented
swap path (with a stub that keeps the system running) already exists. foil/reference slots are exempt.

CLI: python3 scripts/check_provider_replacement_matrix.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from src.baltor.runtime.registry.capability_registry import CapabilityRegistry, load_matrix  # noqa: E402

_EXEMPT = {"foil", "reference"}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    reg = CapabilityRegistry()
    matrix = load_matrix()
    matrix_slots = {m["capability_slot"] for m in matrix["slots"]}
    catalog_slots = set(reg.slot_names())
    check("matrix covers exactly the catalog slots (no drift)", matrix_slots == catalog_slots,
          f"only-in-matrix={matrix_slots - catalog_slots} only-in-catalog={catalog_slots - matrix_slots}")

    # the matrix declares the rule for adoptable slots
    no_primary, no_alt, no_test, exempt_wrong = [], [], [], []
    by_slot = {m["capability_slot"]: m for m in matrix["slots"]}
    for s in reg.slots():
        m = by_slot.get(s["capability_slot"], {})
        if s["status"] in _EXEMPT:
            if not m.get("exempt"):
                exempt_wrong.append(s["capability_slot"])
            continue
        if not m.get("primary"):
            no_primary.append(s["capability_slot"])
        if not m.get("fallback_or_stub"):
            no_alt.append(s["capability_slot"])
        if not m.get("contract_tests"):
            no_test.append(s["capability_slot"])
    check("every adoptable slot has a primary candidate", no_primary == [], str(no_primary))
    check("every adoptable slot has a fallback-or-stub", no_alt == [], str(no_alt))
    check("every adoptable slot has >=1 contract test", no_test == [], str(no_test))
    check("foil/reference slots are marked exempt in the matrix", exempt_wrong == [], str(exempt_wrong))

    # cross-check against the catalog itself: each adoptable slot has a stub adapter + a primary/fallback adapter
    cat_no_stub, cat_no_alt = [], []
    for s in reg.slots():
        if s["status"] in _EXEMPT:
            continue
        roles = [a.get("role") for a in s["adapters"]]
        if "stub" not in roles:
            cat_no_stub.append(s["capability_slot"])
        if "primary" not in roles and "fallback" not in roles:
            cat_no_alt.append(s["capability_slot"])
    check("catalog: every adoptable slot ships a stub adapter", cat_no_stub == [], str(cat_no_stub))
    check("catalog: every adoptable slot ships a primary/fallback adapter", cat_no_alt == [], str(cat_no_alt))

    print(f"\n{'PASS — check_provider_replacement_matrix: matrix == catalog slots; every adoptable slot has primary + fallback/stub + a contract test; foils exempt.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: provider replacement matrix.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
