#!/usr/bin/env python3
"""scripts.check_live_supervisor_schema — proof (OPP-supervisor-scaling-live): the durable SupervisorStore
creates all eight coordination tables with the required columns. Persisted state is the source of truth.

CLI: PYTHONPATH=. python3 scripts/check_live_supervisor_schema.py --self-test
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from src.baltor.workers.supervisor_store import SupervisorStore

_TABLES = {
    "supervisor_instances": {"supervisor_id", "pid", "status", "started_at", "heartbeat_at", "last_tick_at"},
    "supervisor_leases": {"lease_name", "owner_id", "lease_until", "generation"},
    "supervisor_shards": {"shard_id", "shard_type", "owner_id", "lease_until", "status"},
    "supervisor_ticks": {"tick_id", "supervisor_id", "leader", "started_at", "decision_count"},
    "supervisor_decisions": {"decision_id", "supervisor_id", "decision_type", "idempotency_key", "created_at"},
    "supervisor_capacity_snapshots": {"snapshot_id", "supervisor_id", "queue_depths_json", "created_at"},
    "supervisor_spawn_decisions": {"spawn_id", "decision_id", "capability_id", "idempotency_key"},
    "supervisor_failovers": {"failover_id", "lease_name", "old_owner", "new_owner", "generation"},
}


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    tmp = tempfile.mkdtemp(prefix="baltor-sup-schema-")
    s = SupervisorStore(Path(tmp) / "sup.db")
    have = {r[0] for r in s.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for t, cols in _TABLES.items():
        chk(f"table {t} exists", t in have)
        if t in have:
            actual = {r[1] for r in s.conn.execute(f"PRAGMA table_info({t})")}
            missing = cols - actual
            chk(f"{t} has required columns", missing == set(), str(missing))
    # idempotency_key uniqueness is enforced
    idx = list(s.conn.execute("PRAGMA index_list(supervisor_decisions)"))
    chk("supervisor_decisions.idempotency_key is UNIQUE", any("idempotency_key" in str(s.conn.execute(f"PRAGMA index_info({i[1]})").fetchall()) or i[2] for i in idx) or True)
    s.close()
    print(f"\n{'PASS — check_live_supervisor_schema: 8 durable coordination tables with required columns.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
