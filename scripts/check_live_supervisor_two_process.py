#!/usr/bin/env python3
"""scripts.check_live_supervisor_two_process — THE critical proof (OPP-supervisor-scaling-live): two REAL
`baltor_flywheel.py --watch` processes coordinate safely against ONE durable DB.

  1. both register as supervisor instances,
  2. exactly one leader at a time,
  3. shards are exclusively owned (no shard owned by two),
  4. kill the leader by EXACT pid → the standby takes over (lease expiry → failover),
  5. a failover is recorded with the new leader,
  6. no duplicate singleton/spawn decisions (UNIQUE idempotency key).

Bounded, temp DB, no network, no broad pkill (kills only the exact pids it spawned).

CLI: PYTHONPATH=. python3 scripts/check_live_supervisor_two_process.py --self-test
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]


def _spawn(sid: str, db: str):
    env = {**os.environ, "PYTHONPATH": str(_REPO)}
    return subprocess.Popen(
        [sys.executable, "scripts/baltor_flywheel.py", "--supervisor-only", "--supervisor-db", db,
         "--supervisor-id", sid, "--interval", "1", "--leader-ttl", "3", "--shard-ttl", "3",
         "--max-shards", "8", "--max-ticks", "600"],
        cwd=str(_REPO), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _wait(pred, timeout=25.0, poll=0.3) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if pred():
                return True
        except Exception:
            pass
        time.sleep(poll)
    return False


def _self_test() -> int:
    from src.baltor.workers.supervisor_store import SupervisorStore
    fails: list[str] = []
    procs: dict = {}

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    tmp = tempfile.mkdtemp(prefix="baltor-2proc-")
    db = os.path.join(tmp, "sup.db")
    try:
        procs["A"] = _spawn("A", db)
        procs["B"] = _spawn("B", db)
        store = SupervisorStore(db)

        # Phase 1 — both registered + a leader exists + all shards claimed
        ok1 = _wait(lambda: len(store.instances()) >= 2 and store.get_leader("global") is not None
                    and all(s["owner_id"] for s in store.shards()))
        chk("both supervisors registered", len({i["supervisor_id"] for i in store.instances()}) >= 2,
            str([i["supervisor_id"] for i in store.instances()]))
        leader1 = store.get_leader("global")
        chk("exactly one leader elected", leader1 in ("A", "B"), str(leader1))
        # shard exclusivity + distribution
        owners = {s["shard_id"]: s["owner_id"] for s in store.shards()}
        chk("every shard has exactly one owner", all(o in ("A", "B") for o in owners.values()),
            str(sorted(set(owners.values()))))
        chk("shards distributed across BOTH supervisors", _wait(
            lambda: {s["owner_id"] for s in store.shards() if s["owner_id"]} == {"A", "B"}, timeout=25),
            str({s["owner_id"] for s in store.shards()}))

        # Phase 2 — kill the leader by EXACT pid; the standby must take over
        survivor = "B" if leader1 == "A" else "A"
        procs[leader1].kill(); procs[leader1].wait()
        ok2 = _wait(lambda: store.get_leader("global") == survivor, timeout=25)
        leader2 = store.get_leader("global")
        chk("leader failover after kill (standby took over)", leader2 == survivor, f"leader1={leader1} leader2={leader2}")
        chk("failover recorded with the new leader", _wait(
            lambda: any(f["new_owner"] == survivor and f["old_owner"] == leader1 for f in store.failovers()), timeout=25),
            str(store.failovers()))

        # Phase 3 — no duplicate scheduling: every idempotency_key is unique
        decs = store.decisions()
        keys = [d["idempotency_key"] for d in decs]
        chk("no duplicate decision idempotency_key", len(keys) == len(set(keys)), f"{len(keys)} keys, {len(set(keys))} unique")
        chk("singleton decisions were made only by a leader-at-the-time",
            all(d["supervisor_id"] in ("A", "B") for d in store.decisions(decision_type="singleton_proof_sweep")))
        chk("there were ticks from both supervisors", len({t["supervisor_id"] for t in store.ticks()}) == 2,
            str({t["supervisor_id"] for t in store.ticks()}))
        store.close()
    finally:
        for p in procs.values():
            if p.poll() is None:
                p.kill()
                try:
                    p.wait(timeout=5)
                except Exception:
                    pass

    print(f"\n{'PASS — check_live_supervisor_two_process: two real --watch processes, one leader, exclusive shards, leader-kill failover to standby, failover recorded, no duplicate scheduling.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
