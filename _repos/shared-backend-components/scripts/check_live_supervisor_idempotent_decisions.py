#!/usr/bin/env python3
"""scripts.check_live_supervisor_idempotent_decisions — proof (OPP-supervisor-scaling-live): DURABLE
supervisor decisions are idempotent by key (UNIQUE), so two racing supervisors recording the same due job
yield ONE decision; spawn decisions dedup too; distinct keys create distinct decisions; persists.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_live_supervisor_idempotent_decisions.py --self-test
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

    tmp = tempfile.mkdtemp(prefix="baltor-sup-idem-")
    s = SupervisorStore(Path(tmp) / "sup.db")

    d1 = s.record_decision(supervisor_id="A", decision_type="schedule", idempotency_key="wp:reg-e:w1", reason="due", now=100)
    d2 = s.record_decision(supervisor_id="B", decision_type="schedule", idempotency_key="wp:reg-e:w1", reason="due-again", now=101)
    chk("racing supervisors → same decision", d1["decision_id"] == d2["decision_id"])
    chk("exactly one decision recorded", len(s.decisions(decision_type="schedule")) == 1)
    chk("first writer wins (immutable on dedup)", d2["reason"] == "due")
    chk("decision_exists true", s.decision_exists("wp:reg-e:w1"))

    s.record_decision(supervisor_id="A", decision_type="schedule", idempotency_key="wp:reg-e:w2", now=100)
    chk("distinct key → distinct decision", len(s.decisions(decision_type="schedule")) == 2)

    # spawn decisions dedup independently + write the spawn table
    sp1 = s.record_spawn_decision(supervisor_id="A", capability_id="native.export", action="spawn_new_worker", idempotency_key="spawn:native.export:t1", now=100)
    sp2 = s.record_spawn_decision(supervisor_id="B", capability_id="native.export", action="spawn_new_worker", idempotency_key="spawn:native.export:t1", now=101)
    chk("racing spawn → one spawn decision", sp1["decision_id"] == sp2["decision_id"])
    chk("one row in supervisor_spawn_decisions", len(s.spawn_decisions()) == 1, str(len(s.spawn_decisions())))
    chk("no duplicate idempotency_key in decisions table",
        len({d["idempotency_key"] for d in s.decisions()}) == len(s.decisions()))
    s.close()

    # persistence
    s2 = SupervisorStore(Path(tmp) / "sup.db")
    chk("decisions persist across reopen", s2.decision_exists("wp:reg-e:w1") and len(s2.spawn_decisions()) == 1)
    s2.close()
    print(f"\n{'PASS — check_live_supervisor_idempotent_decisions: durable idempotent decisions (UNIQUE key), racing supervisors dedup, spawn dedup, distinct keys distinct, persists.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
