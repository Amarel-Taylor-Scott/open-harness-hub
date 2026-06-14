#!/usr/bin/env python3
"""scripts.check_durable_queue_crash_recovery — PROOF: a worker that crashes/redeploys mid-job does NOT
silently orphan durable work — BOTH durable backends recover it.

The audit found SqliteQueue.pull marked a job 'processing' with no reaper (stuck forever on a crash) and
RedisQueue.lpop removed the job with no in-flight tracking (lost on a crash). Now:
  - SqliteQueue stamps claimed_at and reap_stuck() requeues orphans past a visibility timeout (+ on startup);
  - RedisQueue moves pull → a :processing list (LMOVE), ack/terminal remove it, reap_stuck() requeues leftovers.

Tested against real sqlite + a faithful in-memory fake redis (the exact list ops used). Exit 0/1.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.foundry.queues import RedisQueue, SqliteQueue


class _FakeRedis:
    """Minimal in-memory model of the Redis list ops the queue uses (faithful enough to test the logic)."""

    def __init__(self) -> None:
        self.lists: dict[str, list] = {}

    def rpush(self, k, v):
        self.lists.setdefault(k, []).append(v)

    def lpop(self, k):
        lst = self.lists.get(k) or []
        return lst.pop(0) if lst else None

    def lmove(self, src, dst, src_side, dst_side):
        s = self.lists.get(src) or []
        if not s:
            return None
        v = s.pop(0) if src_side == "LEFT" else s.pop()
        d = self.lists.setdefault(dst, [])
        d.insert(0, v) if dst_side == "LEFT" else d.append(v)
        return v

    def lrem(self, k, count, value):
        lst, out, removed = self.lists.get(k) or [], [], 0
        for x in lst:
            if x == value and removed < count:
                removed += 1
                continue
            out.append(x)
        self.lists[k] = out
        return removed

    def llen(self, k):
        return len(self.lists.get(k) or [])

    def lrange(self, k, start, end):
        lst = self.lists.get(k) or []
        return lst[start:] if end == -1 else lst[start:end + 1]


def _self_test() -> int:
    fails: list[str] = []

    def ck(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    # ── SqliteQueue crash recovery ───────────────────────────────────────────────────────────────
    with tempfile.TemporaryDirectory() as tmp:
        q = SqliteQueue(str(Path(tmp) / "q.db"))
        q.enqueue({"job_id": "j1"})
        j = q.pull()
        ck("sqlite: pull claims the job (processing)", bool(j) and j["job_id"] == "j1")
        ck("sqlite: an in-flight (claimed) job is not re-pulled", q.pull() is None)
        ck("sqlite: reap_stuck(default timeout) does NOT steal a recently-claimed job (safe)", q.reap_stuck() == 0)
        ck("sqlite: reap_stuck(timeout=0) requeues the orphan", q.reap_stuck(visibility_timeout_s=0) == 1)
        j2 = q.pull()
        ck("sqlite: the reaped job is re-pullable — work recovered, not lost", bool(j2) and j2["job_id"] == "j1")
        q.ack(j2)
        ck("sqlite: acked job is gone (queue empty)", q.pull() is None)

        # __init__ reap recovers a STALE orphan (ancient claimed_at) at startup
        q.enqueue({"job_id": "j2"})
        q.pull()  # claims it (processing)
        con = sqlite3.connect(q.path)
        con.execute("UPDATE jobs SET claimed_at=1.0 WHERE status='processing'")  # ancient claim (pre-crash)
        con.commit()
        con.close()
        q2 = SqliteQueue(q.path)  # __init__ runs reap_stuck() → stale orphan requeued
        jr = q2.pull()
        ck("sqlite: __init__ reap recovers a STALE orphan at startup", bool(jr) and jr["job_id"] == "j2")

    # ── RedisQueue crash recovery (faithful fake redis) ──────────────────────────────────────────
    r = RedisQueue(_FakeRedis())
    r.enqueue({"job_id": "r1"})
    j = r.pull()
    ck("redis: pull MOVES the job to the :processing list (reliable, not lost on crash)",
       bool(j) and j["job_id"] == "r1" and r.client.llen(r.processing_key) == 1 and r.client.llen(r.key) == 0)
    ck("redis: reap_stuck requeues the in-flight orphan → pending",
       r.reap_stuck() == 1 and r.client.llen(r.key) == 1 and r.client.llen(r.processing_key) == 0)
    j2 = r.pull()
    r.ack(j2)
    ck("redis: ack removes the job from :processing (no orphan, nothing left pending)",
       r.client.llen(r.processing_key) == 0 and r.client.llen(r.key) == 0)

    r.enqueue({"job_id": "r2", "_attempts": 2})
    j3 = r.pull()
    r.nack(j3)
    pend = [json.loads(x) for x in r.client.lrange(r.key, 0, -1)]
    ck("redis: nack removes from :processing AND requeues to pending",
       r.client.llen(r.processing_key) == 0 and len(pend) == 1)
    ck("redis: nack preserves _attempts (retry state survives) and leaks no _processing_raw",
       pend and pend[0].get("_attempts") == 2 and "_processing_raw" not in pend[0])

    # terminal: fail_permanently removes from :processing and lands in the failed list, no transport-field leak
    j4 = r.pull()
    r.fail_permanently(j4)
    failed = [json.loads(x) for x in r.client.lrange(r.failed_permanently_key, 0, -1)]
    ck("redis: fail_permanently removes from :processing + records cleanly (no _processing_raw)",
       r.client.llen(r.processing_key) == 0 and bool(failed) and "_processing_raw" not in failed[0])

    print(("PASS — " if not fails else "FAIL — ")
          + "check_durable_queue_crash_recovery: a mid-job crash no longer orphans work — SqliteQueue reaps stuck "
            "'processing' rows (visibility timeout + startup) and RedisQueue moves pull→:processing then reaps "
            "leftovers; ack/nack/terminal clear in-flight; retry state (_attempts) survives; no transport field leaks.")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
