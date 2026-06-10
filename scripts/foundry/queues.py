#!/usr/bin/env python3
"""Foundry queues — the broker adapter (the "Celery layer", kept light).

`worker.py` already provides the worker loop + retry + permanent-failure routing + a `Queue`
**protocol**, so the broker is a thin, swappable adapter — NOT a reason to adopt a heavy
framework. Recommended default: a **Redis-list `RedisQueue`** (one dep, pairs natively
with KEDA's Redis scaler — autoscale workers on list length). Celery / RQ / arq / SQS /
Cloud Tasks all satisfy the same protocol if you want their schedulers/monitoring; a
**workflow orchestrator (Argo Workflows / Temporal)** sits ABOVE this for the multi-step
DAG — see `docs/architecture/cloud-architecture.md`.

`RedisQueue` is duck-typed over a redis client (`rpush`/`lpop`/`llen`), so it's tested
offline with an in-memory fake — no `redis` install needed. Run
`python -m scripts.foundry.queues` for the self-test.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

DEFAULT_QUEUE_KEY = "ohh:foundry:jobs"
GOVERNED_QUEUE_STATES = {"approval_required", "budget_blocked", "failed_permanently"}


def _job_without_queue_private_fields(job: dict) -> dict:
    return {k: v for k, v in job.items() if not str(k).startswith("_")}


def _merge_nested_dict(target: dict, updates: dict) -> dict:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            target[key] = _merge_nested_dict(dict(target[key]), value)
        else:
            target[key] = value
    return target


class RedisQueue:
    """Redis-list queue implementing `worker.Queue`. KEDA scales the worker fleet on
    `LLEN(key)`; nack re-queues; permanently failed jobs go to
    ``{key}:failed-permanently`` for inspection.

    Budget governance uses separate lists so approval-required work is resumable
    and budget-blocked work is not mixed with malformed or permanently failed
    jobs.
    """

    def __init__(self, client: Any, key: str = DEFAULT_QUEUE_KEY) -> None:
        self.client = client
        self.key = key
        self.failed_permanently_key = key + ":failed-permanently"
        self.approval_required_key = key + ":approval-required"
        self.budget_blocked_key = key + ":budget-blocked"

    @staticmethod
    def _dec(raw: Any) -> str:
        return raw if isinstance(raw, str) else raw.decode("utf-8")

    def enqueue(self, job: dict) -> None:
        self.client.rpush(self.key, json.dumps(job))

    def pull(self) -> dict | None:
        raw = self.client.lpop(self.key)
        return None if raw is None else json.loads(self._dec(raw))

    def ack(self, job: dict) -> None:   # list-pop already removed it
        pass

    def nack(self, job: dict) -> None:
        self.client.rpush(self.key, json.dumps(job))

    def dead_letter(self, job: dict) -> None:
        """Compatibility alias; new code should call fail_permanently()."""
        self.fail_permanently(job)

    def fail_permanently(self, job: dict) -> None:
        self.client.rpush(self.failed_permanently_key, json.dumps(job))

    def hold(self, job: dict) -> None:
        """Compatibility alias; new code should call hold_for_approval()."""
        self.hold_for_approval(job)

    def hold_for_approval(self, job: dict) -> None:
        self.client.rpush(self.approval_required_key, json.dumps(job))

    def block(self, job: dict) -> None:
        """Compatibility alias; new code should call block_for_budget()."""
        self.block_for_budget(job)

    def block_for_budget(self, job: dict) -> None:
        self.client.rpush(self.budget_blocked_key, json.dumps(job))

    def _state_key(self, status: str) -> str:
        if status == "pending":
            return self.key
        if status == "approval_required":
            return self.approval_required_key
        if status == "budget_blocked":
            return self.budget_blocked_key
        if status == "failed_permanently":
            return self.failed_permanently_key
        raise ValueError(f"unsupported queue status: {status}")

    def depth(self) -> int:
        return int(self.client.llen(self.key))

    def stats(self) -> dict[str, int]:
        return {
            "pending": int(self.client.llen(self.key)),
            "approval_required": int(self.client.llen(self.approval_required_key)),
            "budget_blocked": int(self.client.llen(self.budget_blocked_key)),
            "failed_permanently": int(self.client.llen(self.failed_permanently_key)),
        }

    def list_jobs(self, status: str, *, limit: int = 50) -> list[dict]:
        key = self._state_key(status)
        if not callable(getattr(self.client, "lrange", None)):
            return []
        raw_items = self.client.lrange(key, 0, max(limit - 1, 0))
        jobs = []
        for raw in raw_items:
            try:
                jobs.append(json.loads(self._dec(raw)))
            except json.JSONDecodeError:
                jobs.append({"_raw": self._dec(raw)})
        return jobs

    def requeue_job(self, job_id: str, *, from_status: str, updates: dict | None = None) -> dict | None:
        key = self._state_key(from_status)
        if not callable(getattr(self.client, "lrange", None)) or not callable(getattr(self.client, "lrem", None)):
            return None
        for raw in self.client.lrange(key, 0, -1):
            body = self._dec(raw)
            try:
                job = json.loads(body)
            except json.JSONDecodeError:
                continue
            if str(job.get("job_id") or "") != str(job_id):
                continue
            removed = int(self.client.lrem(key, 1, raw))
            if removed <= 0:
                return None
            job = _merge_nested_dict(_job_without_queue_private_fields(job), updates or {})
            job["requeued_at"] = int(time.time())
            job["requeued_from_status"] = from_status
            self.enqueue(job)
            return job
        return None


class SqliteQueue:
    """Durable LOCAL queue (sqlite) — same protocol, no services. Cloud swaps RedisQueue
    via from_env; nothing else changes. Single-node dev; Redis is the multi-node path."""

    def __init__(self, path: str, *, key: str = DEFAULT_QUEUE_KEY) -> None:
        self.path = str(path)
        self.key = key
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.path)
        con.execute("CREATE TABLE IF NOT EXISTS jobs "
                    "(seq INTEGER PRIMARY KEY AUTOINCREMENT, qkey TEXT, body TEXT, status TEXT DEFAULT 'pending')")
        con.commit()
        con.close()

    def _con(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, isolation_level=None)   # autocommit; pull() manages its own txn

    def enqueue(self, job: dict) -> None:
        c = self._con()
        c.execute("INSERT INTO jobs (qkey, body, status) VALUES (?,?,'pending')", (self.key, json.dumps(job)))
        c.close()

    def pull(self) -> dict | None:
        c = self._con()
        try:
            c.execute("BEGIN IMMEDIATE")   # one worker claims a job atomically
            row = c.execute("SELECT seq, body FROM jobs WHERE qkey=? AND status='pending' ORDER BY seq LIMIT 1",
                            (self.key,)).fetchone()
            if row is None:
                c.execute("COMMIT")
                return None
            seq, body = row
            c.execute("UPDATE jobs SET status='processing' WHERE seq=?", (seq,))
            c.execute("COMMIT")
            job = json.loads(body)
            job["_seq"] = seq   # so ack/retry/failure routing can target this row
            return job
        finally:
            c.close()

    def ack(self, job: dict) -> None:
        c = self._con()
        c.execute("DELETE FROM jobs WHERE seq=?", (job.get("_seq"),))
        c.close()

    def nack(self, job: dict) -> None:   # persist _attempts so retry state survives re-pull
        body = {k: v for k, v in job.items() if k != "_seq"}
        c = self._con()
        c.execute("UPDATE jobs SET status='pending', body=? WHERE seq=?", (json.dumps(body), job.get("_seq")))
        c.close()

    def dead_letter(self, job: dict) -> None:
        """Compatibility alias; new code should call fail_permanently()."""
        self.fail_permanently(job)

    def fail_permanently(self, job: dict) -> None:
        c = self._con()
        c.execute("UPDATE jobs SET status='failed_permanently' WHERE seq=?", (job.get("_seq"),))
        c.close()

    def hold(self, job: dict) -> None:
        """Compatibility alias; new code should call hold_for_approval()."""
        self.hold_for_approval(job)

    def hold_for_approval(self, job: dict) -> None:
        body = {k: v for k, v in job.items() if k != "_seq"}
        c = self._con()
        c.execute("UPDATE jobs SET status='approval_required', body=? WHERE seq=?", (json.dumps(body), job.get("_seq")))
        c.close()

    def block(self, job: dict) -> None:
        """Compatibility alias; new code should call block_for_budget()."""
        self.block_for_budget(job)

    def block_for_budget(self, job: dict) -> None:
        body = {k: v for k, v in job.items() if k != "_seq"}
        c = self._con()
        c.execute("UPDATE jobs SET status='budget_blocked', body=? WHERE seq=?", (json.dumps(body), job.get("_seq")))
        c.close()

    def depth(self) -> int:
        c = self._con()
        n = c.execute("SELECT COUNT(*) FROM jobs WHERE qkey=? AND status='pending'", (self.key,)).fetchone()[0]
        c.close()
        return int(n)

    def count(self, status: str) -> int:
        c = self._con()
        n = c.execute("SELECT COUNT(*) FROM jobs WHERE qkey=? AND status=?", (self.key, status)).fetchone()[0]
        c.close()
        return int(n)

    def stats(self) -> dict[str, int]:
        return {
            "pending": self.count("pending"),
            "processing": self.count("processing"),
            "approval_required": self.count("approval_required"),
            "budget_blocked": self.count("budget_blocked"),
            "failed_permanently": self.count("failed_permanently"),
        }

    def list_jobs(self, status: str, *, limit: int = 50) -> list[dict]:
        c = self._con()
        rows = c.execute(
            "SELECT seq, body FROM jobs WHERE qkey=? AND status=? ORDER BY seq LIMIT ?",
            (self.key, status, int(limit)),
        ).fetchall()
        c.close()
        jobs = []
        for seq, body in rows:
            try:
                job = json.loads(body)
            except json.JSONDecodeError:
                job = {"_raw": body}
            job["_seq"] = seq
            jobs.append(job)
        return jobs

    def requeue_job(self, job_id: str, *, from_status: str, updates: dict | None = None) -> dict | None:
        c = self._con()
        try:
            c.execute("BEGIN IMMEDIATE")
            rows = c.execute(
                "SELECT seq, body FROM jobs WHERE qkey=? AND status=? ORDER BY seq",
                (self.key, from_status),
            ).fetchall()
            for seq, body in rows:
                try:
                    job = json.loads(body)
                except json.JSONDecodeError:
                    continue
                if str(job.get("job_id") or "") != str(job_id):
                    continue
                job = _merge_nested_dict(_job_without_queue_private_fields(job), updates or {})
                job["requeued_at"] = int(time.time())
                job["requeued_from_status"] = from_status
                c.execute("UPDATE jobs SET status='pending', body=? WHERE seq=?", (json.dumps(job), seq))
                c.execute("COMMIT")
                return job
            c.execute("COMMIT")
            return None
        finally:
            c.close()


def from_env(key: str | None = None):
    """Pick the broker from env — the ONLY thing that changes local → cloud.
    ``REDIS_URL`` (+ `redis` lib) → RedisQueue (multi-node/cloud); else a durable local
    SqliteQueue (`OH_QUEUE_PATH`). Never None — local dev always has a real, durable queue."""
    k = key or os.environ.get("FOUNDRY_QUEUE_KEY", DEFAULT_QUEUE_KEY)
    url = os.environ.get("REDIS_URL")
    if url:
        try:
            import redis  # type: ignore
            return RedisQueue(redis.from_url(url, decode_responses=True), key=k)
        except ImportError:
            pass   # redis lib missing — fall back to the durable local queue
    return SqliteQueue(os.environ.get("OH_QUEUE_PATH", "dist/foundry-queue.sqlite"), key=k)


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    class FakeRedis:
        """Minimal in-memory stand-in for a redis client (lists only)."""

        def __init__(self) -> None:
            self.store: dict[str, list[str]] = {}

        def rpush(self, k: str, v: str) -> int:
            self.store.setdefault(k, []).append(v)
            return len(self.store[k])

        def lpop(self, k: str):
            lst = self.store.get(k) or []
            return lst.pop(0) if lst else None

        def llen(self, k: str) -> int:
            return len(self.store.get(k) or [])

        def lrange(self, k: str, start: int, end: int):
            lst = self.store.get(k) or []
            if end == -1:
                return list(lst[start:])
            return list(lst[start:end + 1])

        def lrem(self, k: str, count: int, v: str) -> int:
            lst = self.store.get(k) or []
            removed = 0
            kept = []
            for item in lst:
                if item == v and (count <= 0 or removed < count):
                    removed += 1
                    continue
                kept.append(item)
            self.store[k] = kept
            return removed

    r = FakeRedis()
    q = RedisQueue(r, key="t:jobs")
    q.enqueue({"partition": "a"})
    q.enqueue({"partition": "b"})
    check("enqueue + depth", q.depth() == 2)
    check("pull is FIFO", q.pull() == {"partition": "a"})
    check("depth decremented", q.depth() == 1)
    job = q.pull()
    q.nack(job)
    check("nack re-queues", q.depth() == 1)
    q.pull()
    check("queue drained", q.depth() == 0 and q.pull() is None)
    q.fail_permanently({"partition": "malformed"})
    check("failed jobs go to {key}:failed-permanently", r.llen("t:jobs:failed-permanently") == 1)
    q.hold_for_approval({"partition": "approval"})
    q.block_for_budget({"partition": "budget"})
    check("approval-required jobs go to {key}:approval-required", r.llen("t:jobs:approval-required") == 1)
    check("budget-blocked jobs go to {key}:budget-blocked", r.llen("t:jobs:budget-blocked") == 1)
    check("redis stats include explicit governance queues", q.stats()["approval_required"] == 1 and q.stats()["budget_blocked"] == 1)
    q.hold_for_approval({"job_id": "approve-me", "budget_policy": {"action": "require_approval"}})
    check("redis lists approval-required jobs", q.list_jobs("approval_required")[0]["partition"] == "approval")
    approved = q.requeue_job(
        "approve-me",
        from_status="approval_required",
        updates={"budget_override_approved": True, "budget_policy": {"approved": True}},
    )
    check("redis requeues approved job", approved and approved["budget_override_approved"] and q.depth() == 1)

    # satisfies the worker.Queue protocol
    from scripts.foundry.worker import Queue, Worker
    check("RedisQueue isinstance worker.Queue", isinstance(q, Queue))

    # end-to-end: a Worker drains a RedisQueue (with the fixture job)
    from scripts.foundry.pipeline import _fixture
    rq = RedisQueue(FakeRedis(), key="t2")
    rq.enqueue({"partition": "esg", "kind": "synthetic_demo", "gaps": [c.gap for c in _fixture()[1]]})
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp:
        n = Worker(foundry_factory=lambda: _fixture()[0], queue=rq,
                   ledger_path=Path(tmp) / "l.jsonl", now_s=0).serve()
    check("worker drains a RedisQueue", n == 1 and rq.depth() == 0, str(n))

    # SqliteQueue: the real, DURABLE local broker (survives process restarts)
    with tempfile.TemporaryDirectory() as tmp:
        qp = str(Path(tmp) / "q.sqlite")
        sq = SqliteQueue(qp, key="t")
        sq.enqueue({"partition": "a"})
        sq.enqueue({"partition": "b"})
        check("sqlite queue depth", sq.depth() == 2)
        j = sq.pull()
        check("sqlite pull returns job + _seq", j["partition"] == "a" and "_seq" in j)
        sq.ack(j)
        check("sqlite queue durable across instances", SqliteQueue(qp, key="t").depth() == 1)
        j2 = SqliteQueue(qp, key="t").pull(); SqliteQueue(qp, key="t").nack(j2)
        check("nack re-queues durably", SqliteQueue(qp, key="t").depth() == 1)
        j3 = SqliteQueue(qp, key="t").pull(); SqliteQueue(qp, key="t").hold_for_approval(j3)
        check("approval-required jobs persist explicitly", SqliteQueue(qp, key="t").stats()["approval_required"] == 1)
        sq2 = SqliteQueue(qp, key="t")
        sq2.enqueue({"partition": "budget-block"})
        j4 = sq2.pull(); sq2.block_for_budget(j4)
        check("budget-blocked jobs persist explicitly", SqliteQueue(qp, key="t").stats()["budget_blocked"] == 1)
        sq3 = SqliteQueue(qp, key="t")
        sq3.enqueue({"job_id": "approve-sqlite", "budget_policy": {"action": "require_approval"}})
        j5 = sq3.pull(); sq3.hold_for_approval(j5)
        approval_rows = sq3.list_jobs("approval_required")
        check("sqlite lists approval-required jobs", any(row.get("job_id") == "approve-sqlite" for row in approval_rows))
        approved_sqlite = sq3.requeue_job(
            "approve-sqlite",
            from_status="approval_required",
            updates={"budget_override_approved": True, "budget_policy": {"approved": True}},
        )
        check("sqlite requeues approved job", approved_sqlite and sq3.depth() == 1)

    # from_env without REDIS_URL ⇒ a durable SqliteQueue (NEVER None — local dev has a real queue)
    saved = os.environ.pop("REDIS_URL", None)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["OH_QUEUE_PATH"] = str(Path(tmp) / "fe.sqlite")
            check("from_env without REDIS_URL ⇒ SqliteQueue", isinstance(from_env(), SqliteQueue))
            os.environ.pop("OH_QUEUE_PATH", None)
    finally:
        if saved is not None:
            os.environ["REDIS_URL"] = saved

    print(f"\n{'all queues self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
