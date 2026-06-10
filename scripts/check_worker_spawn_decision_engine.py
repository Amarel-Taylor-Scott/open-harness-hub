#!/usr/bin/env python3
"""scripts.check_worker_spawn_decision_engine — proof (C-FLEET-2): the spawn-decision engine returns the
right action across every lane: dead-letter unknown capability, spawn when no worker, reuse when SLA is
met, spawn when SLA would be missed, batch wait/partial/full, provider fallback on open circuit,
concurrency hold, and P0/P1 bypassing the batch window.

CLI: PYTHONPATH=. python3 scripts/check_worker_spawn_decision_engine.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.workers.spawn_decision import ACTIONS, decide

T0 = "2026-06-06T00:00:00Z"
ONDEMAND = {"batch_min": 1, "max_wait_seconds": 0}
BATCH5 = {"batch_min": 5, "max_wait_seconds": 60}
SLA = {"target_seconds": 10}
LIFE = {"startup_budget_ms": 3000, "max_workers": 50}
KNOWN = {"native.export", "browser.research"}


def _t(i, *, pri="P2", created=T0, deadline=None):
    return {"task_id": f"t{i}", "capability_id": "native.export", "priority_class": pri,
            "created_at": created, "deadline_at": deadline}


def _w(wid, *, avail=T0, mc=4, active=0, status="warm"):
    return {"worker_id": wid, "status": status, "capability_ids": ["native.export"],
            "available_at": avail, "max_concurrency": mc, "active_task_count": active}


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    def act(**kw):
        kw.setdefault("now", T0); kw.setdefault("lifecycle", LIFE); kw.setdefault("sla", SLA)
        kw.setdefault("estimated_runtime_ms", 500); kw.setdefault("known_capabilities", KNOWN)
        return decide(capability_id="native.export", **kw)["action"]

    chk("all actions in the declared vocabulary", set(ACTIONS) >= {
        "use_existing_worker", "spawn_new_worker", "wait_for_batch", "dispatch_partial_batch",
        "route_to_fallback_provider", "hold_due_to_concurrency_limit", "dead_letter_invalid"})

    # dead-letter unknown capability
    chk("unknown capability → dead_letter_invalid",
        decide(capability_id="nope", queued=[_t(1)], workers=[], now=T0, lifecycle=LIFE, batch=ONDEMAND,
               sla=SLA, estimated_runtime_ms=500, known_capabilities=KNOWN)["action"] == "dead_letter_invalid")

    # on-demand, no worker → spawn
    chk("on-demand + no worker → spawn_new_worker", act(queued=[_t(1)], workers=[], batch=ONDEMAND) == "spawn_new_worker")
    # warm worker free + meets SLA → reuse
    chk("warm worker meets SLA → use_existing_worker", act(queued=[_t(1)], workers=[_w("a")], batch=ONDEMAND) == "use_existing_worker")
    # worker free but available far in the future (would miss deadline) → spawn
    chk("existing would miss deadline → spawn_new_worker",
        act(queued=[_t(1)], workers=[_w("a", avail="2026-06-06T01:00:00Z")], batch=ONDEMAND) == "spawn_new_worker")
    # worker busy, no free slot → spawn
    chk("no free slot → spawn_new_worker", act(queued=[_t(1)], workers=[_w("a", mc=1, active=1)], batch=ONDEMAND) == "spawn_new_worker")

    # batch lane
    chk("batch below threshold within max_wait → wait_for_batch",
        act(queued=[_t(i) for i in range(4)], workers=[], batch=BATCH5) == "wait_for_batch")
    chk("batch full → spawn_new_worker", act(queued=[_t(i) for i in range(5)], workers=[], batch=BATCH5) == "spawn_new_worker")
    chk("batch max_wait reached → dispatch_partial_batch",
        decide(capability_id="native.export", queued=[_t(1)], workers=[], now="2026-06-06T00:02:00Z",
               lifecycle=LIFE, batch=BATCH5, sla=SLA, estimated_runtime_ms=500, known_capabilities=KNOWN)["action"]
        == "dispatch_partial_batch")
    # P0/P1 bypass the batch window → on-demand spawn (not wait)
    chk("P0 bypasses batch window", act(queued=[_t(1, pri="P0")], workers=[], batch=BATCH5) == "spawn_new_worker")

    # provider circuit open
    chk("circuit open + fallback → route_to_fallback_provider",
        act(queued=[_t(1)], workers=[_w("a")], batch=ONDEMAND, circuit_open=True, has_fallback=True) == "route_to_fallback_provider")
    chk("circuit open + no fallback → hold",
        act(queued=[_t(1)], workers=[_w("a")], batch=ONDEMAND, circuit_open=True, has_fallback=False) == "hold_due_to_concurrency_limit")

    # concurrency limit
    chk("tenant concurrency limit → hold",
        act(queued=[_t(1)], workers=[_w("a")], batch=ONDEMAND, tenant_active=5, tenant_limit=5) == "hold_due_to_concurrency_limit")

    # determinism
    a = decide(capability_id="native.export", queued=[_t(1)], workers=[_w("a")], now=T0, lifecycle=LIFE,
               batch=ONDEMAND, sla=SLA, estimated_runtime_ms=500, known_capabilities=KNOWN)
    b = decide(capability_id="native.export", queued=[_t(1)], workers=[_w("a")], now=T0, lifecycle=LIFE,
               batch=ONDEMAND, sla=SLA, estimated_runtime_ms=500, known_capabilities=KNOWN)
    chk("deterministic", a == b)

    print(f"\n{'PASS — check_worker_spawn_decision_engine: dead-letter / spawn-no-worker / reuse-SLA / spawn-SLA-miss / batch wait+full+partial / P0-bypass / fallback / concurrency-hold all decided correctly + deterministic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
