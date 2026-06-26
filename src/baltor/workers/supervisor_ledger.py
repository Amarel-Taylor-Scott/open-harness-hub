"""src.baltor.workers.supervisor_ledger — coordination ledger for SCALING the lightweight flywheel
supervisor (C-FLEET-3).

The supervisor scales as a REPLICATED CONTROL PLANE, never by doing worker work: one active leader for
singleton duties + many shard owners for high-volume scans, coordinated by DB leases and idempotent
decisions. This models the five coordination tables in-memory (maps to SQLite/Postgres later, same CAS
semantics):

  supervisor_instances · supervisor_leases · supervisor_shards · supervisor_ticks · supervisor_decisions

Leases use a compare-and-set: acquirable iff unheld, expired, or already mine — modeling
`UPDATE … WHERE lease_until < :now OR owner_id = :me` (Postgres) / a conditional write. Decisions are
idempotent by key so two racing supervisors never enqueue duplicate work. Deterministic (injected `now`).
The supervisor here only RECORDS coordination + decisions; workers still execute via the task ledger's
atomic claim — this never executes heavy work.
"""
from __future__ import annotations

import hashlib

from .fleet_ledger import _epoch, _plus_s


class SupervisorLedgerError(Exception):
    pass


def _hid(prefix: str, *parts: str) -> str:
    return prefix + hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]


