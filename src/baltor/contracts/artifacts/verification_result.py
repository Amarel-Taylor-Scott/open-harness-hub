#!/usr/bin/env python3
"""contracts/artifacts/verification_result — the OUTCOME of running a VerificationTask.

A ``VerificationResult`` records what a refresh found: the new status the fact should take
(verified_current / stale / contested / superseded / needs_human), the EVIDENCE artifact dict the refresh
stored (an evidence record — NOT a fabricated answer), and the re-verification timestamp + the next horizon.
A tenant_private refresh may NOT update a global_public canonical fact (the planner enforces scope; the result
records the refused/applied verdict). Deterministic + offline: ``result_id`` is content-addressed; all times
are injected ints.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from src.baltor.contracts.artifacts.canonical_fact import STATUSES as FACT_STATUSES
from src.baltor.contracts.artifacts.fact_assertion import SCOPES


def _content_id(prefix: str, body: dict) -> str:
    return prefix + "-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


@dataclass(frozen=True)
class VerificationResult:
    task_id: str
    fact_id: str
    scope: str                      # one of SCOPES (the scope the refresh ran in)
    new_status: str                 # one of CanonicalFact STATUSES
    applied: bool                   # did this result update the canonical fact? (False == refused, e.g. scope leak)
    verified_at: int                # injected epoch seconds — the moment of re-verification
    evidence: dict = field(default_factory=dict)  # the stored EVIDENCE artifact dict (NOT an answer)
    next_verify_at: int | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        if self.scope not in SCOPES:
            raise ValueError(f"scope {self.scope!r} not in {SCOPES}")
        if self.new_status not in FACT_STATUSES:
            raise ValueError(f"new_status {self.new_status!r} not in {FACT_STATUSES}")

    @property
    def result_id(self) -> str:
        return _content_id("vres", {"task": self.task_id, "f": self.fact_id, "sc": self.scope,
                                    "ns": self.new_status, "ap": self.applied, "va": self.verified_at,
                                    "ev": json.dumps(self.evidence, sort_keys=True)})

    def to_dict(self) -> dict:
        return {"schema_version": "VerificationResult.v1", "result_id": self.result_id, "task_id": self.task_id,
                "fact_id": self.fact_id, "scope": self.scope, "new_status": self.new_status,
                "applied": self.applied, "verified_at": self.verified_at, "evidence": dict(self.evidence),
                "next_verify_at": self.next_verify_at, "reason": self.reason}
