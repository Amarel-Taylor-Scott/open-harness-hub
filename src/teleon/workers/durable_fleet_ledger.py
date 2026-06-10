"""src.baltor.workers.durable_fleet_ledger — the DURABLE (SQLite) capability-task ledger.

The in-memory FleetLedger is the proven contract; this is its durable, CROSS-PROCESS twin so the live
supervisor's spawn pass acts on REAL persisted queued work and multiple worker processes can claim against
ONE ledger (the "FleetLedger on the live dispatch path"). Same method shape as FleetLedger (drop-in for the
subset the live path needs). Atomic claim uses `BEGIN IMMEDIATE` (SQLite) — the analog of Postgres
`SELECT … FOR UPDATE SKIP LOCKED`; a row is handed to EXACTLY ONE worker. Lives in the shared durable DB
(honors BALTOR_DURABLE_DB); separate tables, not a second runtime. ISO timestamps (real wall-clock across
processes; injectable for deterministic tests).
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path

from .fleet_ledger import CLAIMED, DEAD, FAILED, QUEUED, RETRY_WAIT, RUNNING, SUCCEEDED, _hid, _plus_s

_REPO = Path(__file__).resolve().parents[3]
DEFAULT_DB = os.environ.get("BALTOR_DURABLE_DB") or str(_REPO / ".agent" / "durable.db")


def _iso(now: str | None) -> str:
    return now if now else time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class DurableFleetLedger:
    def __init__(self, path: str | Path = DEFAULT_DB) -> None:
        self.path = str(path)
        d = os.path.dirname(self.path)
        if d:
            os.makedirs(d, exist_ok=True)
        self.conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self._init_schema()

    def _init_schema(self) -> None:
        c = self.conn
        c.execute("""CREATE TABLE IF NOT EXISTS capability_workers(
            worker_id TEXT PRIMARY KEY, capability_ids_json TEXT, status TEXT, max_concurrency INTEGER,
            active_task_count INTEGER, started_at TEXT, heartbeat_at TEXT, last_claim_at TEXT,
            total_tasks_processed INTEGER, total_failures INTEGER)""")
        c.execute("""CREATE TABLE IF NOT EXISTS capability_tasks(
            task_id TEXT PRIMARY KEY, tenant_id TEXT, capability_id TEXT, idempotency_key TEXT UNIQUE,
            status TEXT, priority_class TEXT, queue_name TEXT, deadline_at TEXT, not_before TEXT,
            max_attempts INTEGER, attempt INTEGER, lease_owner TEXT, lease_until TEXT, created_at TEXT,
            claimed_at TEXT, started_at TEXT, finished_at TEXT, failed_at TEXT, error_json TEXT,
            result_ids_json TEXT, depends_on_json TEXT, payload_json TEXT)""")
        # migrations: add columns a pre-existing table may lack (older durable DBs)
        cols = {r[1] for r in c.execute("PRAGMA table_info(capability_tasks)")}
        if "depends_on_json" not in cols:
            c.execute("ALTER TABLE capability_tasks ADD COLUMN depends_on_json TEXT DEFAULT '[]'")
        if "payload_json" not in cols:
            c.execute("ALTER TABLE capability_tasks ADD COLUMN payload_json TEXT DEFAULT '{}'")

    # ── workers ──────────────────────────────────────────────────────────────
    def register_worker(self, *, worker_id: str, capability_ids: list, max_concurrency: int = 1,
                        now: str | None = None) -> dict:
        t = _iso(now)
        self.conn.execute("""INSERT INTO capability_workers(worker_id,capability_ids_json,status,max_concurrency,
            active_task_count,started_at,heartbeat_at,last_claim_at,total_tasks_processed,total_failures)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(worker_id) DO UPDATE SET capability_ids_json=excluded.capability_ids_json,
            status=excluded.status,heartbeat_at=excluded.heartbeat_at""",
            (worker_id, json.dumps(list(capability_ids)), "warm", max_concurrency, 0, t, t, "", 0, 0))
        return self.worker(worker_id)

    def set_worker_status(self, worker_id: str, status: str, *, now: str | None = None) -> None:
        self.conn.execute("UPDATE capability_workers SET status=?,heartbeat_at=? WHERE worker_id=?",
                          (status, _iso(now), worker_id))

    def worker(self, worker_id: str) -> dict | None:
        r = self.conn.execute("SELECT * FROM capability_workers WHERE worker_id=?", (worker_id,)).fetchone()
        return dict(r) if r else None

    def live_workers(self, capability_id: str | None = None, *, now: str | None = None) -> list[dict]:
        out = []
        for r in self.conn.execute("SELECT * FROM capability_workers WHERE status NOT IN ('stopped','failed')"):
            d = dict(r); caps = json.loads(d["capability_ids_json"])
            d["capability_ids"] = caps
            if capability_id is None or capability_id in caps:
                out.append(d)
        return out

    # ── tasks ────────────────────────────────────────────────────────────────
    def enqueue_task(self, *, tenant_id: str, capability_id: str, idempotency_key: str, now: str | None = None,
                     priority_class: str = "standard", queue_name: str = "", deadline_at: str = "",
                     not_before: str = "", max_attempts: int = 3, depends_on: list | None = None,
                     payload: dict | None = None) -> dict:
        t = _iso(now)
        existing = self.conn.execute("SELECT task_id FROM capability_tasks WHERE idempotency_key=?",
                                     (idempotency_key,)).fetchone()
        if existing:
            return self.task(existing["task_id"])          # idempotent: no duplicate
        tid = _hid("task-", tenant_id, capability_id, idempotency_key)
        self.conn.execute("""INSERT INTO capability_tasks(task_id,tenant_id,capability_id,idempotency_key,status,
            priority_class,queue_name,deadline_at,not_before,max_attempts,attempt,lease_owner,lease_until,
            created_at,claimed_at,started_at,finished_at,failed_at,error_json,result_ids_json,depends_on_json,payload_json)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (tid, tenant_id, capability_id, idempotency_key, QUEUED, priority_class, queue_name, deadline_at,
             not_before, max_attempts, 0, "", "", t, "", "", "", "", "{}", "[]", json.dumps(list(depends_on or [])),
             json.dumps(payload or {})))
        return self.task(tid)

    def _deps_satisfied(self, depends_on_json: str | None) -> bool:
        """A task is claimable only when EVERY task it depends on has succeeded (dependency ordering)."""
        deps = json.loads(depends_on_json or "[]")
        for dep_id in deps:
            r = self.conn.execute("SELECT status FROM capability_tasks WHERE task_id=?", (dep_id,)).fetchone()
            if r is None or r["status"] != SUCCEEDED:
                return False
        return True

    def claim_task(self, *, worker_id: str, capability_id: str, now: str | None = None,
                   lease_seconds: int = 60) -> dict | None:
        """ATOMIC claim: the oldest ready task for this capability → EXACTLY ONE worker. The
        `BEGIN IMMEDIATE` + the `status=QUEUED` guard in the UPDATE make concurrent claims race-safe across
        processes (the SQLite analog of FOR UPDATE SKIP LOCKED)."""
        t = _iso(now)
        c = self.conn
        c.execute("BEGIN IMMEDIATE")
        try:
            # oldest-first candidates; pick the first whose dependencies are ALL satisfied (dependency order)
            cands = c.execute(
                """SELECT task_id, depends_on_json FROM capability_tasks WHERE status=? AND capability_id=?
                   AND (not_before='' OR not_before<=?) ORDER BY created_at, task_id""",
                (QUEUED, capability_id, t)).fetchall()
            tid = next((r["task_id"] for r in cands if self._deps_satisfied(r["depends_on_json"])), None)
            if tid is None:
                c.execute("COMMIT"); return None            # nothing ready (queue empty or all dep-blocked)
            cur = c.execute("""UPDATE capability_tasks SET status=?,lease_owner=?,lease_until=?,claimed_at=?,
                attempt=attempt WHERE task_id=? AND status=?""",
                (CLAIMED, worker_id, _plus_s(t, lease_seconds), t, tid, QUEUED))
            if cur.rowcount != 1:                            # someone else won the race
                c.execute("COMMIT"); return None
            c.execute("UPDATE capability_workers SET last_claim_at=? WHERE worker_id=?", (t, worker_id))
            c.execute("COMMIT")
            return self.task(tid)
        except Exception:
            c.execute("ROLLBACK"); raise

    def start_task(self, task_id: str, worker_id: str, now: str | None = None) -> dict:
        self._require_owner(task_id, worker_id)
        self.conn.execute("UPDATE capability_tasks SET status=?,started_at=? WHERE task_id=?",
                          (RUNNING, _iso(now), task_id))
        return self.task(task_id)

    def ack_task(self, task_id: str, worker_id: str, result_ids: list | None = None, now: str | None = None) -> dict:
        self._require_owner(task_id, worker_id)
        self.conn.execute("UPDATE capability_tasks SET status=?,finished_at=?,lease_until='',result_ids_json=? WHERE task_id=?",
                          (SUCCEEDED, _iso(now), json.dumps(result_ids or []), task_id))
        self.conn.execute("UPDATE capability_workers SET total_tasks_processed=total_tasks_processed+1 WHERE worker_id=?", (worker_id,))
        return self.task(task_id)

    def nack_task(self, task_id: str, worker_id: str, error: dict, *, retryable: bool, now: str | None = None) -> dict:
        self._require_owner(task_id, worker_id)
        t = _iso(now); task = self.task(task_id); attempt = task["attempt"] + 1
        dead = (not retryable) or attempt >= task["max_attempts"]
        self.conn.execute("""UPDATE capability_tasks SET status=?,failed_at=?,error_json=?,attempt=?,lease_owner='',lease_until='' WHERE task_id=?""",
                          (DEAD if dead else QUEUED, t, json.dumps(error), attempt, task_id))
        self.conn.execute("UPDATE capability_workers SET total_failures=total_failures+1 WHERE worker_id=?", (worker_id,))
        return self.task(task_id)

    def reclaim_expired_leases(self, now: str | None = None) -> list[str]:
        t = _iso(now)
        rows = self.conn.execute("SELECT task_id FROM capability_tasks WHERE status IN (?,?) AND lease_until!='' AND lease_until<?",
                                 (CLAIMED, RUNNING, t)).fetchall()
        ids = [r["task_id"] for r in rows]
        for tid in ids:
            self.conn.execute("UPDATE capability_tasks SET status=?,lease_owner='',lease_until='' WHERE task_id=?", (QUEUED, tid))
        return ids

    def _require_owner(self, task_id: str, worker_id: str) -> None:
        r = self.conn.execute("SELECT lease_owner FROM capability_tasks WHERE task_id=?", (task_id,)).fetchone()
        if not r or r["lease_owner"] != worker_id:
            raise ValueError(f"task {task_id} not owned by {worker_id} (claim first)")

    # ── reads ──────────────────────────────────────────────────────────────
    def task(self, task_id: str) -> dict | None:
        r = self.conn.execute("SELECT * FROM capability_tasks WHERE task_id=?", (task_id,)).fetchone()
        return dict(r) if r else None

    def queued_tasks(self, capability_id: str | None = None) -> list[dict]:
        if capability_id:
            rows = self.conn.execute("SELECT * FROM capability_tasks WHERE status=? AND capability_id=? ORDER BY created_at,task_id", (QUEUED, capability_id))
        else:
            rows = self.conn.execute("SELECT * FROM capability_tasks WHERE status=? ORDER BY created_at,task_id", (QUEUED,))
        return [dict(r) for r in rows]

    def tasks_by_status(self, status: str) -> list[dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM capability_tasks WHERE status=? ORDER BY task_id", (status,))]

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass


__all__ = ["DurableFleetLedger", "DEFAULT_DB"]
