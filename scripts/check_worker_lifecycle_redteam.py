#!/usr/bin/env python3
"""scripts.check_worker_lifecycle_redteam — proof (C-FLEET-2): ten lifecycle attacks all fail safely.

  1. a P0 task is made to wait for a batch              → rejected (P0 bypasses the window)
  2. a batch task starves forever                        → rejected (max_wait forces a partial dispatch)
  3. a worker shuts down while compatible work is queued → rejected (cooldown drains first)
  4. a provider circuit breaker is ignored               → rejected (open circuit denies work)
  5. fallback duplicates side effects                    → rejected (exactly one provider per attempt)
  6. a stale worker keeps its lease forever              → rejected (expired leases are reclaimed)
  7. the recommender suggests an unsafe truth path       → rejected (never emitted)
  8. worker metrics omit startup/processed               → rejected (lifecycle metrics carry them)
  9. an unknown failure type is accepted blindly         → safe (falls back to unknown, non-retryable)
 10. a task is processed without an atomic claim         → rejected (ownership only via claim)

CLI: PYTHONPATH=. python3 scripts/check_worker_lifecycle_redteam.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.workers import telemetry as T
from src.baltor.workers.batch_windows import WAIT, window_decision
from src.baltor.workers.cooldown_drain import run_cooldown
from src.baltor.workers.failure_taxonomy import failure_policy, is_retryable
from src.baltor.workers.fleet_ledger import FleetLedger, FleetLedgerError
from src.baltor.workers.policy_recommender import recommend
from src.baltor.workers.provider_circuit_breaker import CircuitBreaker
from src.baltor.workers.provider_fallback import FallbackRouter
from src.baltor.workers.spawn_decision import decide

T0 = "2026-06-06T00:00:00Z"
CAP = "native.export"
BATCH5 = {"batch_min": 5, "max_wait_seconds": 60}


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # 1 — P0 cannot be trapped in a batch window
    a1 = decide(capability_id=CAP, queued=[{"task_id": "t", "capability_id": CAP, "priority_class": "P0", "created_at": T0}],
                workers=[], now=T0, lifecycle={"startup_budget_ms": 3000, "max_workers": 10}, batch=BATCH5,
                sla={"target_seconds": 10}, estimated_runtime_ms=500, known_capabilities={CAP})["action"]
    chk("1 P0 does not wait for a batch", a1 != "wait_for_batch", a1)

    # 2 — batch cannot starve (max_wait forces dispatch)
    d2 = window_decision([{"task_id": "t", "priority_class": "P3", "created_at": T0}],
                         batch_min=5, max_wait_seconds=60, now="2026-06-06T00:05:00Z")["decision"]
    chk("2 batch does not starve past max_wait", d2 != WAIT, d2)

    # 3 — cooldown drains queued work instead of abandoning it
    L = FleetLedger(); L.register_worker(worker_id="w", capability_ids=[CAP], now=T0)
    L.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="q", now=T0)
    out = run_cooldown(L, worker_id="w", capability_id=CAP, now=T0, idle_shutdown_seconds=60)
    chk("3 worker drains queued work before shutdown", out["cooldown_task_pickup_count"] == 1)

    # 4 — an open circuit denies work
    cb = CircuitBreaker("p", consec_threshold=1); cb.record_failure("provider_unavailable", now=T0)
    chk("4 open circuit denies work", cb.allow(now=T0) is False)

    # 5 — fallback selects exactly one provider (no duplicate side effects)
    fr = FallbackRouter(["a@v1", "b@v1"])
    sel = fr.select(now=T0)
    chk("5 fallback returns a single provider", isinstance(sel, str))
    stamped = FallbackRouter.mark_output(sel, {"r": 1})
    chk("5 result carries exactly one provider_id", stamped.get("provider_id") == sel)

    # 6 — stale lease is reclaimed, not held forever
    L6 = FleetLedger(); L6.register_worker(worker_id="s", capability_ids=[CAP], now=T0)
    L6.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="lease", now=T0)
    L6.claim_task(worker_id="s", capability_id=CAP, now=T0, lease_seconds=10)
    reclaimed = L6.reclaim_expired_leases("2026-06-06T00:05:00Z")
    chk("6 expired lease reclaimed", len(reclaimed) == 1)

    # 7 — recommender never emits an unsafe truth path
    recs = recommend({"worker_cost_metrics": {"tasks_per_worker_start": 9}, "worker_queue_metrics": {"batch_fill_ratio": 0.99, "oldest_task_age_s": 999},
                      "worker_provider_metrics": [{"provider_id": "x", "successes": 0, "failures": 9, "failure_rate": 1.0}]},
                     current_lifecycle_policy_id="warm_pool", sla_miss_count=9, idle_burn_ms=999999)
    unsafe = {"auto_promote", "skip_verification", "serve_unverified", "disable_review"}
    chk("7 no unsafe truth-path recommendation", all(r["recommendation"] not in unsafe for r in recs))

    # 8 — lifecycle metrics carry startup/processed
    L8 = FleetLedger(); L8.register_worker(worker_id="m", capability_ids=[CAP], now=T0)
    lm = T.lifecycle_metrics(L8)[0]
    chk("8 worker metrics include startup_ms + tasks_processed", "startup_ms" in lm and "tasks_processed" in lm)

    # 9 — unknown failure type is handled safely (not retryable, no crash)
    chk("9 unknown failure → unknown policy", failure_policy("xyz_made_up")["failure_type"] == "unknown")
    chk("9 unknown failure is not retryable (no infinite loop)", is_retryable("xyz_made_up") is False)

    # 10 — cannot process a task without claiming it
    L10 = FleetLedger(); L10.register_worker(worker_id="w", capability_ids=[CAP], now=T0)
    t = L10.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="nc", now=T0)
    raised = False
    try:
        L10.start_task(t["task_id"], "w", T0)        # never claimed → must reject
    except FleetLedgerError:
        raised = True
    chk("10 cannot start a task without atomic claim", raised)

    print(f"\n{'PASS — check_worker_lifecycle_redteam: 10 attacks fail safely (P0 bypass, no starvation, drain-before-exit, circuit honored, single-provider fallback, lease reclaim, no unsafe recs, metrics complete, unknown-failure safe, no claimless processing).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
