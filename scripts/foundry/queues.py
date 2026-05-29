#!/usr/bin/env python3
"""Foundry queues — the broker adapter (the "Celery layer", kept light).

`worker.py` already provides the worker loop + retry + dead-letter + a `Queue`
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
from pathlib import Path
from typing import Any

DEFAULT_QUEUE_KEY = "ohh:foundry:jobs"


class RedisQueue:
    """Redis-list queue implementing `worker.Queue`. KEDA scales the worker fleet on
    `LLEN(key)`; nack re-queues; dead-letter goes to ``{key}:dead`` for inspection."""

    def __init__(self, client: Any, key: str = DEFAULT_QUEUE_KEY) -> None:
        self.client = client
        self.key = key
        self.dead_key = key + ":dead"

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
        self.client.rpush(self.dead_key, json.dumps(job))

    def depth(self) -> int:
        return int(self.client.llen(self.key))


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
            job["_seq"] = seq   # so ack/nack/dead_letter can target this row
            return job
        finally:
            c.close()

    def ack(self, job: dict) -> None:
        c = self._con()
        c.execute("DELETE FROM jobs WHERE seq=?", (job.get("_seq"),))
        c.close()

    def nack(self, job: dict) -> None:   # persist _attempts so retry/dead-letter survives re-pull
        body = {k: v for k, v in job.items() if k != "_seq"}
        c = self._con()
        c.execute("UPDATE jobs SET status='pending', body=? WHERE seq=?", (json.dumps(body), job.get("_seq")))
        c.close()

    def dead_letter(self, job: dict) -> None:
        c = self._con()
        c.execute("UPDATE jobs SET status='dead' WHERE seq=?", (job.get("_seq"),))
        c.close()

    def depth(self) -> int:
        c = self._con()
        n = c.execute("SELECT COUNT(*) FROM jobs WHERE qkey=? AND status='pending'", (self.key,)).fetchone()[0]
        c.close()
        return int(n)


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
    q.dead_letter({"partition": "poison"})
    check("dead-letter goes to {key}:dead", r.llen("t:jobs:dead") == 1)

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
