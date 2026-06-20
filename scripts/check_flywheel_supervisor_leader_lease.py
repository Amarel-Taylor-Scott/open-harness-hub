#!/usr/bin/env python3
"""scripts.check_flywheel_supervisor_leader_lease — proof (C-FLEET-3): the leader lease admits exactly one
holder for a singleton duty. Acquire succeeds for the first supervisor; a second cannot acquire while the
lease is held; the holder can renew; the holder query is accurate.

CLI: PYTHONPATH=. python3 scripts/check_flywheel_supervisor_leader_lease.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.workers.fleet_ledger import _plus_s
from src.baltor.workers.supervisor_ledger import SupervisorLedger

T0 = "2026-06-06T00:00:00Z"


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    L = SupervisorLedger()
    L.register_instance(supervisor_id="A", now=T0)
    L.register_instance(supervisor_id="B", now=T0)

    chk("first supervisor acquires the leader lease", L.acquire_lease(lease_name="global", owner_id="A", now=T0, ttl_seconds=30))
    chk("holder is A", L.lease_holder("global", now=T0) == "A")
    chk("A is leader", L.is_leader(lease_name="global", owner_id="A", now=T0))

    t10 = _plus_s(T0, 10)
    chk("second supervisor cannot acquire while held", L.acquire_lease(lease_name="global", owner_id="B", now=t10) is False)
    chk("B is not leader", L.is_leader(lease_name="global", owner_id="B", now=t10) is False)
    chk("A renews its lease", L.renew_lease(lease_name="global", owner_id="A", now=t10, ttl_seconds=30))
    chk("B still cannot acquire after A renewed", L.acquire_lease(lease_name="global", owner_id="B", now=_plus_s(T0, 20)) is False)
    chk("only one holder ever", L.lease_holder("global", now=_plus_s(T0, 20)) == "A")

    print(f"\n{'PASS — check_flywheel_supervisor_leader_lease: exactly one leader; second blocked while held; holder renews; holder query accurate.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
