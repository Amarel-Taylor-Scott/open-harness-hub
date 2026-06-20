#!/usr/bin/env python3
"""scripts.check_flywheel_supervisor_lag_metrics — proof (C-FLEET-3): supervisor lag metrics expose
COORDINATION pressure (loop duration vs interval budget, over-budget ratio, shard lag, due backlog) and
the scale signal fires on that pressure — NOT on heavy-worker busyness. Steady state recommends no scale.

CLI: PYTHONPATH=. python3 scripts/check_flywheel_supervisor_lag_metrics.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.workers.fleet_ledger import _plus_s
from src.baltor.workers.supervisor_metrics import lag_metrics, should_scale_supervisor
from src.baltor.workers.supervisor_ledger import SupervisorLedger

T0 = "2026-06-06T00:00:00Z"


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # steady: ticks well under the 10s (10000ms) interval budget, no backlog
    steady = SupervisorLedger(); steady.register_instance(supervisor_id="A", now=T0)
    for i in range(4):
        steady.record_tick(supervisor_id="A", started_at=_plus_s(T0, i * 10), duration_ms=200,
                           due_task_count=2, scheduled_count=2, interval_ms=10000)
    m = lag_metrics(steady, now=_plus_s(T0, 40))
    chk("steady avg loop duration computed", m["avg_loop_duration_ms"] == 200.0)
    chk("steady has no over-budget ticks", m["over_budget_tick_count"] == 0)
    chk("steady → no scale", should_scale_supervisor(m)["scale_supervisor"] is False)

    # pressure: most ticks exceed the interval budget
    busy = SupervisorLedger(); busy.register_instance(supervisor_id="A", now=T0)
    for i in range(4):
        busy.record_tick(supervisor_id="A", started_at=_plus_s(T0, i * 10), duration_ms=15000,
                         due_task_count=80, scheduled_count=80, interval_ms=10000)
    mb = lag_metrics(busy, now=_plus_s(T0, 40))
    chk("pressure: over_budget_ratio high", mb["over_budget_ratio"] >= 0.5, str(mb["over_budget_ratio"]))
    chk("pressure: due backlog surfaced", mb["latest_due_task_count"] == 80)
    s = should_scale_supervisor(mb)
    chk("pressure → scale the control plane", s["scale_supervisor"] is True)
    chk("scale action is add shard owner / standby (not in-process work)", s["action"] == "add_shard_owner_or_standby")
    chk("scale reason cites coordination pressure", any("over budget" in r or "backlog" in r for r in s["reasons"]))

    # shard lag pressure
    sl = SupervisorLedger(); sl.register_instance(supervisor_id="A", now=T0)
    sl.register_shard(shard_id="shard:x", shard_type="capability", shard_key="x")
    sl.claim_shard(shard_id="shard:x", owner_id="A", now=T0, ttl_seconds=30)
    sl.record_tick(supervisor_id="A", started_at=T0, duration_ms=100, interval_ms=10000)
    m_lag = lag_metrics(sl, now=_plus_s(T0, 120))   # shard heartbeat is 120s old
    chk("shard lag measured", m_lag["max_shard_lag_s"] >= 60)
    chk("shard lag → scale", should_scale_supervisor(m_lag)["scale_supervisor"] is True)

    print(f"\n{'PASS — check_flywheel_supervisor_lag_metrics: loop duration / over-budget / shard-lag / due-backlog computed; scale fires on coordination pressure; steady state does not scale.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
