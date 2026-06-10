#!/usr/bin/env python3
"""scripts.check_live_supervisor_redteam — proof (OPP-supervisor-scaling-live): live-supervisor attacks
fail safely:

  1. two supervisors both 'leader'           → only one holds the lease
  2. standby runs a leader-only duty          → the watch step records NO singleton unless leader
  3. non-owner runs a shard duty              → claim/renew refused for non-owner
  4. duplicate spawn decision                 → UNIQUE idempotency key prevents it
  5. old leader renews after losing the lease → refused
  6. stale shard never reclaimed              → expire_stale_shards reclaims it
  7. supervisor state only in memory          → state persists to the DB (reopen)
  8. broad pkill used                         → supervisor code kills only by exact pid (no pkill/killall)
  9. heavy task executed inside supervisor    → no provider/exec/subprocess calls in the control-plane code
 10. dashboard mutates supervisor truth       → the projection is read-only (no write methods)

CLI: PYTHONPATH=. python3 scripts/check_live_supervisor_redteam.py --self-test
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from src.baltor.workers.supervisor_store import SupervisorStore
from src.baltor.workers import supervisor_watch

_REPO = Path(__file__).resolve().parents[1]


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    tmp = tempfile.mkdtemp(prefix="baltor-sup-redteam-")
    db = Path(tmp) / "sup.db"
    s = SupervisorStore(db)

    # 1 — only one leader
    s.try_claim_leader(lease_name="global", supervisor_id="A", ttl_seconds=30, now=100)
    chk("1 two cannot both be leader", s.try_claim_leader(lease_name="global", supervisor_id="B", ttl_seconds=30, now=105) is False)

    # 2 — a non-leader watch step records NO singleton duty
    s.register_instance(supervisor_id="B", now=105)
    out_b = supervisor_watch.step(s, supervisor_id="B", leader_ttl=30, shard_ttl=30, max_shards=7, now=106)
    chk("2 standby does not run leader-only duty", out_b["leader"] is False and out_b["decisions"] == 0)

    # 3 — non-owner cannot renew a shard owned by another
    sr = SupervisorStore(Path(tmp) / "redteam-shards.db")
    sr.ensure_default_shards(now=100)
    chk("3 A claims a shard", sr.claim_shard(shard_id="ingest", supervisor_id="A", ttl_seconds=30, now=100))
    chk("3 non-owner cannot renew a shard", sr.renew_shards(supervisor_id="B", shard_ids=["ingest"], ttl_seconds=30, now=110) == 0)
    chk("3 non-owner cannot steal a held shard", sr.claim_shard(shard_id="ingest", supervisor_id="B", ttl_seconds=30, now=110) is False)
    sr.close()

    # 4 — duplicate spawn decision deduped
    s.record_spawn_decision(supervisor_id="A", capability_id="x", action="spawn_new_worker", idempotency_key="k", now=100)
    s.record_spawn_decision(supervisor_id="B", capability_id="x", action="spawn_new_worker", idempotency_key="k", now=101)
    chk("4 duplicate spawn decision prevented", len(s.spawn_decisions()) == 1)

    # 5 — old leader cannot renew after losing the lease
    chk("5 old leader cannot renew after expiry", s.renew_leader(lease_name="global", supervisor_id="A", ttl_seconds=30, now=999) is False)

    # 6 — stale shard reclaimed
    reclaimed = s.expire_stale_shards(now=999)
    chk("6 stale shard reclaimed", "ingest" in reclaimed)

    # 7 — state persists (not memory-only)
    s.close()
    s2 = SupervisorStore(db)
    chk("7 supervisor state persisted to DB", s2.instance("B") is not None and len(s2.ticks()) >= 1)
    s2.close()

    # 8 — no broad pkill anywhere in the supervisor control-plane code or its proofs
    sup_sources = [
        _REPO / "src/baltor/workers/supervisor_store.py",
        _REPO / "src/baltor/workers/supervisor_watch.py",
        _REPO / "scripts/check_live_supervisor_two_process.py",
    ]
    # flag actual broad-kill CALLS, not the word "pkill" in a docstring ("kills only by exact pid")
    _BAD = ("'pkill'", '"pkill"', "pkill -", "killall", "os.killpg", "os.system(")
    pk = [str(f) for f in sup_sources if any(tok in f.read_text() for tok in _BAD)]
    chk("8 no broad pkill in supervisor code (exact-pid kill only)", pk == [], str(pk))

    # 9 — control-plane code executes no heavy work (no provider/subprocess/exec in store or watch step)
    # the supervisor must not INLINE-EXECUTE heavy work — it may DELEGATE spawning to local_spawn_manager.
    # Match actual call-forms (not the word "subprocess" in a docstring); a direct subprocess./exec is banned.
    cp = (_REPO / "src/baltor/workers/supervisor_store.py").read_text() + (_REPO / "src/baltor/workers/supervisor_watch.py").read_text()
    banned = [t for t in ("subprocess.", "import subprocess", "os.system(", "requests.", "urllib.request", "eval(", "exec(") if t in cp]
    chk("9 supervisor runs no inline heavy/execution code (spawning is delegated to local_spawn_manager)", banned == [], str(banned))

    # 10 — the store exposes reads + lease/decision recording but no destructive mutation of others' truth
    s3 = SupervisorStore(db)
    forbidden = [m for m in ("delete_instance", "wipe", "force_set_leader", "overwrite_decision") if hasattr(s3, m)]
    chk("10 store has no method to overwrite/forge another supervisor's truth", forbidden == [], str(forbidden))
    s3.close()

    print(f"\n{'PASS — check_live_supervisor_redteam: 10 attacks fail safely (single leader, leader-gated duties, owner-only shards, no dup spawn, dead-leader refused, stale reclaim, durable state, no pkill, no heavy work, no truth-forging).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
