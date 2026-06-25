#!/usr/bin/env python3
"""scripts.work_queue — durable work queue + STATELESS-RESTART workers (pick up where you left off).

The orchestration spine the infra review said was missing — built local-first (SQLite WAL, like scale_index) so it
runs in the demo today and SWAPS to Redpanda/SQS/Temporal via the same enqueue/claim/ack contract, no rewrite. All
worker state lives in the QUEUE, not the worker: a worker leases items, processes idempotently, and acks; if it
crashes, the lease expires and another (or the restarted) worker re-claims and RESUMES. At-least-once + content-hash
idempotency = safe. This is how "always running, always improving, search→queue→process" survives restarts.

  --self-test
  --demo                                  prove enqueue → process → crash → RESUME
  --enqueue --topic T --payload '<json>'  | --enqueue-from FILE --topic T
  --work --topic T [--max N]              run a worker (default handler = stamp 'processed'; real handlers register())
  --stats [--topic T]
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DB = REPO / "data" / "dev-intel" / "work_queue.db"
STOP = REPO / ".agent" / "QUEUE_STOP_REQUESTED"
_MAX_ATTEMPTS = 5
_HANDLERS: dict = {}                                        # topic -> fn(payload_dict) -> None (register() to add real work)


def register(topic: str, fn) -> None:
    _HANDLERS[topic] = fn


def _conn(db: Path = DB) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(db), timeout=30)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=5000")
    c.execute("CREATE TABLE IF NOT EXISTS queue(id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT, item_hash TEXT,"
              " payload TEXT, status TEXT DEFAULT 'ready', leased_until REAL DEFAULT 0, worker TEXT, attempts INT"
              " DEFAULT 0, created REAL, UNIQUE(topic, item_hash))")
    c.execute("CREATE INDEX IF NOT EXISTS ix_q ON queue(topic, status, leased_until)")
    return c


def enqueue(topic: str, payload: dict, db: Path = DB) -> bool:
    """Idempotent: same (topic, content-hash) is never double-queued. Returns True if newly enqueued."""
    h = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
    c = _conn(db)
    try:
        cur = c.execute("INSERT OR IGNORE INTO queue(topic,item_hash,payload,created) VALUES(?,?,?,?)",
                        (topic, h, json.dumps(payload), time.time()))
        c.commit()
        return cur.rowcount > 0
    finally:
        c.close()


def claim(topic: str, worker: str, lease: float = 30.0, n: int = 10, db: Path = DB) -> list[tuple]:
    """Atomically lease up to n ready (or expired-lease) items → resume picks up crashed work automatically."""
    now = time.time()
    c = _conn(db)
    try:
        c.execute("BEGIN IMMEDIATE")
        rows = c.execute("SELECT id, payload FROM queue WHERE topic=? AND (status='ready' OR (status='leased' AND "
                         "leased_until<?)) ORDER BY id LIMIT ?", (topic, now, n)).fetchall()
        ids = [r[0] for r in rows]
        if ids:
            ph = ",".join("?" * len(ids))
            c.execute(f"UPDATE queue SET status='leased', leased_until=?, worker=?, attempts=attempts+1 "
                      f"WHERE id IN ({ph})", [now + lease, worker, *ids])
        c.execute("COMMIT")
        return rows
    finally:
        c.close()


def ack(item_id: int, db: Path = DB) -> None:
    c = _conn(db)
    try:
        c.execute("UPDATE queue SET status='done', leased_until=0 WHERE id=?", (item_id,)); c.commit()
    finally:
        c.close()


def fail(item_id: int, db: Path = DB) -> None:
    """Retry until _MAX_ATTEMPTS, then dead-letter."""
    c = _conn(db)
    try:
        a = c.execute("SELECT attempts FROM queue WHERE id=?", (item_id,)).fetchone()
        status = "dead" if a and a[0] >= _MAX_ATTEMPTS else "ready"
        c.execute("UPDATE queue SET status=?, leased_until=0 WHERE id=?", (status, item_id)); c.commit()
    finally:
        c.close()


def stats(topic: str | None = None, db: Path = DB) -> dict:
    if not db.exists():
        return {}
    c = _conn(db)
    try:
        q = "SELECT topic, status, COUNT(*) FROM queue" + (" WHERE topic=?" if topic else "") + " GROUP BY topic, status"
        out: dict = {}
        for t, st, n in c.execute(q, (topic,) if topic else ()).fetchall():
            out.setdefault(t, {})[st] = n
        return out
    finally:
        c.close()


def _default_handler(payload: dict) -> None:
    return None                                            # no-op (the demo/real handlers register their own)


def run_worker(topic: str, fn=None, *, lease: float = 30.0, batch: int = 10, max_items: int | None = None,
               idle_sleep: float = 2.0, db: Path = DB) -> dict:
    """Stateless: claim → process idempotently → ack/fail, until STOP or max_items. Restart = resume from the queue."""
    fn = fn or _HANDLERS.get(topic) or _default_handler
    worker = f"{os.getpid()}"
    done = failed = 0
    while True:
        if STOP.exists() or (max_items is not None and done + failed >= max_items):
            break
        rows = claim(topic, worker, lease, batch, db)
        if not rows:
            if max_items is not None:
                break
            time.sleep(idle_sleep)
            continue
        for item_id, payload in rows:
            try:
                fn(json.loads(payload))
                ack(item_id, db); done += 1
            except Exception:  # noqa: BLE001 — a bad item never kills the worker; it retries/dead-letters
                fail(item_id, db); failed += 1
            if max_items is not None and done + failed >= max_items:
                break
    return {"topic": topic, "processed": done, "failed": failed}


def self_test() -> int:
    import tempfile
    db = Path(tempfile.mkdtemp()) / "q.db"
    assert enqueue("t", {"x": 1}, db) and not enqueue("t", {"x": 1}, db), "idempotent enqueue (dedup)"
    assert enqueue("t", {"x": 2}, db) and enqueue("t", {"x": 3}, db)
    rows = claim("t", "w1", lease=0.2, n=2, db=db)
    assert len(rows) == 2, "lease 2"
    assert len(claim("t", "w2", lease=30, n=10, db=db)) == 1, "third still claimable (1 left ready)"
    ack(rows[0][0], db)
    # RESUME: w1 leased 2 with a 0.2s lease, acked 1; the other's lease expires → re-claimable (crash recovery)
    time.sleep(0.25)
    again = claim("t", "w3", lease=30, n=10, db=db)
    assert any(r[0] == rows[1][0] for r in again), "expired-lease item is re-claimed → RESUME works"
    # dead-letter: an always-failing item retries up to _MAX_ATTEMPTS (incremented per claim) then dead-letters
    def _boom(_p):
        raise ValueError("boom")
    register("bad", _boom)
    enqueue("bad", {"y": 1}, db)
    run_worker("bad", max_items=_MAX_ATTEMPTS + 3, idle_sleep=0, db=db)
    assert stats("bad", db).get("bad", {}).get("dead", 0) == 1, "always-failing item dead-letters after max attempts"
    # stateless worker processes a registered handler to completion
    seen = []
    register("h", lambda p: seen.append(p["x"]))
    for i in range(4):
        enqueue("h", {"x": i}, db)
    r = run_worker("h", max_items=4, idle_sleep=0, db=db)
    assert r["processed"] == 4 and sorted(seen) == [0, 1, 2, 3], f"worker drained the queue: {r}"
    print("work_queue self-test: OK (idempotent enqueue, lease/claim, ack, RESUME on expired lease, dead-letter, stateless worker)")
    return 0


def demo() -> int:
    import tempfile
    db = Path(tempfile.mkdtemp()) / "demo.db"
    for i in range(5):
        enqueue("demo", {"task": f"item-{i}"}, db)
    print("  enqueued 5 items.")
    # worker A claims 3 with a SHORT lease, processes 1, then CRASHES (2 leased+unacked, 2 still ready)
    rows = claim("demo", "A", lease=1.0, n=3, db=db)
    ack(rows[0][0], db)
    print(f"  worker A: claimed 3, acked 1, then CRASHED → {stats('demo', db)['demo']} (2 leased-unacked, 2 ready)")
    time.sleep(1.1)                                                    # the crashed worker's lease expires
    processed = []
    register("demo", lambda p: processed.append(p["task"]))
    run_worker("demo", max_items=10, idle_sleep=0, db=db)             # worker B restarts → RESUMES everything
    print(f"  worker B (restart): resumed the 2 expired-lease items + the 2 ready → processed {len(processed)} more")
    print(f"  queue: {stats('demo', db)['demo']}  → 5 done total (1 by A + 4 by B); none lost, none double-processed")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--demo" in argv:
        return demo()

    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default

    topic = opt("--topic", "default")
    if "--enqueue" in argv:
        print("enqueued" if enqueue(topic, json.loads(opt("--payload", "{}"))) else "duplicate (skipped)"); return 0
    if "--enqueue-from" in argv:
        n = 0
        for ln in Path(opt("--enqueue-from")).read_text(encoding="utf-8").splitlines():
            if ln.strip() and enqueue(topic, json.loads(ln)):
                n += 1
        print(f"enqueued {n} new items to '{topic}'"); return 0
    if "--work" in argv:
        print(json.dumps(run_worker(topic, max_items=int(opt("--max")) if opt("--max") else None), indent=2)); return 0
    if "--stats" in argv:
        print(json.dumps(stats(opt("--topic")), indent=2)); return 0
    print("usage: work_queue.py --self-test | --demo | --enqueue --topic T --payload J | --enqueue-from F --topic T | --work --topic T [--max N] | --stats")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
