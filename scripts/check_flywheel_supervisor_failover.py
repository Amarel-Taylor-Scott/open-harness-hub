#!/usr/bin/env python3
"""scripts.check_flywheel_supervisor_failover — proof (C-FLEET-3): if the leader dies (stops renewing),
its lease expires and a standby takes over — but NOT before expiry. Singleton duties never run twice.

CLI: PYTHONPATH=. python3 scripts/check_flywheel_supervisor_failover.py --self-test
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
    L.acquire_lease(lease_name="global", owner_id="A", now=T0, ttl_seconds=30)

    # before expiry, the standby cannot take over
    chk("standby blocked before expiry", L.acquire_lease(lease_name="global", owner_id="B", now=_plus_s(T0, 20)) is False)
    chk("A still leader before expiry", L.is_leader(lease_name="global", owner_id="A", now=_plus_s(T0, 20)))

    # A dies (no renew). After ttl, the lease is unheld.
    t_after = _plus_s(T0, 31)
    chk("expired lease has no holder", L.lease_holder("global", now=t_after) is None)
    chk("standby acquires after expiry (failover)", L.acquire_lease(lease_name="global", owner_id="B", now=t_after, ttl_seconds=30))
    chk("B is now leader", L.is_leader(lease_name="global", owner_id="B", now=t_after))
    chk("the dead leader is no longer leader", L.is_leader(lease_name="global", owner_id="A", now=t_after) is False)
    # the recovered A cannot reclaim while B holds
    chk("recovered A cannot steal back while B holds", L.acquire_lease(lease_name="global", owner_id="A", now=_plus_s(T0, 40)) is False)

    print(f"\n{'PASS — check_flywheel_supervisor_failover: standby blocked before expiry, takes over after, dead leader demoted, no double leadership.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
