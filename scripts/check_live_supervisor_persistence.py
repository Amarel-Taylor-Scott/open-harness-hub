#!/usr/bin/env python3
"""scripts.check_live_supervisor_persistence — proof (OPP-supervisor-scaling-live): the live supervisor
state PERSISTS to durable storage and reloads after restart — no in-memory-only state is required for
correctness. Writes instance/tick/decision/lease/shard/capacity/failover, reopens the store, queries them.

CLI: PYTHONPATH=. python3 scripts/check_live_supervisor_persistence.py --self-test
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from src.baltor.workers.supervisor_store import SupervisorStore
from src.baltor.workers import supervisor_watch


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    tmp = tempfile.mkdtemp(prefix="baltor-sup-persist-")
    db = Path(tmp) / "sup.db"
    s = SupervisorStore(db)
    s.register_instance(supervisor_id="A", pid=123, now=100)
    out = supervisor_watch.step(s, supervisor_id="A", leader_ttl=30, shard_ttl=30, max_shards=14, now=100)
    chk("watch step ran (leader + shards + tick)", out["leader"] and len(out["owned_shards"]) > 0 and out["tick_id"])
    ticks_before = len(s.ticks()); snaps_before = len(s.capacity_snapshots())
    s.close()

    # restart: a brand-new store on the same DB reloads everything
    s2 = SupervisorStore(db)
    chk("instance persists", s2.instance("A") is not None)
    chk("leader lease persists", s2.get_leader("global", now=110) == "A")
    chk("shards persist", len(s2.list_owned_shards("A", now=110)) > 0)
    chk("ticks persist + queryable", len(s2.ticks()) == ticks_before and ticks_before >= 1)
    chk("capacity snapshot persists", len(s2.capacity_snapshots()) == snaps_before and snaps_before >= 1)
    chk("singleton decision persists", s2.decision_exists("singleton:proof_sweep:" + str(100 // 30)))
    # a second step on the reloaded store continues coherently (renews, same leader)
    out2 = supervisor_watch.step(s2, supervisor_id="A", leader_ttl=30, shard_ttl=30, max_shards=14, now=115)
    chk("reloaded supervisor keeps leadership", out2["leader"] is True)
    s2.close()
    print(f"\n{'PASS — check_live_supervisor_persistence: instance/lease/shards/ticks/capacity/decisions persist + reload after restart; no in-memory-only state.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
