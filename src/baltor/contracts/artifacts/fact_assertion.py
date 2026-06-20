#!/usr/bin/env python3
"""contracts/artifacts/fact_assertion — a single asserted claim from one source, BEFORE canonicalization.

A ``FactAssertion`` is what a source SAYS (e.g. "Reg E gives 10 business days"); it is not yet a certified
canonical fact. ``claim_type`` reuses the four CLAIM_SHAPED types from the governed artifact-type registry
(``scripts.pipeline_runtime.artifact_types``) so an allegation/conclusion/emotion is never silently treated
as an atomic fact. ``scope`` decides who may see/own it (global_public / tenant_private / tenant_override /
system_reference). Deterministic + offline: ``assertion_id`` is content-addressed (hashlib); ``asserted_at``
is an injected int (never wall-clock).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from scripts.pipeline_runtime.artifact_types import CLAIM_SHAPED

#: where an assertion (and the canonical fact it feeds) may live / be served. Single source for the watchtower.
SCOPES = ("global_public", "tenant_private", "tenant_override", "system_reference")


def _content_id(prefix: str, body: dict) -> str:
    """A content-addressed id: prefix + sha256 of the canonical-JSON body. No clock, no RNG."""
    return prefix + "-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


@dataclass(frozen=True)
class FactAssertion:
    claim_text: str
    claim_type: str                 # one of CLAIM_SHAPED (atomic_fact/narrative_allegation/conclusion/emotion_signal)
    source_handle: str
    scope: str                      # one of SCOPES
    asserted_at: int                # injected epoch seconds — never wall-clock
    subject: str = ""
    predicate: str = ""
    object: str = ""
    source_authority: str = ""      # e.g. source-of-law / agency-faq / vendor-doc / demo-fixture
    authority_rank: int = 0
    tenant_id: str = ""

    def __post_init__(self) -> None:
        if self.claim_type not in CLAIM_SHAPED:
            raise ValueError(f"claim_type {self.claim_type!r} not in CLAIM_SHAPED {CLAIM_SHAPED}")
        if self.scope not in SCOPES:
            raise ValueError(f"scope {self.scope!r} not in {SCOPES}")

    @property
    def assertion_id(self) -> str:
        return _content_id("fa", {"t": self.claim_text, "ct": self.claim_type, "sh": self.source_handle,
                                  "sc": self.scope, "sub": self.subject, "pred": self.predicate,
                                  "obj": self.object, "ten": self.tenant_id})

    def to_dict(self) -> dict:
        return {"schema_version": "FactAssertion.v1", "assertion_id": self.assertion_id,
                "claim_text": self.claim_text, "claim_type": self.claim_type,
                "source_handle": self.source_handle, "scope": self.scope, "asserted_at": self.asserted_at,
                "subject": self.subject, "predicate": self.predicate, "object": self.object,
                "source_authority": self.source_authority, "authority_rank": self.authority_rank,
                "tenant_id": self.tenant_id}
