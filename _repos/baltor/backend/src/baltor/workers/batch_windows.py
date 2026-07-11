"""src.baltor.workers.batch_windows — BATCH WINDOW evaluation (C-FLEET-2).

Decides when a batch of queued tasks should dispatch: full at `batch_min`, partial at `max_wait`
(anti-starvation), or wait. Supports tenant/domain/provider grouping, a high-priority bypass (P0/P1
never wait for a batch), and fairness (the group whose oldest task has waited longest dispatches first).

Pure + deterministic (time injected). The batch threshold numbers live ONLY in worker_batch_policies.json
(passed in here as `batch_min`/`max_wait_seconds`) — never re-typed.
"""
from __future__ import annotations

from .fleet_ledger import _age_s

_HIGH_PRIORITIES = ("P0", "P1")

# dispatch decisions
WAIT = "wait"
DISPATCH = "dispatch"
DISPATCH_PARTIAL = "dispatch_partial"
BYPASS = "dispatch_high_priority"


def window_decision(tasks: list[dict], *, batch_min: int, max_wait_seconds: int, now: str) -> dict:
    """Decide a single batch group's fate. High-priority tasks bypass the window entirely."""
    if not tasks:
        return {"decision": WAIT, "ready": [], "reason": "empty group", "count": 0}
    ordered = sorted(tasks, key=lambda t: t.get("created_at", ""))
    high = [t for t in ordered if t.get("priority_class") in _HIGH_PRIORITIES]
    if high:
        return {"decision": BYPASS, "ready": [t["task_id"] for t in high],
                "reason": f"{len(high)} high-priority task(s) bypass the batch window", "count": len(ordered)}
    n = len(ordered)
    if n >= batch_min:
        return {"decision": DISPATCH, "ready": [t["task_id"] for t in ordered[:batch_min]],
                "reason": f"batch full ({n}>={batch_min})", "count": n}
    oldest_age = _age_s(ordered[0].get("created_at", now), now)
    if max_wait_seconds > 0 and oldest_age >= max_wait_seconds:
        return {"decision": DISPATCH_PARTIAL, "ready": [t["task_id"] for t in ordered],
                "reason": f"max_wait reached ({int(oldest_age)}s>={max_wait_seconds}s) — dispatch partial (no starvation)",
                "count": n}
    return {"decision": WAIT, "ready": [],
            "reason": f"below threshold ({n}<{batch_min}) and within max_wait ({int(oldest_age)}s<{max_wait_seconds}s)",
            "count": n}


def partition(tasks: list[dict], group_by: str | None) -> dict:
    """Partition tasks into batch groups by tenant/domain/provider (or one group when group_by is None)."""
    if not group_by:
        return {"_all": list(tasks)}
    groups: dict = {}
    for t in tasks:
        groups.setdefault(t.get(group_by, "_none"), []).append(t)
    return groups


def plan_dispatch(tasks: list[dict], *, batch_min: int, max_wait_seconds: int, now: str,
                  group_by: str | None = None) -> list[dict]:
    """Evaluate every group and return the dispatchable ones, FAIREST FIRST (the group whose oldest task
    has waited longest goes first). Groups that should still wait are omitted."""
    out = []
    for key, group in partition(tasks, group_by).items():
        d = window_decision(group, batch_min=batch_min, max_wait_seconds=max_wait_seconds, now=now)
        if d["decision"] != WAIT:
            oldest = min((g.get("created_at", now) for g in group), default=now)
            out.append({"group": key, "oldest": oldest, **d})
    out.sort(key=lambda d: d["oldest"])     # oldest-waiting group first = fairness
    return out


__all__ = ["window_decision", "partition", "plan_dispatch", "WAIT", "DISPATCH", "DISPATCH_PARTIAL", "BYPASS"]
