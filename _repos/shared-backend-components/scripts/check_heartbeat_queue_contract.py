#!/usr/bin/env python3
"""scripts.check_heartbeat_queue_contract — proof (G3): the queue/heartbeat contract is COMPLETE offline.

The offline (no-Redis) `queue_stats()` branch must expose the SAME contract keys as the Redis branch —
list keys are lists, count keys are ints — so the heartbeat / dashboard / flow test never branch on
whether Redis is reachable. This is the fitness function that prevents the `pending_sample`-missing-offline
drift from recurring.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_heartbeat_queue_contract.py --self-test
"""
from __future__ import annotations

import argparse
import os

# force the offline branch deterministically (no Redis) regardless of environment
os.environ.setdefault("BALTOR_DISABLE_REDIS", "1")

_LIST_KEYS = ("pending_sample", "recent_worker_events", "active_worker_jobs")
_COUNT_KEYS = ("active_worker_job_count", "stale_active_worker_job_count", "stale_pending_job_count",
               "pending_sample_missing_timestamps")
_PRESENT_KEYS = ("available", "queue", "oldest_pending_age_seconds", "newest_pending_age_seconds",
                 "thresholds", "trend")


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    import scripts.baltor_admin_demo_server as srv
    # deterministically force the offline branch (do not depend on whether Redis happens to be running)
    _orig = srv.redis_client
    srv.redis_client = lambda: None
    try:
        chk("offline branch forced (redis_client -> None)", srv.redis_client() is None)
        q = srv.queue_stats()
        hb = srv.heartbeat_payload()
    finally:
        srv.redis_client = _orig
    chk("offline queue_stats reports available=False", q.get("available") is False, str(q.get("available")))
    for k in _PRESENT_KEYS:
        chk(f"contract key present: {k}", k in q)
    for k in _LIST_KEYS:
        chk(f"{k} is a list offline", isinstance(q.get(k), list), str(type(q.get(k))))
    for k in _COUNT_KEYS:
        chk(f"{k} is an int offline", isinstance(q.get(k), int), str(type(q.get(k))))

    # the full heartbeat payload must also carry the queue contract offline
    hb = srv.heartbeat_payload()
    chk("heartbeat kind correct", hb.get("kind") == "baltor.debug_heartbeat")
    chk("heartbeat.queue.pending_sample is a list", isinstance(hb.get("queue", {}).get("pending_sample"), list))
    chk("heartbeat.queue.active_worker_jobs is a list", isinstance(hb.get("queue", {}).get("active_worker_jobs"), list))

    print(f"\n{'PASS — check_heartbeat_queue_contract: the offline queue/heartbeat contract is complete (lists are lists, counts are ints) — no Redis-vs-offline drift.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
