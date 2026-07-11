#!/usr/bin/env python3
"""scripts.pipeline_runtime.artifact_types — the governed artifact-type registry (single source of truth).

Every artifact Baltor produces — from a raw ``source_field`` to a model-interpreted ``emotion_signal`` —
declares its governance up front: is it source-grounded or derived, model-dependent, promotion-eligible
by default, does it need human review, may it be embedded / served / used as a certified fact, and what
retention class it falls under. The four "claim-shaped" types — ``atomic_fact``, ``narrative_allegation``,
``conclusion``, ``emotion_signal`` — are DISTINCT types with DISTINCT governance defaults, so the system
cannot silently treat an allegation or a model interpretation as a certified fact.

This is metadata + contract only (no I/O). The defaults here are the floor; a run may be MORE restrictive
(e.g. hold out a fact pending review) but never looser than the type's governance.

CLI: imported by the registry proof (_repos/shared-backend-components/scripts/check_artifact_type_registry.py).
"""
from __future__ import annotations

from dataclasses import dataclass

#: retention classes — map later to storage TTL/legal tiers without changing the contract.
RETENTION_CLASSES = ("ephemeral", "standard", "audit")


@dataclass(frozen=True)
class ArtifactTypeSpec:
    artifact_type: str
    schema_version: str
    source_grounded: bool
    derived: bool
    model_dependent: bool
    promotion_eligible_default: bool
    requires_human_review: bool
    can_be_embedded: bool
    can_be_served: bool
    can_be_used_as_fact: bool
    retention_class: str

    @property
    def requires_processor_metadata(self) -> bool:
        """A model-dependent artifact is meaningless without the processor_id@version + config that
        produced it — so the registry REQUIRES processor metadata on every model-dependent artifact."""
        return self.model_dependent

    def governance_key(self) -> tuple:
        """The governance fingerprint — used to assert distinct types have distinct governance."""
        return (self.source_grounded, self.derived, self.model_dependent,
                self.promotion_eligible_default, self.requires_human_review,
                self.can_be_embedded, self.can_be_served, self.can_be_used_as_fact,
                self.retention_class)


def _spec(at: str, *, sg: bool, der: bool, md: bool, promo: bool, hr: bool,
          emb: bool, srv: bool, fact: bool, ret: str = "standard",
          schema_version: str = "v1") -> ArtifactTypeSpec:
    assert ret in RETENTION_CLASSES, ret
    return ArtifactTypeSpec(at, schema_version, sg, der, md, promo, hr, emb, srv, fact, ret)


#: THE REGISTRY. Source containers → not facts; structured leaf (source_field) → usable as fact;
#: the four claim-shaped types are deliberately distinct (see governance_key distinctness in the proof).
REGISTRY: dict[str, ArtifactTypeSpec] = {s.artifact_type: s for s in [
    # ── source-grounded raw artifacts (verbatim from the source; not derived, not model-dependent) ──
    _spec("source_record",   sg=True,  der=False, md=False, promo=False, hr=False, emb=False, srv=True,  fact=False, ret="audit"),
    _spec("source_document", sg=True,  der=False, md=False, promo=False, hr=False, emb=False, srv=True,  fact=False, ret="audit"),
    _spec("source_page",     sg=True,  der=False, md=False, promo=False, hr=False, emb=False, srv=True,  fact=False, ret="audit"),
    _spec("source_block",    sg=True,  der=False, md=False, promo=False, hr=False, emb=True,  srv=True,  fact=False),
    _spec("source_line",     sg=True,  der=False, md=False, promo=False, hr=False, emb=True,  srv=True,  fact=False),
    _spec("source_field",    sg=True,  der=False, md=False, promo=True,  hr=False, emb=True,  srv=True,  fact=True),
    # ── decomposed grains ──
    _spec("paragraph",       sg=True,  der=False, md=False, promo=False, hr=False, emb=True,  srv=True,  fact=False),
    _spec("sentence",        sg=True,  der=False, md=False, promo=False, hr=False, emb=True,  srv=True,  fact=False),
    # ── the four CLAIM-SHAPED types: distinct governance, cannot be conflated ──
    _spec("atomic_fact",        sg=True,  der=False, md=False, promo=True,  hr=False, emb=True,  srv=True,  fact=True),
    _spec("narrative_allegation", sg=True, der=False, md=False, promo=False, hr=True, emb=True, srv=True, fact=False),
    _spec("conclusion",         sg=False, der=True,  md=False, promo=False, hr=True,  emb=False, srv=True,  fact=False),
    _spec("emotion_signal",     sg=False, der=True,  md=True,  promo=False, hr=False, emb=False, srv=True,  fact=False, ret="ephemeral"),
    # ── extraction / interpretation ──
    _spec("entity_mention",  sg=True,  der=True,  md=False, promo=False, hr=False, emb=False, srv=True,  fact=False),
    _spec("relation",        sg=True,  der=True,  md=False, promo=False, hr=True,  emb=False, srv=True,  fact=False),
    _spec("sentiment_vector",sg=False, der=True,  md=True,  promo=False, hr=False, emb=True,  srv=True,  fact=False, ret="ephemeral"),
    _spec("embedding",       sg=False, der=True,  md=True,  promo=False, hr=False, emb=False, srv=True,  fact=False, ret="ephemeral"),
    # ── assembled / served ──
    _spec("context_pack",    sg=False, der=True,  md=False, promo=False, hr=False, emb=False, srv=True,  fact=False),
    _spec("receipt",         sg=False, der=True,  md=False, promo=False, hr=False, emb=False, srv=True,  fact=False, ret="audit"),
]}

#: the four claim-shaped types whose governance MUST stay distinct (no silent conflation).
CLAIM_SHAPED = ("atomic_fact", "narrative_allegation", "conclusion", "emotion_signal")

REQUIRED_TYPES = (
    "source_record", "source_document", "source_page", "source_block", "source_line", "source_field",
    "paragraph", "sentence", "atomic_fact", "narrative_allegation", "entity_mention", "relation",
    "conclusion", "emotion_signal", "sentiment_vector", "embedding", "context_pack", "receipt",
)


def get(artifact_type: str) -> ArtifactTypeSpec:
    if artifact_type not in REGISTRY:
        raise KeyError(f"unknown artifact_type: {artifact_type!r}")
    return REGISTRY[artifact_type]


def is_model_dependent(artifact_type: str) -> bool:
    return get(artifact_type).model_dependent


def requires_processor_metadata(artifact_type: str) -> bool:
    return get(artifact_type).requires_processor_metadata
