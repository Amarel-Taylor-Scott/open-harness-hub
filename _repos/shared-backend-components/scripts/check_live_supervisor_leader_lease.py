#!/usr/bin/env python3
"""scripts.check_live_supervisor_leader_lease — proof (OPP-supervisor-scaling-live): the DURABLE leader
lease admits exactly one holder, blocks a standby while held, lets the holder renew, fails over to the
standby after expiry (recording a failover + bumping generation), and refuses the dead leader's renew.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_live_supervisor_leader_lease.py --self-test
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from src.baltor.workers.supervisor_store import SupervisorStore

L = "global"


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    tmp = tempfile.mkdtemp(prefix="baltor-sup-lease-")
    s = SupervisorStore(Path(tmp) / "sup.db")

    chk("A claims the leader lease", s.try_claim_leader(lease_name=L, supervisor_id="A", ttl_seconds=30, now=100))
    chk("A is leader", s.get_leader(L, now=100) == "A")
    chk("B blocked while A holds", s.try_claim_leader(lease_name=L, supervisor_id="B", ttl_seconds=30, now=110) is False)
    chk("A renews (try_claim acts as renew for owner)", s.try_claim_leader(lease_name=L, supervisor_id="A", ttl_seconds=30, now=110))
    chk("renew_leader works for owner", s.renew_leader(lease_name=L, supervisor_id="A", ttl_seconds=30, now=115))
    chk("renew_leader fails for non-owner", s.renew_leader(lease_name=L, supervisor_id="B", ttl_seconds=30, now=120) is False)

    # A dies (no renew). At now=200, lease (until ~145) is expired.
    chk("expired lease has no holder", s.get_leader(L, now=200) is None)
    chk("B takes over after expiry (failover)", s.try_claim_leader(lease_name=L, supervisor_id="B", ttl_seconds=30, now=200))
    chk("B is now leader", s.get_leader(L, now=200) == "B")
    chk("dead leader A cannot renew", s.renew_leader(lease_name=L, supervisor_id="A", ttl_seconds=30, now=205) is False)
    chk("dead leader A cannot reclaim while B holds", s.try_claim_leader(lease_name=L, supervisor_id="A", ttl_seconds=30, now=205) is False)

    fos = s.failovers()
    chk("failover recorded with new_owner=B", any(f["new_owner"] == "B" and f["old_owner"] == "A" for f in fos), str(fos))
    chk("generation incremented on takeover", any(f["generation"] >= 2 for f in fos))

    # release lets a fresh claim succeed
    s.release_leader(lease_name=L, supervisor_id="B")
    chk("after release, leader is free", s.get_leader(L, now=210) is None)
    chk("A can claim after release", s.try_claim_leader(lease_name=L, supervisor_id="A", ttl_seconds=30, now=210))
    s.close()

    # persistence across reopen: the lease survives a new connection
    s2 = SupervisorStore(Path(tmp) / "sup.db")
    chk("lease persists across reopen", s2.get_leader(L, now=215) == "A")
    s2.close()

    print(f"\n{'PASS — check_live_supervisor_leader_lease: durable single-leader, standby blocked, renew, failover+generation+record, dead-leader refused, persists across reopen.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
