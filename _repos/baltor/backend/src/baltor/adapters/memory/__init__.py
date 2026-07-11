"""adapters/memory — governed memory/context providers behind the MemoryProviderPort.

Every provider here (the working Baltor-local store, the deterministic Supermemory emulator, and the
Supermemory api/mcp CANDIDATE contract stubs) turns a write/search/profile call into governed
``MemoryArtifact`` records that are ALWAYS ``claim_status="candidate"`` with a populated
``external_source_handle`` (the upstream id) + ``lineage`` — never a served/canonical fact.

GOVERNANCE: remembered != verified · retrieved != served · profiled != canonical · candidate != promoted.
A memory result can only become a CanonicalFact downstream through the existing VerificationGate +
Reconciliation + ConsumptionGate. Supermemory is NEVER the source of truth. No provider here imports a
third-party SDK or makes a network call; the emulator is the working offline contract impl and the reference
path runs with NO credentials. LOSSLESS DISTILLATION: providers never overwrite/delete raw — lineage and
source handles are preserved on every artifact.

The shared helpers below build a governed MemoryArtifact identically for every provider so the artifact
shape + content-addressing live in ONE place (no magic values, no parallel shapes).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from src.baltor.ports.memory_provider import (
    CANDIDATE_CLAIM_STATUS,
    MEMORY_ARTIFACT_TYPE,
)


def memory_content_hash(obj: Any) -> str:
    """Content-address an object: deterministic 16-hex sha256 of its canonical JSON. No RNG, no wall-clock."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def external_source_handle(*, provider_id: str, tenant_id: str, project: str, upstream_id: str) -> str:
    """The upstream/provider id, wrapped as a stable Baltor source handle. This is the LINEAGE back-pointer to
    where the memory came from — never dropped. Form: ``mem://<provider>/tenant/<tid>/project/<proj>#<id>``.
    """
    return f"mem://{provider_id}/tenant/{tenant_id}/project/{project}#{upstream_id}"


def make_memory_artifact(
    *,
    provider_id: str,
    tenant_id: str,
    project: str,
    content: Any,
    now: int,
    upstream_id: str | None = None,
    container_tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    lineage_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ONE governed MemoryArtifact. Output is ALWAYS ``claim_status="candidate"`` (never served /
    canonical / verified) and ALWAYS carries tenant_id + project scope + external_source_handle + lineage +
    content_hash. Content-addressed: same (provider, tenant, project, content) → same id (deterministic).

    ``now`` is injected (no wall-clock). ``upstream_id`` defaults to the content hash when a backend did not
    supply one (the emulator/local store self-assign). LOSSLESS: the raw ``content`` is preserved verbatim and
    lineage records provenance + version; nothing is overwritten or deleted.
    """
    body_hash = memory_content_hash({"content": content, "tenant_id": tenant_id, "project": project})
    uid = upstream_id if upstream_id is not None else body_hash
    handle = external_source_handle(provider_id=provider_id, tenant_id=tenant_id, project=project, upstream_id=uid)
    artifact_id = f"memart-{memory_content_hash({'provider': provider_id, 'handle': handle, 'body': body_hash})}"
    lineage: dict[str, Any] = {
        "provider_id": provider_id,
        "external_source_handle": handle,
        "upstream_id": uid,
        "remembered_at": now,        # injected time, not wall-clock
        "version": 1,
        "transform": "remember",     # remembered != verified; this is a candidate, not a promotion
        "preserves_raw": True,       # LOSSLESS: raw content is preserved on the artifact below
        "rollback_target": handle,   # held-out/rollback pointer per lossless-distillation law
    }
    if lineage_extra:
        lineage.update(lineage_extra)
    return {
        "artifact_id": artifact_id,
        "artifact_type": MEMORY_ARTIFACT_TYPE,
        "claim_status": CANDIDATE_CLAIM_STATUS,   # candidate ONLY — never served/canonical
        "served": False,                          # explicit negatives the proofs assert
        "canonical": False,
        "tenant_id": tenant_id,
        "project": project,
        "container_tags": list(container_tags or []),
        "external_source_handle": handle,
        "lineage": lineage,
        "content_hash": body_hash,
        "content": content,                       # raw content preserved (lossless)
        "metadata": dict(metadata or {}),
        "provider_id": provider_id,
    }
