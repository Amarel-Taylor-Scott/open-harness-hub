#!/usr/bin/env python3
"""scripts.check_flywheel_supervisor_shards — proof (C-FLEET-3): high-volume scan work shards across
supervisors. Different supervisors claim different shards; a supervisor cannot claim a shard another
already owns; a stale shard lease is reclaimable and re-claimable by a third supervisor.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_flywheel_supervisor_shards.py --self-test
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
    for sid, st in [("shard:browser", "capability"), ("shard:ingest", "capability"), ("shard:verify", "capability")]:
        L.register_shard(shard_id=sid, shard_type=st, shard_key=sid.split(":")[1])

    chk("A claims browser shard", L.claim_shard(shard_id="shard:browser", owner_id="A", now=T0, ttl_seconds=30))
    chk("B claims ingest shard", L.claim_shard(shard_id="shard:ingest", owner_id="B", now=T0, ttl_seconds=30))
    chk("B cannot claim A's shard", L.claim_shard(shard_id="shard:browser", owner_id="B", now=_plus_s(T0, 5)) is False)
    chk("A owns exactly its shard", [s["shard_id"] for s in L.shards_owned_by("A", now=_plus_s(T0, 5))] == ["shard:browser"])
    chk("shards distribute across supervisors",
        {s["shard_id"] for s in L.shards_owned_by("A", now=_plus_s(T0, 5))} != {s["shard_id"] for s in L.shards_owned_by("B", now=_plus_s(T0, 5))})

    # A keeps its shard via heartbeat; B's goes stale (no heartbeat) past ttl
    chk("A heartbeats its shard", L.heartbeat_shard(shard_id="shard:browser", owner_id="A", now=_plus_s(T0, 20), ttl_seconds=30))
    t_stale = _plus_s(T0, 31)
    reclaimed = L.reclaim_stale_shards(now=t_stale)
    chk("only the stale (un-heartbeated) shard is reclaimed", reclaimed == ["shard:ingest"], str(reclaimed))
    chk("A's heartbeated shard is NOT reclaimed", "shard:browser" not in reclaimed)

    # a third supervisor claims the reclaimed shard
    chk("C claims the reclaimed shard", L.claim_shard(shard_id="shard:ingest", owner_id="C", now=t_stale, ttl_seconds=30))
    chk("ingest now owned by C", [s["shard_id"] for s in L.shards_owned_by("C", now=t_stale)] == ["shard:ingest"])

    print(f"\n{'PASS — check_flywheel_supervisor_shards: shards distribute, no double-ownership, stale lease reclaimed + re-claimable, heartbeated shard retained.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
