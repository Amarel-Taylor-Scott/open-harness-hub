#!/usr/bin/env python3
"""scripts.check_worker_batch_windows — proof (C-FLEET-2): batch windows dispatch full at batch_min, hold
below it, dispatch partial at max_wait (no starvation), let high-priority bypass, group by tenant/domain/
provider, and dispatch the longest-waiting group first (fairness).

Asserts the spec table: 4/5 wait, 5 dispatch, 24/25 wait, 25 dispatch, 99/100 wait, 100 dispatch.

CLI: PYTHONPATH=. python3 scripts/check_worker_batch_windows.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.workers.batch_windows import BYPASS, DISPATCH, DISPATCH_PARTIAL, WAIT, plan_dispatch, window_decision

T0 = "2026-06-06T00:00:00Z"


def _tasks(n, *, pri="P2", created=T0, tenant="acme"):
    return [{"task_id": f"t{i}", "priority_class": pri, "created_at": created, "tenant_id": tenant} for i in range(n)]


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    def dec(n, bmin, *, now=T0, pri="P2"):
        return window_decision(_tasks(n, pri=pri), batch_min=bmin, max_wait_seconds=60, now=now)["decision"]

    # the spec table
    chk("4 of 5 → wait", dec(4, 5) == WAIT)
    chk("5 of 5 → dispatch", dec(5, 5) == DISPATCH)
    chk("24 of 25 → wait", dec(24, 25) == WAIT)
    chk("25 of 25 → dispatch", dec(25, 25) == DISPATCH)
    chk("99 of 100 → wait", dec(99, 100) == WAIT)
    chk("100 of 100 → dispatch", dec(100, 100) == DISPATCH)

    # dispatch caps at batch_min
    full = window_decision(_tasks(7), batch_min=5, max_wait_seconds=60, now=T0)
    chk("dispatch readies exactly batch_min", len(full["ready"]) == 5, str(len(full["ready"])))

    # max_wait → partial (no starvation)
    chk("below threshold but max_wait reached → dispatch_partial",
        window_decision(_tasks(2, created=T0), batch_min=5, max_wait_seconds=60, now="2026-06-06T00:02:00Z")["decision"]
        == DISPATCH_PARTIAL)

    # high priority bypass
    chk("P0 bypasses the batch window", dec(2, 5, pri="P0") == BYPASS)
    chk("P1 bypasses the batch window", dec(1, 25, pri="P1") == BYPASS)

    # grouping + fairness (oldest-waiting group dispatches first)
    mixed = (_tasks(5, tenant="late", created="2026-06-06T00:00:30Z")
             + _tasks(5, tenant="early", created="2026-06-06T00:00:00Z"))
    plan = plan_dispatch(mixed, batch_min=5, max_wait_seconds=60, now="2026-06-06T00:01:00Z", group_by="tenant_id")
    chk("two groups dispatched", len(plan) == 2, str(len(plan)))
    chk("fairness: longest-waiting group first", plan[0]["group"] == "early", str([p["group"] for p in plan]))

    # determinism
    a = window_decision(_tasks(5), batch_min=5, max_wait_seconds=60, now=T0)
    b = window_decision(_tasks(5), batch_min=5, max_wait_seconds=60, now=T0)
    chk("deterministic", a == b)

    print(f"\n{'PASS — check_worker_batch_windows: 5/25/100 thresholds, partial at max_wait (no starvation), P0/P1 bypass, grouping + fairness, deterministic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
