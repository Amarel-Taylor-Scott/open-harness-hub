"""src.baltor.graph.temporal.contracts — constants, deterministic ids, and dataclasses for the governed
Temporal Fact Graph. Pure/deterministic (hashlib ids, injected time; no wall-clock, no RNG)."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Any

EPOCH = "1970-01-01T00:00:00Z"

# governed states (Baltor decides which is safe to serve)
CANDIDATE = "candidate"
VERIFIED_CURRENT = "verified_current"
STALE = "stale"
CONTESTED = "contested"
SUPERSEDED = "superseded"
HELD_OUT = "held_out"
TENANT_OVERRIDE = "tenant_override"
NEEDS_HUMAN = "needs_human"
DEPRECATED = "deprecated"
STATES = {CANDIDATE, VERIFIED_CURRENT, STALE, CONTESTED, SUPERSEDED, HELD_OUT, TENANT_OVERRIDE, NEEDS_HUMAN, DEPRECATED}
#: states excluded from a default "current" projection (never served unless explicitly requested).
NOT_SERVABLE = {CANDIDATE, STALE, CONTESTED, SUPERSEDED, HELD_OUT, NEEDS_HUMAN, DEPRECATED}

SCOPES = {"global_public", "tenant_private", "tenant_override", "system_reference"}

EDGE_TYPES = {
    "OBSERVED_AS", "SUPPORTS", "CONTRADICTS", "SUPERSEDES", "SUPERSEDED_BY", "INVALIDATES", "HELD_OUT_BY",
    "RECONCILED_BY", "VERIFIED_BY", "DERIVED_FROM", "SAME_FACT_KEY", "SAME_SUBJECT", "SAME_PREDICATE",
    "SAME_OBJECT", "SAME_SOURCE_HANDLE", "TENANT_OVERRIDE_OF", "VERSION_OF", "CURRENT_VERSION_OF",
    "IMPACTS_CONTEXT_PACK", "IMPACTS_CONTEXT_RESPONSE"}

EDGE_SOURCES = {"deterministic", "llm_candidate", "human", "imported", "provider"}

#: source authority ranking (higher wins). Shared with reconciliation/reliability — source-of-law beats FAQ.
AUTHORITY_RANK = {
    "source_of_law": 100, "official_regulation": 90, "statute": 95, "official_agency": 80,
    "primary_dataset": 75, "official_api": 70, "official_faq": 40, "agency_faq": 40,
    "public_summary": 30, "vendor_doc": 25, "secondary_summary": 20, "blog": 10, "unknown": 0,
}


def _canon(body: Any) -> bytes:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode()


def content_hash(body: Any) -> str:
    return "sha256:" + hashlib.sha256(_canon(body)).hexdigest()


def temporal_fact_id(*, canonical_fact_key: str, tenant_id: str, value_normalized: str,
                     source_authority: str, content_hash_: str) -> str:
    """Deterministic, content-addressed node id (same logical observation → same id, clock-independent)."""
    h = hashlib.sha256(_canon([canonical_fact_key, tenant_id, value_normalized, source_authority, content_hash_])).hexdigest()[:20]
    return f"tfn-{h}"


def edge_id(*, tenant_id: str, from_id: str, edge_type: str, to_id: str, observed_at_or_policy: str) -> str:
    """Deterministic edge id: tenant + from + edge_type + to + observed_at_or_policy_hash."""
    h = hashlib.sha256(_canon([tenant_id, from_id, edge_type, to_id, observed_at_or_policy])).hexdigest()[:20]
    return f"tfe-{h}"


def observation_id(*, temporal_fact_id_: str, observed_at: str, content_hash_: str) -> str:
    h = hashlib.sha256(_canon([temporal_fact_id_, observed_at, content_hash_])).hexdigest()[:20]
    return f"tfo-{h}"


@dataclass
class TemporalFactNode:
    canonical_fact_key: str
    tenant_id: str
    scope: str
    subject: str
    predicate: str
    object: str
    value_normalized: str
    source_authority: str
    content_hash: str
    claim_status: str = CANDIDATE
    current_state: str = CANDIDATE
    unit: str = ""
    source_artifact_ids: list = field(default_factory=list)
    source_handles: list = field(default_factory=list)
    first_observed_at: str = EPOCH
    last_observed_at: str = EPOCH
    valid_from: str = ""
    valid_to: str = ""
    invalidated_at: str = ""
    verification_receipt_ids: list = field(default_factory=list)
    reconciliation_receipt_ids: list = field(default_factory=list)
    freshness: dict = field(default_factory=dict)
    lineage: dict = field(default_factory=dict)
    created_at: str = EPOCH
    updated_at: str = EPOCH
    temporal_fact_id: str = ""

    def __post_init__(self):
        if not self.temporal_fact_id:
            self.temporal_fact_id = temporal_fact_id(
                canonical_fact_key=self.canonical_fact_key, tenant_id=self.tenant_id,
                value_normalized=self.value_normalized, source_authority=self.source_authority,
                content_hash_=self.content_hash)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["schema_version"] = "TemporalFactNode.v1"
        return d

    def authority_rank(self) -> int:
        return AUTHORITY_RANK.get(self.source_authority, 0)
