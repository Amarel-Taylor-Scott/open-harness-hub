#!/usr/bin/env python3
"""scripts.check_flywheel_supervisor_idempotent_decisions — proof (C-FLEET-3): supervisor decisions are
idempotent by key — the same due job recorded twice yields the SAME decision (one record), while distinct
keys create distinct decisions. This is what makes running multiple supervisors safe.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_flywheel_supervisor_idempotent_decisions.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.workers.supervisor_ledger import SupervisorLedger

T0 = "2026-06-06T00:00:00Z"


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    L = SupervisorLedger()
    d1 = L.record_decision(supervisor_id="A", decision_type="schedule_watch_policy",
                           idempotency_key="wp:reg-e:2026-06-06", reason="due", now=T0)
    d2 = L.record_decision(supervisor_id="A", decision_type="schedule_watch_policy",
                           idempotency_key="wp:reg-e:2026-06-06", reason="due again", now=T0)
    chk("same key → same decision_id", d1["decision_id"] == d2["decision_id"])
    chk("same key → exactly one decision recorded", len(L.decisions()) == 1)
    chk("first reason wins (record is immutable on dedup)", d2["reason"] == "due")

    d3 = L.record_decision(supervisor_id="A", decision_type="schedule_watch_policy",
                           idempotency_key="wp:reg-e:2026-06-07", reason="next day", now=T0)
    chk("distinct key → distinct decision", d3["decision_id"] != d1["decision_id"] and len(L.decisions()) == 2)

    # a different decision TYPE with its own key is also distinct
    L.record_decision(supervisor_id="A", decision_type="run_proof_sweep", idempotency_key="proof:2026-06-06", now=T0)
    chk("distinct type+key → distinct decision", len(L.decisions()) == 3)

    print(f"\n{'PASS — check_flywheel_supervisor_idempotent_decisions: same key dedups to one immutable decision; distinct keys/types create distinct decisions.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
