"""src.baltor.workers.supervisor_store — DURABLE, cross-process supervisor coordination (OPP-supervisor-
scaling-live). The durable analog of the in-memory SupervisorLedger: it persists the control-plane
coordination state in SQLite so MULTIPLE `baltor_flywheel.py --watch` processes coordinate safely against
ONE ledger.

Source of truth = this DB (lives in the existing durable DB file by default, `.agent/durable.db`). Leases
use `BEGIN IMMEDIATE` compare-and-set so exactly one process wins (SQLite analog of Postgres
`SELECT … FOR UPDATE SKIP LOCKED` / a conditional UPDATE). Decisions are idempotent by a UNIQUE
idempotency_key so two racing supervisors never enqueue duplicate work. WAL + busy_timeout make concurrent
processes safe.

Eight tables: supervisor_instances · supervisor_leases · supervisor_shards · supervisor_ticks ·
supervisor_decisions · supervisor_capacity_snapshots · supervisor_spawn_decisions · supervisor_failovers.

This is a CONTROL-PLANE store: it records who-coordinates-what and the decisions; it never executes heavy
work and never claims tasks (workers do that via the task ledger's atomic claim).
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
# co-locate with the EXISTING durable DB (shared file, separate tables); honor BALTOR_DURABLE_DB so the
# admin server, watch loop, and projection all read the same store.
DEFAULT_DB = os.environ.get("BALTOR_DURABLE_DB") or str(_REPO / ".agent" / "durable.db")

DEFAULT_SHARDS = [
    ("control", "control"), ("proof_health", "control"), ("worker_health", "control"),
    ("fleet_capacity", "control"), ("watch_policies", "scheduler"), ("ingest", "capability"),
    ("browser", "capability"), ("verify", "capability"), ("reconcile", "capability"),
    ("optimize", "capability"), ("contextops", "capability"), ("memory", "capability"),
    ("native_export", "capability"), ("monitoring", "control"),
    ("temporal_graph", "capability"), ("standards", "capability"),
]


def _now(now: int | None) -> int:
    return int(now) if now is not None else int(time.time())


def _hid(prefix: str, *parts: str) -> str:
    return prefix + hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]


class SupervisorStore:
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
        c.execute("""CREATE TABLE IF NOT EXISTS supervisor_instances(
            supervisor_id TEXT PRIMARY KEY, pid INTEGER, hostname TEXT, version TEXT, mode TEXT,
            status TEXT, started_at INTEGER, heartbeat_at INTEGER, last_tick_at INTEGER, metadata_json TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS supervisor_leases(
            lease_name TEXT PRIMARY KEY, owner_id TEXT, lease_until INTEGER, heartbeat_at INTEGER,
            generation INTEGER, created_at INTEGER, updated_at INTEGER)""")
        c.execute("""CREATE TABLE IF NOT EXISTS supervisor_shards(
            shard_id TEXT PRIMARY KEY, shard_type TEXT, shard_key TEXT, owner_id TEXT, lease_until INTEGER,
            heartbeat_at INTEGER, status TEXT, created_at INTEGER, updated_at INTEGER)""")
        c.execute("""CREATE TABLE IF NOT EXISTS supervisor_ticks(
            tick_id TEXT PRIMARY KEY, supervisor_id TEXT, mode TEXT, leader INTEGER, shard_ids_json TEXT,
            started_at INTEGER, finished_at INTEGER, status TEXT, proof_count INTEGER, green_count INTEGER,
            red_count INTEGER, queue_snapshot_hash TEXT, decision_count INTEGER, error_json TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS supervisor_decisions(
            decision_id TEXT PRIMARY KEY, supervisor_id TEXT, tick_id TEXT, shard_id TEXT, decision_type TEXT,
            idempotency_key TEXT UNIQUE, reason TEXT, input_snapshot_hash TEXT, output_command_ids_json TEXT,
            created_at INTEGER)""")
        c.execute("""CREATE TABLE IF NOT EXISTS supervisor_capacity_snapshots(
            snapshot_id TEXT PRIMARY KEY, supervisor_id TEXT, tick_id TEXT, queue_depths_json TEXT,
            worker_counts_json TEXT, oldest_task_age_json TEXT, due_jobs_json TEXT, stale_workers_json TEXT,
            provider_health_json TEXT, created_at INTEGER)""")
        c.execute("""CREATE TABLE IF NOT EXISTS supervisor_spawn_decisions(
            spawn_id TEXT PRIMARY KEY, decision_id TEXT, supervisor_id TEXT, capability_id TEXT, action TEXT,
            reason TEXT, idempotency_key TEXT UNIQUE, created_at INTEGER)""")
        c.execute("""CREATE TABLE IF NOT EXISTS supervisor_failovers(
            failover_id TEXT PRIMARY KEY, lease_name TEXT, old_owner TEXT, new_owner TEXT, generation INTEGER,
            created_at INTEGER)""")
        c.execute("""CREATE TABLE IF NOT EXISTS supervisor_spawn_requests(
            request_id TEXT PRIMARY KEY, decision_id TEXT, supervisor_id TEXT, capability_id TEXT, worker_id TEXT,
            pid INTEGER, dry_run INTEGER, command_json TEXT, status TEXT, idempotency_key TEXT UNIQUE,
            created_at INTEGER)""")

    # ── instances ──────────────────────────────────────────────────────────
    def register_instance(self, *, supervisor_id: str, pid: int = 0, hostname: str = "", version: str = "",
                          mode: str = "watch", metadata: dict | None = None, now: int | None = None) -> dict:
        t = _now(now)
        self.conn.execute(
            """INSERT INTO supervisor_instances(supervisor_id,pid,hostname,version,mode,status,started_at,
               heartbeat_at,last_tick_at,metadata_json) VALUES(?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(supervisor_id) DO UPDATE SET pid=excluded.pid,status='active',heartbeat_at=excluded.heartbeat_at""",
            (supervisor_id, pid, hostname, version, mode, "active", t, t, 0, json.dumps(metadata or {})))
        return self.instance(supervisor_id)

    def heartbeat_instance(self, supervisor_id: str, *, now: int | None = None) -> None:
        self.conn.execute("UPDATE supervisor_instances SET heartbeat_at=? WHERE supervisor_id=?", (_now(now), supervisor_id))

    def set_instance_status(self, supervisor_id: str, status: str, *, now: int | None = None) -> None:
        self.conn.execute("UPDATE supervisor_instances SET status=?,heartbeat_at=? WHERE supervisor_id=?",
                          (status, _now(now), supervisor_id))

    def instance(self, supervisor_id: str) -> dict | None:
        r = self.conn.execute("SELECT * FROM supervisor_instances WHERE supervisor_id=?", (supervisor_id,)).fetchone()
        return dict(r) if r else None

    def instances(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM supervisor_instances ORDER BY supervisor_id")]

    # ── leader lease (atomic CAS) ────────────────────────────────────────────
    def try_claim_leader(self, *, lease_name: str, supervisor_id: str, ttl_seconds: int = 30,
                         now: int | None = None) -> bool:
        """Atomic: claim iff unheld, expired, or already ours. Generation increments on a takeover."""
        t = _now(now)
        c = self.conn
        try:
            c.execute("BEGIN IMMEDIATE")
            r = c.execute("SELECT owner_id,lease_until,generation FROM supervisor_leases WHERE lease_name=?",
                          (lease_name,)).fetchone()
            if r is None:
                c.execute("""INSERT INTO supervisor_leases(lease_name,owner_id,lease_until,heartbeat_at,generation,
                             created_at,updated_at) VALUES(?,?,?,?,?,?,?)""",
                          (lease_name, supervisor_id, t + ttl_seconds, t, 1, t, t))
                c.execute("COMMIT"); return True
            owner, until, gen = r["owner_id"], r["lease_until"], r["generation"]
            if owner == supervisor_id:
                c.execute("UPDATE supervisor_leases SET lease_until=?,heartbeat_at=?,updated_at=? WHERE lease_name=?",
                          (t + ttl_seconds, t, t, lease_name)); c.execute("COMMIT"); return True
            if until < t:   # expired → takeover (new generation), record the failover
                newgen = gen + 1
                c.execute("UPDATE supervisor_leases SET owner_id=?,lease_until=?,heartbeat_at=?,generation=?,updated_at=? WHERE lease_name=?",
                          (supervisor_id, t + ttl_seconds, t, newgen, t, lease_name))
                c.execute("""INSERT OR IGNORE INTO supervisor_failovers(failover_id,lease_name,old_owner,new_owner,generation,created_at)
                             VALUES(?,?,?,?,?,?)""",
                          (_hid("fo-", lease_name, owner, supervisor_id, str(newgen)), lease_name, owner, supervisor_id, newgen, t))
                c.execute("COMMIT"); return True
            c.execute("COMMIT"); return False
        except Exception:
            try:
                c.execute("ROLLBACK")
            except Exception:
                pass
            raise

    def renew_leader(self, *, lease_name: str, supervisor_id: str, ttl_seconds: int = 30, now: int | None = None) -> bool:
        t = _now(now)
        c = self.conn
        c.execute("BEGIN IMMEDIATE")
        try:
            cur = c.execute("UPDATE supervisor_leases SET lease_until=?,heartbeat_at=?,updated_at=? WHERE lease_name=? AND owner_id=? AND lease_until>=?",
                            (t + ttl_seconds, t, t, lease_name, supervisor_id, t))
            ok = cur.rowcount > 0
            c.execute("COMMIT"); return ok
        except Exception:
            c.execute("ROLLBACK"); raise

    def release_leader(self, *, lease_name: str, supervisor_id: str) -> None:
        self.conn.execute("DELETE FROM supervisor_leases WHERE lease_name=? AND owner_id=?", (lease_name, supervisor_id))

    def get_leader(self, lease_name: str, *, now: int | None = None) -> str | None:
        t = _now(now)
        r = self.conn.execute("SELECT owner_id,lease_until FROM supervisor_leases WHERE lease_name=?", (lease_name,)).fetchone()
        return r["owner_id"] if r and r["lease_until"] >= t else None

    def failovers(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM supervisor_failovers ORDER BY created_at,failover_id")]

    # ── shard leases ─────────────────────────────────────────────────────────
    def ensure_default_shards(self, *, now: int | None = None) -> None:
        t = _now(now)
        for sid, st in DEFAULT_SHARDS:
            self.conn.execute("""INSERT OR IGNORE INTO supervisor_shards(shard_id,shard_type,shard_key,owner_id,
                                 lease_until,heartbeat_at,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)""",
                              (sid, st, sid, "", 0, 0, "unclaimed", t, t))

    def claim_shard(self, *, shard_id: str, supervisor_id: str, ttl_seconds: int = 30, now: int | None = None) -> bool:
        t = _now(now)
        c = self.conn
        c.execute("BEGIN IMMEDIATE")
        try:
            r = c.execute("SELECT owner_id,lease_until FROM supervisor_shards WHERE shard_id=?", (shard_id,)).fetchone()
            if r is None:
                c.execute("COMMIT"); return False
            owner, until = r["owner_id"], r["lease_until"]
            if (not owner) or owner == supervisor_id or until < t:
                c.execute("UPDATE supervisor_shards SET owner_id=?,lease_until=?,heartbeat_at=?,status='owned',updated_at=? WHERE shard_id=?",
                          (supervisor_id, t + ttl_seconds, t, t, shard_id))
                c.execute("COMMIT"); return True
            c.execute("COMMIT"); return False
        except Exception:
            c.execute("ROLLBACK"); raise

    def claim_available_shards(self, *, supervisor_id: str, max_shards: int, ttl_seconds: int = 30, now: int | None = None) -> list[str]:
        got = []
        for r in self.conn.execute("SELECT shard_id FROM supervisor_shards ORDER BY shard_id"):
            if len(got) >= max_shards:
                break
            if self.claim_shard(shard_id=r["shard_id"], supervisor_id=supervisor_id, ttl_seconds=ttl_seconds, now=now):
                got.append(r["shard_id"])
        return got

    def renew_shards(self, *, supervisor_id: str, shard_ids: list[str], ttl_seconds: int = 30, now: int | None = None) -> int:
        t = _now(now); n = 0
        for sid in shard_ids:
            cur = self.conn.execute("UPDATE supervisor_shards SET lease_until=?,heartbeat_at=?,updated_at=? WHERE shard_id=? AND owner_id=?",
                                    (t + ttl_seconds, t, t, sid, supervisor_id))
            n += cur.rowcount
        return n

    def expire_stale_shards(self, *, now: int | None = None) -> list[str]:
        t = _now(now)
        rows = self.conn.execute("SELECT shard_id FROM supervisor_shards WHERE owner_id!='' AND lease_until<?", (t,)).fetchall()
        ids = [r["shard_id"] for r in rows]
        for sid in ids:
            self.conn.execute("UPDATE supervisor_shards SET owner_id='',status='unclaimed',updated_at=? WHERE shard_id=?", (t, sid))
        return ids

    def list_owned_shards(self, supervisor_id: str, *, now: int | None = None) -> list[str]:
        t = _now(now)
        return [r["shard_id"] for r in self.conn.execute(
            "SELECT shard_id FROM supervisor_shards WHERE owner_id=? AND lease_until>=? ORDER BY shard_id", (supervisor_id, t))]

    def shards(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM supervisor_shards ORDER BY shard_id")]

    # ── idempotent decisions ─────────────────────────────────────────────────
    def record_decision(self, *, supervisor_id: str, decision_type: str, idempotency_key: str, tick_id: str = "",
                        shard_id: str = "", reason: str = "", input_snapshot_hash: str = "",
                        output_command_ids: list | None = None, now: int | None = None) -> dict:
        t = _now(now)
        did = _hid("sdec-", decision_type, idempotency_key)
        self.conn.execute("""INSERT OR IGNORE INTO supervisor_decisions(decision_id,supervisor_id,tick_id,shard_id,
                             decision_type,idempotency_key,reason,input_snapshot_hash,output_command_ids_json,created_at)
                             VALUES(?,?,?,?,?,?,?,?,?,?)""",
                          (did, supervisor_id, tick_id, shard_id, decision_type, idempotency_key, reason,
                           input_snapshot_hash, json.dumps(output_command_ids or []), t))
        r = self.conn.execute("SELECT * FROM supervisor_decisions WHERE idempotency_key=?", (idempotency_key,)).fetchone()
        return dict(r)

    def decision_exists(self, idempotency_key: str) -> bool:
        return self.conn.execute("SELECT 1 FROM supervisor_decisions WHERE idempotency_key=?", (idempotency_key,)).fetchone() is not None

    def record_spawn_decision(self, *, supervisor_id: str, capability_id: str, action: str, idempotency_key: str,
                              reason: str = "", tick_id: str = "", shard_id: str = "", now: int | None = None) -> dict:
        t = _now(now)
        dec = self.record_decision(supervisor_id=supervisor_id, decision_type="spawn_worker",
                                   idempotency_key=idempotency_key, tick_id=tick_id, shard_id=shard_id, reason=reason, now=now)
        self.conn.execute("""INSERT OR IGNORE INTO supervisor_spawn_decisions(spawn_id,decision_id,supervisor_id,
                             capability_id,action,reason,idempotency_key,created_at) VALUES(?,?,?,?,?,?,?,?)""",
                          (_hid("spawn-", idempotency_key), dec["decision_id"], supervisor_id, capability_id, action, reason, idempotency_key, t))
        return dec

    def decisions(self, *, decision_type: str | None = None) -> list[dict]:
        if decision_type:
            return [dict(r) for r in self.conn.execute("SELECT * FROM supervisor_decisions WHERE decision_type=? ORDER BY decision_id", (decision_type,))]
        return [dict(r) for r in self.conn.execute("SELECT * FROM supervisor_decisions ORDER BY decision_id")]

    def spawn_decisions(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM supervisor_spawn_decisions ORDER BY spawn_id")]

    def record_spawn_request(self, *, supervisor_id: str, capability_id: str, worker_id: str, decision_id: str = "",
                             pid: int = 0, dry_run: bool = True, command: list | None = None, status: str = "issued",
                             idempotency_key: str = "", now: int | None = None) -> dict:
        """Record an ISSUED worker-spawn (links to the decision). Idempotent by key so a re-tick over the same
        queued work does not issue a duplicate spawn."""
        t = _now(now)
        key = idempotency_key or f"req:{capability_id}:{worker_id}"
        self.conn.execute("""INSERT OR IGNORE INTO supervisor_spawn_requests(request_id,decision_id,supervisor_id,
            capability_id,worker_id,pid,dry_run,command_json,status,idempotency_key,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (_hid("req-", key), decision_id, supervisor_id, capability_id, worker_id, pid, 1 if dry_run else 0,
             json.dumps(command or []), status, key, t))
        r = self.conn.execute("SELECT * FROM supervisor_spawn_requests WHERE idempotency_key=?", (key,)).fetchone()
        return dict(r)

    def spawn_requests(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM supervisor_spawn_requests ORDER BY request_id")]

    # ── ticks + capacity ─────────────────────────────────────────────────────
    def record_tick(self, *, supervisor_id: str, mode: str = "watch", leader: bool = False, shard_ids: list | None = None,
                    started_at: int | None = None, duration_ms: int = 0, status: str = "ok", proof_count: int = 0,
                    green_count: int = 0, red_count: int = 0, queue_snapshot_hash: str = "", decision_count: int = 0,
                    error: dict | None = None) -> dict:
        s = _now(started_at)
        tick_id = _hid("tick-", supervisor_id, str(s), str(len(self.ticks())))
        self.conn.execute("""INSERT OR IGNORE INTO supervisor_ticks(tick_id,supervisor_id,mode,leader,shard_ids_json,
                             started_at,finished_at,status,proof_count,green_count,red_count,queue_snapshot_hash,
                             decision_count,error_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                          (tick_id, supervisor_id, mode, 1 if leader else 0, json.dumps(shard_ids or []), s,
                           s + duration_ms // 1000, status, proof_count, green_count, red_count,
                           queue_snapshot_hash, decision_count, json.dumps(error or {})))
        self.conn.execute("UPDATE supervisor_instances SET last_tick_at=? WHERE supervisor_id=?", (s, supervisor_id))
        return dict(self.conn.execute("SELECT * FROM supervisor_ticks WHERE tick_id=?", (tick_id,)).fetchone())

    def ticks(self, *, supervisor_id: str | None = None) -> list[dict]:
        if supervisor_id:
            return [dict(r) for r in self.conn.execute("SELECT * FROM supervisor_ticks WHERE supervisor_id=? ORDER BY started_at,tick_id", (supervisor_id,))]
        return [dict(r) for r in self.conn.execute("SELECT * FROM supervisor_ticks ORDER BY started_at,tick_id")]

    def record_capacity_snapshot(self, *, supervisor_id: str, tick_id: str = "", queue_depths: dict | None = None,
                                 worker_counts: dict | None = None, oldest_task_age: dict | None = None,
                                 due_jobs: dict | None = None, stale_workers: dict | None = None,
                                 provider_health: dict | None = None, now: int | None = None) -> dict:
        t = _now(now)
        sid = _hid("snap-", supervisor_id, tick_id, str(t), str(len(self.capacity_snapshots())))
        self.conn.execute("""INSERT OR IGNORE INTO supervisor_capacity_snapshots(snapshot_id,supervisor_id,tick_id,
                             queue_depths_json,worker_counts_json,oldest_task_age_json,due_jobs_json,stale_workers_json,
                             provider_health_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                          (sid, supervisor_id, tick_id, json.dumps(queue_depths or {}), json.dumps(worker_counts or {}),
                           json.dumps(oldest_task_age or {}), json.dumps(due_jobs or {}), json.dumps(stale_workers or {}),
                           json.dumps(provider_health or {}), t))
        return dict(self.conn.execute("SELECT * FROM supervisor_capacity_snapshots WHERE snapshot_id=?", (sid,)).fetchone())

    def capacity_snapshots(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM supervisor_capacity_snapshots ORDER BY created_at,snapshot_id")]

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass


__all__ = ["SupervisorStore", "DEFAULT_DB", "DEFAULT_SHARDS"]
