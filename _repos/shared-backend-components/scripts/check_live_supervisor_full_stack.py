#!/usr/bin/env python3
"""scripts.check_live_supervisor_full_stack — master proof (OPP-supervisor-scaling-live). Prints the
CAPABILITY | STATUS | PROOF | NOTES table and verifies (a) every dedicated proof is REGISTERED in the
flywheel PROOF_MODULES (so the suite actually runs it — including the heavy two-process + API proofs,
without this master re-running them), and (b) a quick in-process two-supervisor composition smoke holds.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_live_supervisor_full_stack.py --self-test
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from scripts.baltor_flywheel import PROOF_MODULES
from src.baltor.workers.supervisor_store import SupervisorStore
from src.baltor.workers import supervisor_watch

_ROWS = [
    ("schema", "check_live_supervisor_schema", "8 durable coordination tables + UNIQUE keys"),
    ("leader lease", "check_live_supervisor_leader_lease", "single leader, renew, failover+generation"),
    ("shard lease", "check_live_supervisor_shards", "exclusive, distribute, stale reclaim"),
    ("idempotent decisions", "check_live_supervisor_idempotent_decisions", "UNIQUE key — no duplicate work"),
    ("spawn decisions", "check_live_supervisor_spawn_decisions", "live tick calls spawn-decision; dedup; SLA-aware"),
    ("flywheel watch integration", "check_flywheel_watch_uses_supervisor_leases", "--watch USES the leases"),
    ("two-process failover", "check_live_supervisor_two_process", "kill leader → standby takes over"),
    ("live dispatch (spawn/drain)", "check_live_supervisor_dispatch", "--watch --dispatch spawns a real worker that drains the durable queue"),
    ("persistence", "check_live_supervisor_persistence", "reload after restart; no memory-only state"),
    ("API projection", "check_live_supervisor_api", "/api/fleet/* served read-only"),
    ("UI projection", "check_live_supervisor_ui", "/fleet projection-only page"),
    ("redteam", "check_live_supervisor_redteam", "10 attacks fail safely"),
    ("regressions", "check_worker_fleet_supervisor_full_stack", "offline fleet supervisor stays green"),
]


def _self_test() -> int:
    fails: list[str] = []
    registered = {name for _, name in PROOF_MODULES}

    def chk(name, ok, detail=""):
        if not ok:
            fails.append(name)
        return ok

    # composition smoke: two supervisors over one durable store — one leader, shards split, no dup decisions
    tmp = tempfile.mkdtemp(prefix="baltor-sup-fullstack-")
    s = SupervisorStore(Path(tmp) / "sup.db")
    s.register_instance(supervisor_id="A", now=1000); s.register_instance(supervisor_id="B", now=1000)
    a = supervisor_watch.step(s, supervisor_id="A", leader_ttl=300, shard_ttl=300, max_shards=7, now=1000)
    b = supervisor_watch.step(s, supervisor_id="B", leader_ttl=300, shard_ttl=300, max_shards=7, now=1000)
    smoke_leader = (a["leader"] is True and b["leader"] is False)
    smoke_split = set(a["owned_shards"]).isdisjoint(set(b["owned_shards"])) and len(a["owned_shards"]) > 0 and len(b["owned_shards"]) > 0
    smoke_nodup = len({d["idempotency_key"] for d in s.decisions()}) == len(s.decisions())
    s.close()
    chk("composition smoke: single leader", smoke_leader)
    chk("composition smoke: shards split exclusively", smoke_split)
    chk("composition smoke: no duplicate decisions", smoke_nodup)

    print("CAPABILITY | STATUS | PROOF | NOTES")
    for cap, proof, notes in _ROWS:
        ok = proof in registered
        if not ok:
            fails.append(f"{cap}:{proof} not registered")
        print(f"  {cap} | {'GREEN' if ok else 'RED'} | {proof} | {notes}")

    smoke = "GREEN" if (smoke_leader and smoke_split and smoke_nodup) else "RED"
    print(f"  composition-smoke | {smoke} | (in-process) | two supervisors, one leader, shards split, no dup")
    print(f"\n{'PASS — check_live_supervisor_full_stack: all capability proofs registered in the flywheel + two-supervisor composition smoke green.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
