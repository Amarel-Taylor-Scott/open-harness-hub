#!/usr/bin/env python3
"""scripts.check_live_supervisor_shards — proof (OPP-supervisor-scaling-live): DURABLE shard leases are
exclusive, distribute across supervisors, reclaim stale leases, renew for owner only, and persist.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_live_supervisor_shards.py --self-test
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from src.baltor.workers.supervisor_store import SupervisorStore


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    tmp = tempfile.mkdtemp(prefix="baltor-sup-shard-")
    s = SupervisorStore(Path(tmp) / "sup.db")
    s.ensure_default_shards(now=100)
    n_shards = len(s.shards())
    chk("default shards created", n_shards >= 14, str(n_shards))

    # A claims up to 7, B claims ALL the rest → exclusive split
    a = s.claim_available_shards(supervisor_id="A", max_shards=7, ttl_seconds=30, now=100)
    b = s.claim_available_shards(supervisor_id="B", max_shards=n_shards, ttl_seconds=30, now=100)
    chk("A claimed 7", len(a) == 7, str(len(a)))
    chk("B claimed the remaining", len(b) == n_shards - 7, str(len(b)))
    chk("no shard owned by both", set(a).isdisjoint(set(b)))
    owners = {r["shard_id"]: r["owner_id"] for r in s.shards()}
    chk("every claimed shard has exactly one owner", all(owners[x] == "A" for x in a) and all(owners[x] == "B" for x in b))

    # non-owner cannot renew; owner can
    chk("B cannot renew A's shard", s.renew_shards(supervisor_id="B", shard_ids=a[:1], ttl_seconds=30, now=110) == 0)
    chk("A renews its shard", s.renew_shards(supervisor_id="A", shard_ids=a[:1], ttl_seconds=30, now=110) == 1)
    chk("non-owner cannot claim a held shard", s.claim_shard(shard_id=a[0], supervisor_id="B", ttl_seconds=30, now=120) is False)

    # A dies: its shards go stale by now=200 (>130). expire_stale_shards reclaims them.
    reclaimed = s.expire_stale_shards(now=200)
    chk("stale shards (A's) reclaimed", set(a) <= set(reclaimed), str(reclaimed))
    # B still holds (renew keeps it alive); a third supervisor C claims a reclaimed shard
    s.renew_shards(supervisor_id="B", shard_ids=b, ttl_seconds=30, now=200)
    chk("C claims a reclaimed shard", s.claim_shard(shard_id=a[0], supervisor_id="C", ttl_seconds=30, now=200))
    chk("reclaimed shard now owned by C", {r["owner_id"] for r in s.shards() if r["shard_id"] == a[0]} == {"C"})
    s.close()

    # persistence
    s2 = SupervisorStore(Path(tmp) / "sup.db")
    chk("shard ownership persists across reopen", a[0] in [x["shard_id"] for x in s2.shards()])
    s2.close()
    print(f"\n{'PASS — check_live_supervisor_shards: durable exclusive shard leases, distribution, owner-only renew, stale reclaim + re-claim, persistence.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
