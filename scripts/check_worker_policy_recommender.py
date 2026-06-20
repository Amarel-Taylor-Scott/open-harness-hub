#!/usr/bin/env python3
"""scripts.check_worker_policy_recommender — proof (C-FLEET-2): given telemetry, the recommender proposes
the right ramp-up/ramp-down moves (warmer on SLA miss, colder on idle burn, bigger batches on high fill,
more workers on queue aging, open-circuit+fallback on provider failures, amortize cold start when reused),
stays quiet at steady state, and NEVER recommends an unsafe truth path. It only recommends.

CLI: PYTHONPATH=. python3 scripts/check_worker_policy_recommender.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.workers.policy_recommender import recommend

_STEADY = {
    "worker_cost_metrics": {"tasks_per_worker_start": 1.0},
    "worker_queue_metrics": {"batch_fill_ratio": 0.1, "oldest_task_age_s": 1},
    "worker_provider_metrics": [{"provider_id": "p", "successes": 10, "failures": 0, "failure_rate": 0.0}],
}


def _kinds(recs):
    return {r["recommendation"] for r in recs}


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # steady state → no recommendations
    chk("steady state → no recommendations", recommend(_STEADY, current_lifecycle_policy_id="warm_pool") == [])

    # SLA miss → warmer + lower max_wait
    r = recommend(_STEADY, current_lifecycle_policy_id="burst_keepalive", sla_miss_count=4)
    chk("SLA miss → switch warmer", any(x["recommendation"] == "switch_lifecycle_policy" and x.get("to_policy") == "warm_pool" for x in r))
    chk("SLA miss → lower max_wait", "lower_max_wait" in _kinds(r))

    # cold_start reused a lot → amortize (burst_keepalive)
    reused = {**_STEADY, "worker_cost_metrics": {"tasks_per_worker_start": 4.0}}
    r2 = recommend(reused, current_lifecycle_policy_id="cold_start_each_task")
    chk("reused cold_start → keep alive", any(x.get("to_policy") == "burst_keepalive" for x in r2))

    # idle burn high on warm pool → cool down + shrink
    r3 = recommend(_STEADY, current_lifecycle_policy_id="warm_pool", idle_burn_ms=400_000)
    chk("idle burn → cool down", any(x.get("to_policy") == "burst_keepalive" for x in r3))
    chk("idle burn → reduce max_workers", "reduce_max_workers" in _kinds(r3))

    # high batch fill → bigger batches
    fill = {**_STEADY, "worker_queue_metrics": {"batch_fill_ratio": 0.95, "oldest_task_age_s": 1}}
    chk("high batch fill → increase_batch_min", "increase_batch_min" in _kinds(recommend(fill, current_lifecycle_policy_id="batch_min_5")))

    # queue aging → more workers
    aged = {**_STEADY, "worker_queue_metrics": {"batch_fill_ratio": 0.1, "oldest_task_age_s": 300}}
    chk("queue aging → increase_max_workers", "increase_max_workers" in _kinds(recommend(aged, current_lifecycle_policy_id="warm_pool")))

    # provider failing → open circuit + add fallback
    badp = {**_STEADY, "worker_provider_metrics": [{"provider_id": "flaky@v1", "successes": 1, "failures": 5, "failure_rate": 0.83}]}
    rp = recommend(badp, current_lifecycle_policy_id="warm_pool")
    chk("provider failing → open_circuit_and_add_fallback", any(x["recommendation"] == "open_circuit_and_add_fallback" and x.get("provider_id") == "flaky@v1" for x in rp))

    # safety: no unsafe truth-path recommendation ever
    allr = (recommend(_STEADY, current_lifecycle_policy_id="burst_keepalive", sla_miss_count=9, idle_burn_ms=999999)
            + recommend(badp, current_lifecycle_policy_id="warm_pool") + recommend(aged, current_lifecycle_policy_id="warm_pool"))
    unsafe = {"auto_promote", "skip_verification", "serve_unverified", "disable_review", "publish_allegation"}
    chk("never recommends an unsafe truth path", all(x["recommendation"] not in unsafe for x in allr))

    # determinism
    chk("deterministic", recommend(badp, current_lifecycle_policy_id="warm_pool") == recommend(badp, current_lifecycle_policy_id="warm_pool"))

    print(f"\n{'PASS — check_worker_policy_recommender: warmer-on-SLA / colder-on-idle / bigger-batches / more-workers / open-circuit+fallback / amortize-cold-start; quiet at steady state; no unsafe truth path; deterministic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
