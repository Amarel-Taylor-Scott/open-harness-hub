#!/usr/bin/env python3
"""contracts/artifacts/canonical_fact — the reconciled, governed fact the system may certify and serve.

A ``CanonicalFact`` is the single reconciled answer for one (subject, predicate, scope) after assertions are
weighed (authority, freshness, conflict). Its ``status`` records exactly how trustworthy it is right now —
candidate → verified_current → stale → contested → superseded, with held_out / tenant_override / needs_human /
deprecated for the governance edges. Only ``verified_current`` (and a fresh ``tenant_override`` within its
tenant) is servable as truth; everything else rides as a warning. Deterministic + offline: ``fact_id`` is
content-addressed; all times are injected ints.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from src.baltor.contracts.artifacts.fact_assertion import SCOPES

#: lifecycle of a canonical fact — the watchtower drives a fact through these as freshness/conflict change.
STATUSES = ("candidate", "verified_current", "stale", "contested", "superseded",
            "held_out", "tenant_override", "needs_human", "deprecated")

#: the only statuses that may be served as certified truth (everything else is a held-out warning).
SERVABLE_STATUSES = ("verified_current", "tenant_override")


def _content_id(prefix: str, body: dict) -> str:
    return prefix + "-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


@dataclass(frozen=True)
class CanonicalFact:
    subject: str
    predicate: str
    object: str
    scope: str                      # one of SCOPES
    status: str                     # one of STATUSES
    source_handle: str
    content_hash: str
    authority_rank: int = 0
    fragility_id: str = ""          # the FragilityMetadata governing this fact's freshness
    supporting_assertion_ids: tuple = ()
    tenant_id: str = ""
    unit: str = ""

    def __post_init__(self) -> None:
        if self.scope not in SCOPES:
            raise ValueError(f"scope {self.scope!r} not in {SCOPES}")
        if self.status not in STATUSES:
            raise ValueError(f"status {self.status!r} not in {STATUSES}")

    @property
    def fact_id(self) -> str:
        # identity is the reconciled CLAIM, not its current status (status changes; identity must not).
        return _content_id("cf", {"sub": self.subject, "pred": self.predicate, "obj": self.object,
                                  "sc": self.scope, "ten": self.tenant_id})

    @property
    def servable(self) -> bool:
        return self.status in SERVABLE_STATUSES

    def to_dict(self) -> dict:
        return {"schema_version": "CanonicalFact", "fact_id": self.fact_id, "subject": self.subject,
                "predicate": self.predicate, "object": self.object, "scope": self.scope, "status": self.status,
                "source_handle": self.source_handle, "content_hash": self.content_hash,
                "authority_rank": self.authority_rank, "fragility_id": self.fragility_id,
                "supporting_assertion_ids": list(self.supporting_assertion_ids),
                "tenant_id": self.tenant_id, "unit": self.unit}
