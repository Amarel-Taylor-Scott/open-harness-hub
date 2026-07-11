#!/usr/bin/env python3
"""scripts.check_repo_health_policy — proof (C35): the repo health policy is well-formed and the catalog obeys
it. Health/adoption enums are declared; monitored signals carry thresholds + actions; quarantine triggers and
a review cadence exist; every adapter card's health_status is in the enum; and the load-bearing invariant holds
— an active/candidate slot is never wired to a decayed/archived adapter.

CLI: python3 _repos/shared-backend-components/scripts/check_repo_health_policy.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from src.baltor.runtime.registry.capability_registry import CapabilityRegistry, load_health_policy  # noqa: E402


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    pol = load_health_policy()
    health_enum = set(pol.get("health_status_enum", []))
    adopt_enum = set(pol.get("adoption_status_enum", []))
    check("health_status_enum + adoption_status_enum declared", len(health_enum) >= 4 and len(adopt_enum) >= 6)
    check("review_cadence_days is a positive number", isinstance(pol.get("review_cadence_days"), int) and pol["review_cadence_days"] > 0)

    sigs = pol.get("monitored_signals", [])
    check("monitored signals declare signal + thresholds + action",
          len(sigs) >= 4 and all({"signal", "action"} <= set(s) and ("warn_threshold" in s or "fail_threshold" in s) for s in sigs),
          str([s.get("signal") for s in sigs if not ({"signal", "action"} <= set(s))]))
    check("quarantine triggers declared (archived/relicense/abandonment)", len(pol.get("quarantine_triggers", [])) >= 3)
    check("invariants are documented", len(pol.get("invariants", [])) >= 3)

    reg = CapabilityRegistry()
    bad_health, bad_status, wired_decayed = [], [], []
    for s in reg.slots():
        if s["status"] not in adopt_enum:
            bad_status.append(f"{s['capability_slot']}={s['status']}")
        for a in s["adapters"]:
            if a.get("health_status") not in health_enum:
                bad_health.append(f"{s['capability_slot']}/{a.get('adapter_id')}={a.get('health_status')}")
            if a.get("status") not in adopt_enum:
                bad_status.append(f"{s['capability_slot']}/{a.get('adapter_id')}={a.get('status')}")
        if s["status"] in ("active", "candidate"):
            wired = next((a for a in s["adapters"] if a.get("adapter_id") == s.get("adapter_id")), None)
            if wired and wired.get("health_status") in ("decayed", "archived"):
                wired_decayed.append(f"{s['capability_slot']}->{wired.get('health_status')}")
    check("every adapter health_status is in the policy enum", bad_health == [], str(bad_health[:6]))
    check("every slot/adapter adoption status is in the policy enum", bad_status == [], str(bad_status[:6]))
    check("no active/candidate slot is wired to a decayed/archived adapter (the load-bearing invariant)", wired_decayed == [], str(wired_decayed))

    print(f"\n{'PASS — check_repo_health_policy: policy well-formed; every adapter health is governed; no active slot rides a decayed/archived repo.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: repo health policy.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
