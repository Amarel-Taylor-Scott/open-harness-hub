"""src.baltor.workers.supervisor_projection — READ-ONLY projection of live supervisor state
(OPP-supervisor-scaling-live, API/UI). Powers /api/fleet/* and the /fleet page. It only READS the durable
SupervisorStore (the source of truth) and never mutates it — the dashboard cannot change supervisor truth.
"""
from __future__ import annotations

import time

from .supervisor_store import DEFAULT_DB, SupervisorStore

_SECTIONS = ("supervisors", "leader", "shards", "ticks", "decisions", "capacity", "failovers", "tasks",
             "spawn_requests", "execution")


def _now(now: int | None) -> int:
    return int(now) if now is not None else int(time.time())


def _execution(s, *, limit: int = 50) -> dict:
    """READ-ONLY projection of the live EXECUTION-BACKEND decisions (which backend each capability's work ran
    on). Makes the policy/pricebook-driven, switchable backend choice VISIBLE. The chosen backend + capability
    are parsed from the decision's idempotency_key (`exec:{capability}:{backend}:{task_id}`) — no extra column,
    no fragile prose parsing. Local-first today; the same surface shows a k8s/cloud-function mix tomorrow."""
    decs = s.decisions(decision_type="execution_backend")
    by_backend: dict = {}
    by_capability: dict = {}
    recent = []
    for d in decs:
        parts = (d.get("idempotency_key", "") or "").split(":", 3)
        cap = parts[1] if len(parts) >= 4 and parts[0] == "exec" else "?"
        backend = parts[2] if len(parts) >= 4 and parts[0] == "exec" else "?"
        by_backend[backend] = by_backend.get(backend, 0) + 1
        by_capability[cap] = by_capability.get(cap, 0) + 1
    for d in decs[-limit:]:
        parts = (d.get("idempotency_key", "") or "").split(":", 3)
        recent.append({"capability": parts[1] if len(parts) >= 4 else "?",
                       "backend": parts[2] if len(parts) >= 4 else "?",
                       "reason": d.get("reason", ""), "decision_id": d.get("decision_id", ""),
                       "created_at": d.get("created_at", 0)})
    return {"total": len(decs), "by_backend": by_backend, "by_capability": by_capability, "recent": recent,
            "note": "backend choice is policy/pricebook-driven + reversible; local-first, cloud-deferred-never-blocking"}


def _durable_tasks(db_path) -> dict:
    """Read-only summary of the durable CapabilityTask queue (live dispatch state)."""
    try:
        from .durable_fleet_ledger import DurableFleetLedger
        L = DurableFleetLedger(db_path)
        try:
            by_status = {st: len(L.tasks_by_status(st)) for st in
                         ("queued", "claimed", "running", "succeeded", "failed", "dead")}
            recent = (L.queued_tasks())[:25]
            return {"by_status": by_status, "queued": recent,
                    "by_capability": _count(L.queued_tasks(), "capability_id")}
        finally:
            L.close()
    except Exception as e:  # projection must never fail the page
        return {"by_status": {}, "queued": [], "error": f"{type(e).__name__}: {e}"}


def _count(rows, key) -> dict:
    out: dict = {}
    for r in rows:
        out[r.get(key, "?")] = out.get(r.get(key, "?"), 0) + 1
    return out


def fleet_projection(db_path=None, *, now: int | None = None, limit: int = 50) -> dict:
    """Full read-only snapshot of the control-plane coordination state + the durable task queue."""
    db_path = db_path or DEFAULT_DB
    s = SupervisorStore(db_path)
    try:
        t = _now(now)
        return {
            "ok": True,
            "now": t,
            "leader": s.get_leader("global", now=t),
            "supervisors": s.instances(),
            "shards": s.shards(),
            "ticks": s.ticks()[-limit:],
            "decisions": s.decisions()[-limit:],
            "spawn_decisions": s.spawn_decisions()[-limit:],
            "spawn_requests": s.spawn_requests()[-limit:],
            "capacity": s.capacity_snapshots()[-limit:],
            "failovers": s.failovers(),
            "tasks": _durable_tasks(db_path),
            "execution": _execution(s, limit=limit),
            "contract": {"source_of_truth": "durable SupervisorStore + DurableFleetLedger", "projection": "read-only"},
        }
    finally:
        s.close()


def fleet_section(section: str, db_path=None, *, now: int | None = None) -> dict:
    """One named section (for /api/fleet/<section>)."""
    full = fleet_projection(db_path, now=now)
    if section not in _SECTIONS:
        return {"ok": False, "error": f"unknown fleet section {section!r}", "sections": list(_SECTIONS)}
    return {"ok": True, "section": section, section: full[section], "now": full["now"]}


def supervisor_detail(supervisor_id: str, db_path=None, *, limit: int = 50) -> dict:
    s = SupervisorStore(db_path or DEFAULT_DB)
    try:
        return {
            "ok": True,
            "supervisor": s.instance(supervisor_id),
            "owned_shards": s.list_owned_shards(supervisor_id),
            "ticks": s.ticks(supervisor_id=supervisor_id)[-limit:],
        }
    finally:
        s.close()


__all__ = ["fleet_projection", "fleet_section", "supervisor_detail"]