class SupervisorLedger:
    def __init__(self) -> None:
        self._instances: dict = {}
        self._leases: dict = {}       # lease_name -> {owner_id, lease_until, heartbeat_at}
        self._shards: dict = {}       # shard_id -> {shard_type, shard_key, owner_id, lease_until, heartbeat_at, status}
        self._ticks: list = []        # {supervisor_id, shard_id, started_at, duration_ms, ...}
        self._decisions: dict = {}    # idempotency_key -> decision record

    # ── instances ─────────────────────────────────────────────────────────
    def register_instance(self, *, supervisor_id: str, hostname: str = "", pid: int = 0,
                          version: str = "", now: str) -> dict:
        inst = {"schema_version": "SupervisorInstance", "supervisor_id": supervisor_id, "hostname": hostname,
                "pid": pid, "version": version, "status": "running", "started_at": now,
                "heartbeat_at": now, "last_tick_at": ""}
        self._instances[supervisor_id] = inst
        return inst

    def heartbeat_instance(self, supervisor_id: str, now: str) -> None:
        self._instances[supervisor_id]["heartbeat_at"] = now

    # ── leader lease (singleton duties) ─────────────────────────────────────
    def acquire_lease(self, *, lease_name: str, owner_id: str, now: str, ttl_seconds: int = 30) -> bool:
        """CAS acquire: succeed iff the lease is unheld, expired, or already ours. Models
        `UPDATE supervisor_leases SET owner=:me, lease_until=:exp WHERE lease_until < :now OR owner=:me`."""
        cur = self._leases.get(lease_name)
        if cur is None or _epoch(cur["lease_until"]) < _epoch(now) or cur["owner_id"] == owner_id:
            self._leases[lease_name] = {"lease_name": lease_name, "owner_id": owner_id,
                                        "lease_until": _plus_s(now, ttl_seconds), "heartbeat_at": now}
            return True
        return False

    def renew_lease(self, *, lease_name: str, owner_id: str, now: str, ttl_seconds: int = 30) -> bool:
        cur = self._leases.get(lease_name)
        if cur and cur["owner_id"] == owner_id and _epoch(cur["lease_until"]) >= _epoch(now):
            cur["lease_until"] = _plus_s(now, ttl_seconds); cur["heartbeat_at"] = now
            return True
        return False

    def lease_holder(self, lease_name: str, *, now: str) -> str | None:
        cur = self._leases.get(lease_name)
        if cur and _epoch(cur["lease_until"]) >= _epoch(now):
            return cur["owner_id"]
        return None

    def is_leader(self, *, lease_name: str, owner_id: str, now: str) -> bool:
        return self.lease_holder(lease_name, now=now) == owner_id

    # ── shard leases (high-volume scans) ────────────────────────────────────
    def register_shard(self, *, shard_id: str, shard_type: str, shard_key: str) -> dict:
        s = {"schema_version": "SupervisorShard", "shard_id": shard_id, "shard_type": shard_type,
             "shard_key": shard_key, "owner_id": "", "lease_until": "", "heartbeat_at": "", "status": "unclaimed"}
        self._shards[shard_id] = s
        return s

    def claim_shard(self, *, shard_id: str, owner_id: str, now: str, ttl_seconds: int = 30) -> bool:
        """CAS claim a shard: succeed iff unclaimed, expired, or already ours."""
        s = self._shards.get(shard_id)
        if s is None:
            raise SupervisorLedgerError(f"unknown shard {shard_id!r}")
        if not s["owner_id"] or (s["lease_until"] and _epoch(s["lease_until"]) < _epoch(now)) or s["owner_id"] == owner_id:
            s["owner_id"] = owner_id; s["lease_until"] = _plus_s(now, ttl_seconds)
            s["heartbeat_at"] = now; s["status"] = "owned"
            return True
        return False

    def heartbeat_shard(self, *, shard_id: str, owner_id: str, now: str, ttl_seconds: int = 30) -> bool:
        s = self._shards.get(shard_id)
        if s and s["owner_id"] == owner_id and _epoch(s["lease_until"]) >= _epoch(now):
            s["lease_until"] = _plus_s(now, ttl_seconds); s["heartbeat_at"] = now
            return True
        return False

    def shards_owned_by(self, owner_id: str, *, now: str) -> list[dict]:
        return [s for s in self._shards.values()
                if s["owner_id"] == owner_id and s["lease_until"] and _epoch(s["lease_until"]) >= _epoch(now)]

    def reclaim_stale_shards(self, *, now: str) -> list[str]:
        out = []
        for s in self._shards.values():
            if s["owner_id"] and s["lease_until"] and _epoch(s["lease_until"]) < _epoch(now):
                s["owner_id"] = ""; s["status"] = "unclaimed"; out.append(s["shard_id"])
        return out

    # ── idempotent decisions (no duplicate spawn) ───────────────────────────
    def record_decision(self, *, supervisor_id: str, decision_type: str, idempotency_key: str,
                        shard_id: str = "", reason: str = "", output_command_ids: list | None = None,
                        now: str) -> dict:
        """Idempotent: the SAME idempotency_key returns the SAME decision (no duplicate work). Models a
        unique constraint on (idempotency_key)."""
        if idempotency_key in self._decisions:
            return self._decisions[idempotency_key]
        d = {"schema_version": "SupervisorDecision",
             "decision_id": _hid("sdec-", supervisor_id, decision_type, idempotency_key),
             "supervisor_id": supervisor_id, "shard_id": shard_id, "decision_type": decision_type,
             "reason": reason, "idempotency_key": idempotency_key,
             "output_command_ids": list(output_command_ids or []), "created_at": now}
        self._decisions[idempotency_key] = d
        return d

    def decisions(self) -> list[dict]:
        return list(self._decisions.values())

    # ── ticks (lag accounting) ──────────────────────────────────────────────
    def record_tick(self, *, supervisor_id: str, shard_id: str = "", started_at: str, duration_ms: int,
                    due_task_count: int = 0, scheduled_count: int = 0, interval_ms: int = 0) -> dict:
        t = {"schema_version": "SupervisorTick", "supervisor_id": supervisor_id, "shard_id": shard_id,
             "started_at": started_at, "duration_ms": duration_ms, "due_task_count": due_task_count,
             "scheduled_count": scheduled_count, "interval_ms": interval_ms}
        self._ticks.append(t)
        if supervisor_id in self._instances:
            self._instances[supervisor_id]["last_tick_at"] = started_at
        return t

    def ticks(self) -> list[dict]:
        return list(self._ticks)


__all__ = ["SupervisorLedger", "SupervisorLedgerError"]
