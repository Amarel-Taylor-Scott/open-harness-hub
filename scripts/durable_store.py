#!/usr/bin/env python3
"""scripts.durable_store — the durability + fault-tolerance layer (stdlib sqlite3; no broker, no cloud).

Fixes the flagged fragility / non-durableness: the in-process event bus loses everything on restart,
there is no durable task ownership, no idempotency, no retry/DLQ. This is the constraint-respecting fix
— a single file-backed, ACID, crash-safe SQLite store (WAL mode) providing:

  * **Durable event log** — every bus event persisted; survives restart (hydrate the bus on startup).
  * **Durable job queue** — `enqueue → claim(lease) → ack | nack(retry) → DLQ`. A crashed worker's
    lease expires and the job is re-claimed (at-least-once). Equivalent to the SKIP-LOCKED pattern;
    SQLite `BEGIN IMMEDIATE` serializes claims so two workers never take the same job.
  * **Idempotency table** — `mark_processed(consumer, message_id)` dedupes at-least-once redelivery.
  * **Transactional outbox** — enqueue side-effects durably, relay once (no dual-write loss).

THREAD-SAFE: the connection is opened with ``check_same_thread=False`` and every operation is serialized
through an ``RLock`` — so it works under the admin server's ThreadingHTTPServer (each request a thread).

Deterministic + offline: time is INJECTED (`now`), never read from a clock, so the self-test is exact
and the queue stays testable. This is the local stand-in for a broker/KEDA fleet — same contract, swap
the backend later (see `research/worker-fleet-architecture.md`).

CLI:
    python3 scripts/durable_store.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Iterable

_REPO = Path(__file__).resolve().parents[1]
DEFAULT_DB = _REPO / ".agent" / "durable.db"
JOB_STATES = ("queued", "claimed", "done", "dead")
DEFAULT_MAX_ATTEMPTS = 5  # retries before a job is dead-lettered


class DurableStore:
    """ACID, crash-safe (WAL), thread-safe durable event log + job queue + idempotency + outbox."""

    def __init__(self, path: str | Path = DEFAULT_DB) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        # check_same_thread=False + the lock = safe under ThreadingHTTPServer / worker threads.
        self.conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")   # crash-safe: committed txns survive a kill
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA busy_timeout=5000")  # multi-PROCESS: wait, don't error, on a held lock
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            c = self.conn
            c.execute("""CREATE TABLE IF NOT EXISTS events(
                id INTEGER PRIMARY KEY AUTOINCREMENT, seq INTEGER, kind TEXT, stage TEXT, component TEXT,
                correlation_id TEXT, object_ref TEXT, payload_json TEXT, ts TEXT)""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_events_corr ON events(correlation_id)")
            c.execute("""CREATE TABLE IF NOT EXISTS jobs(
                id INTEGER PRIMARY KEY AUTOINCREMENT, queue TEXT NOT NULL, payload_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued', idempotency_key TEXT UNIQUE,
                attempts INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL DEFAULT 5,
                claimed_by TEXT, lease_until INTEGER NOT NULL DEFAULT 0, error TEXT)""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_jobs_q ON jobs(queue, status, lease_until)")
            c.execute("""CREATE TABLE IF NOT EXISTS processed(
                consumer TEXT NOT NULL, message_id TEXT NOT NULL, PRIMARY KEY(consumer, message_id))""")
            c.execute("""CREATE TABLE IF NOT EXISTS outbox(
                id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT NOT NULL, payload_json TEXT NOT NULL,
                published INTEGER NOT NULL DEFAULT 0)""")
            c.execute("CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT)")

    def close(self) -> None:
        with self._lock:
            self.conn.close()

    # ── durable event log ────────────────────────────────────────────────────
    def append_event(self, ev: dict) -> None:
        with self._lock:
            self.conn.execute(
                "INSERT INTO events(seq,kind,stage,component,correlation_id,object_ref,payload_json,ts)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (ev.get("seq"), ev.get("kind"), ev.get("stage"), ev.get("component"),
                 ev.get("correlation_id"), ev.get("object_ref"),
                 json.dumps(ev.get("payload") or {}), ev.get("ts", "")))

    def recent_events(self, limit: int = 500) -> list[dict]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT seq,kind,stage,component,correlation_id,object_ref,payload_json,ts"
                " FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        out = [{"seq": r[0], "kind": r[1], "stage": r[2], "component": r[3], "correlation_id": r[4],
                "object_ref": r[5], "payload": json.loads(r[6] or "{}"), "ts": r[7]} for r in rows]
        return list(reversed(out))  # chronological (oldest→newest)

    def events_by_correlation(self, correlation_id: str) -> list[dict]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT seq,kind,stage,component,correlation_id,object_ref,payload_json"
                " FROM events WHERE correlation_id=? ORDER BY id", (correlation_id,)).fetchall()
        return [{"seq": r[0], "kind": r[1], "stage": r[2], "component": r[3], "correlation_id": r[4],
                 "object_ref": r[5], "payload": json.loads(r[6] or "{}")} for r in rows]

    def event_count(self) -> int:
        with self._lock:
            return self.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    def clear_events(self) -> None:
        with self._lock:
            self.conn.execute("DELETE FROM events")

    # ── durable job queue ──────────────────────────────────────────────────────
    def enqueue(self, queue: str, payload: Any, *, idempotency_key: str | None = None,
                max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> dict:
        """Enqueue a job. With an idempotency_key, a duplicate enqueue is a no-op (returns the existing id)."""
        with self._lock:
            if idempotency_key:
                row = self.conn.execute("SELECT id FROM jobs WHERE idempotency_key=?", (idempotency_key,)).fetchone()
                if row:
                    return {"id": row[0], "duplicate": True}
            cur = self.conn.execute(
                "INSERT INTO jobs(queue,payload_json,status,idempotency_key,attempts,max_attempts)"
                " VALUES(?,?,'queued',?,0,?)", (queue, json.dumps(payload, sort_keys=True), idempotency_key, max_attempts))
            return {"id": cur.lastrowid, "duplicate": False}

    def claim(self, queue: str, *, worker: str, lease_seconds: int, now: int) -> dict | None:
        """Atomically claim the oldest available job (queued, or claimed-but-lease-expired). Increments attempts."""
        with self._lock:
            c = self.conn
            c.execute("BEGIN IMMEDIATE")
            try:
                row = c.execute(
                    "SELECT id,payload_json,attempts,max_attempts FROM jobs"
                    " WHERE queue=? AND (status='queued' OR (status='claimed' AND lease_until<=?))"
                    " ORDER BY id LIMIT 1", (queue, now)).fetchone()
                if not row:
                    c.execute("COMMIT")
                    return None
                jid, payload, attempts, maxa = row
                c.execute("UPDATE jobs SET status='claimed', claimed_by=?, lease_until=?, attempts=attempts+1 WHERE id=?",
                          (worker, now + lease_seconds, jid))
                c.execute("COMMIT")
                return {"id": jid, "payload": json.loads(payload), "attempts": attempts + 1, "max_attempts": maxa}
            except Exception:
                c.execute("ROLLBACK")
                raise

    def ack(self, job_id: int) -> None:
        with self._lock:
            self.conn.execute("UPDATE jobs SET status='done' WHERE id=?", (job_id,))

    def nack(self, job_id: int, *, error: str = "", permanent: bool = False) -> str:
        """Requeue for retry, or dead-letter once attempts have reached max_attempts. A PERMANENT failure
        (e.g. a schema-invalid command that can never succeed) dead-letters IMMEDIATELY — no retry budget is
        burned reprocessing a job that cannot pass. Returns the new status."""
        with self._lock:
            row = self.conn.execute("SELECT attempts,max_attempts FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row:
                return "missing"
            attempts, maxa = row
            if permanent or attempts >= maxa:
                self.conn.execute("UPDATE jobs SET status='dead', error=? WHERE id=?", (error, job_id))
                return "dead"
            self.conn.execute("UPDATE jobs SET status='queued', lease_until=0, error=? WHERE id=?", (error, job_id))
            return "queued"

    def stats(self, queue: str) -> dict:
        with self._lock:
            rows = self.conn.execute("SELECT status,COUNT(*) FROM jobs WHERE queue=? GROUP BY status", (queue,)).fetchall()
        d = {s: 0 for s in JOB_STATES}
        for s, n in rows:
            d[s] = n
        return d

    def dead_letters(self, queue: str) -> list[dict]:
        with self._lock:
            rows = self.conn.execute("SELECT id,payload_json,error FROM jobs WHERE queue=? AND status='dead' ORDER BY id", (queue,)).fetchall()
        return [{"id": r[0], "payload": json.loads(r[1]), "error": r[2]} for r in rows]

    # ── idempotent consumer ────────────────────────────────────────────────────
    def mark_processed(self, consumer: str, message_id: str) -> bool:
        """True if newly recorded (process it); False if already processed (skip the duplicate)."""
        with self._lock:
            try:
                self.conn.execute("INSERT INTO processed(consumer,message_id) VALUES(?,?)", (consumer, message_id))
                return True
            except sqlite3.IntegrityError:
                return False

    # ── transactional outbox ───────────────────────────────────────────────────
    def outbox_add(self, topic: str, payload: Any) -> int:
        with self._lock:
            cur = self.conn.execute("INSERT INTO outbox(topic,payload_json,published) VALUES(?,?,0)",
                                    (topic, json.dumps(payload, sort_keys=True)))
            return cur.lastrowid

    def outbox_relay(self, limit: int = 100) -> list[dict]:
        with self._lock:
            rows = self.conn.execute("SELECT id,topic,payload_json FROM outbox WHERE published=0 ORDER BY id LIMIT ?", (limit,)).fetchall()
            if rows:
                self.conn.executemany("UPDATE outbox SET published=1 WHERE id=?", [(r[0],) for r in rows])
        return [{"id": r[0], "topic": r[1], "payload": json.loads(r[2])} for r in rows]

    # ── meta (durable status surface — the dashboard reads this projection) ────
    def set_meta(self, key: str, value: str) -> None:
        with self._lock:
            self.conn.execute("INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

    def get_meta(self, key: str, default: str = "") -> str:
        with self._lock:
            row = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def queue_overview(self) -> dict:
        """Per-queue {queued,claimed,done,dead} across all queues — the work-plane projection."""
        with self._lock:
            rows = self.conn.execute("SELECT queue,status,COUNT(*) FROM jobs GROUP BY queue,status").fetchall()
        out: dict[str, dict] = {}
        for q, st, n in rows:
            out.setdefault(q, {s: 0 for s in JOB_STATES})[st] = n
        return out


def _self_test() -> int:
    import tempfile

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    tmp = tempfile.mkdtemp(prefix="baltor-durable-")
    dbp = str(Path(tmp) / "t.db")

    # ── DURABILITY across process restart (the core fix): write, CLOSE, REOPEN, assert persisted ──
    s = DurableStore(dbp)
    s.append_event({"seq": 1, "kind": "pipeline.started", "correlation_id": "c1", "payload": {"a": 1}})
    s.append_event({"seq": 2, "kind": "receipt_issued", "correlation_id": "c1", "payload": {"answer": 10}})
    eid = s.enqueue("ingest", {"corpus": "cfpb"}, idempotency_key="cfpb-1")["id"]
    s.close()
    s = DurableStore(dbp)  # reopen = a fresh "process"
    check("events SURVIVE restart", s.event_count() == 2, str(s.event_count()))
    check("recent_events chronological + parsed", [e["kind"] for e in s.recent_events()] == ["pipeline.started", "receipt_issued"])
    check("by_correlation filters", len(s.events_by_correlation("c1")) == 2)
    check("queued job SURVIVES restart", s.stats("ingest")["queued"] == 1)

    # ── thread-safety: concurrent appends from many threads (the ThreadingHTTPServer case) ──
    def _worker(n):
        for i in range(20):
            s.append_event({"seq": 1000 + n * 100 + i, "kind": "rot.detected", "correlation_id": f"t{n}"})
    before = s.event_count()
    threads = [threading.Thread(target=_worker, args=(n,)) for n in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    check("concurrent appends from 5 threads all persisted (no thread error)", s.event_count() == before + 100, str(s.event_count() - before))

    # ── idempotent enqueue ──
    dup = s.enqueue("ingest", {"corpus": "cfpb"}, idempotency_key="cfpb-1")
    check("duplicate enqueue is a no-op (same id)", dup["duplicate"] and dup["id"] == eid)
    check("still only one queued job", s.stats("ingest")["queued"] == 1)

    # ── claim → ack ──
    j = s.claim("ingest", worker="w1", lease_seconds=30, now=100)
    check("claim returns the job", j and j["id"] == eid and j["payload"]["corpus"] == "cfpb")
    check("claimed not re-claimable while lease holds", s.claim("ingest", worker="w2", lease_seconds=30, now=110) is None)
    s.ack(j["id"])
    check("ack → done", s.stats("ingest")["done"] == 1)

    # ── crashed-worker recovery: lease expiry → re-claim (at-least-once) ──
    s.enqueue("work", {"n": 1})
    a = s.claim("work", worker="w1", lease_seconds=30, now=100)   # w1 claims then "crashes"
    again = s.claim("work", worker="w2", lease_seconds=30, now=200)  # after lease expiry
    check("expired lease lets another worker re-claim", again and again["id"] == a["id"] and again["attempts"] == 2)

    # ── retry → DLQ ──
    jid = s.enqueue("flaky", {"x": 1}, max_attempts=2)["id"]
    s.claim("flaky", worker="w", lease_seconds=10, now=0); st1 = s.nack(jid, error="boom")   # attempts=1 → requeue
    s.claim("flaky", worker="w", lease_seconds=10, now=0); st2 = s.nack(jid, error="boom")   # attempts=2 → dead
    check("first nack requeues, second dead-letters", st1 == "queued" and st2 == "dead")
    check("dead-letter retrievable with its error", [d["id"] for d in s.dead_letters("flaky")] == [jid])

    # ── FIFO order ──
    for n in ("A", "B", "C"):
        s.enqueue("fifo", {"n": n})
    order = [s.claim("fifo", worker="w", lease_seconds=5, now=0)["payload"]["n"] for _ in range(3)]
    check("FIFO claim order A,B,C", order == ["A", "B", "C"], str(order))

    # ── idempotency table ──
    check("mark_processed: first True, duplicate False",
          s.mark_processed("c", "m1") is True and s.mark_processed("c", "m1") is False)

    # ── transactional outbox ──
    s.outbox_add("evt", {"k": 1}); s.outbox_add("evt", {"k": 2})
    relayed = s.outbox_relay()
    check("outbox relays unpublished once", len(relayed) == 2 and s.outbox_relay() == [])

    # ── meta status surface + queue overview projection ──
    s.set_meta("durable_status", "ok"); s.set_meta("durable_status", "red")
    check("meta upsert (last write wins)", s.get_meta("durable_status") == "red")
    ov = s.queue_overview()
    check("queue_overview reports per-queue stats",
          ov.get("ingest", {}).get("done") == 1 and ov.get("flaky", {}).get("dead") == 1 and ov.get("fifo", {}).get("claimed") == 3, str(ov))

    # ── clear_events ──
    s.clear_events()
    check("clear_events empties the log", s.event_count() == 0)
    s.close()

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'all durable_store self-tests passed (events + jobs survive restart; thread-safe; lease re-claim; retry→DLQ; idempotency; outbox; FIFO).' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Durable event log + job queue + idempotency + outbox (sqlite3).")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(list(argv) if argv is not None else None)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
