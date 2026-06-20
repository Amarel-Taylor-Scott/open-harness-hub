#!/usr/bin/env python3
"""contracts/artifacts/verification_task — a DURABLE unit of work: 're-verify this stale fact'.

When a fact passes its refresh horizon, the FactRefreshPlanner emits a ``VerificationTask``. It is a queued
intent — it carries WHAT to re-verify (fact_id + source_handle + scope), under WHICH watch policy, and the
``due_at`` horizon it missed. The C40 gate treats a stale fact with a pending task as 'allow' (queued), so the
task id must be stable/durable across reruns. Deterministic + offline: ``task_id`` is content-addressed;
``created_at`` / ``due_at`` are injected ints.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from src.baltor.contracts.artifacts.fact_assertion import SCOPES

#: task lifecycle (the planner emits 'queued'; a refresh resolves it). Single source for the watchtower.
TASK_STATUSES = ("queued", "in_progress", "resolved", "escalated", "failed")


def _content_id(prefix: str, body: dict) -> str:
    return prefix + "-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


@dataclass(frozen=True)
class VerificationTask:
    fact_id: str
    source_handle: str
    scope: str                      # one of SCOPES — a refresh may NOT cross from tenant_private to global_public
    watch_policy_id: str
    due_at: int                     # the missed refresh horizon (injected epoch seconds)
    created_at: int                 # when the planner emitted the task (injected epoch seconds)
    status: str = "queued"          # one of TASK_STATUSES
    reason: str = "fact past refresh horizon"

    def __post_init__(self) -> None:
        if self.scope not in SCOPES:
            raise ValueError(f"scope {self.scope!r} not in {SCOPES}")
        if self.status not in TASK_STATUSES:
            raise ValueError(f"status {self.status!r} not in {TASK_STATUSES}")

    @property
    def task_id(self) -> str:
        # durable: identity is the (fact, horizon it missed, policy) — NOT created_at — so reruns coalesce.
        return _content_id("vtask", {"f": self.fact_id, "sh": self.source_handle, "sc": self.scope,
                                     "wp": self.watch_policy_id, "due": self.due_at})

    def to_dict(self) -> dict:
        return {"schema_version": "VerificationTask.v1", "task_id": self.task_id, "fact_id": self.fact_id,
                "source_handle": self.source_handle, "scope": self.scope,
                "watch_policy_id": self.watch_policy_id, "due_at": self.due_at, "created_at": self.created_at,
                "status": self.status, "reason": self.reason}
