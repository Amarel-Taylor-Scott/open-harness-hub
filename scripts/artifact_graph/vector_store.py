#!/usr/bin/env python3
"""scripts.artifact_graph.vector_store — pluggable VectorProvider; deterministic local provider + search.

Proves the vector lifecycle (artifact → vector → nearest-neighbour → graph linkage) with NO network and NO
paid API: DeterministicLocalVectorProvider hashes a lexical bag-of-words into a fixed-dimension, L2-normalised
vector — stable byte-for-byte across runs. The EmbeddingProvider seam (sentence-transformers / OpenAI /
Cohere / Gemini, and pgvector/Qdrant/LanceDB backends) is a later swap behind the SAME interface; every
vector row records provider/model/version/dimensions so the lifecycle is provider-agnostic.

The vector store does NOT blur governance: search can filter by artifact_type, so a semantically-similar
narrative_allegation is never returned as if it were an atomic_fact.

CLI: imported by scripts/check_cfpb_vectorization.py and the orchestrator.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import Iterable

from scripts.artifact_graph.artifact_ledger import EPOCH, ArtifactGraphLedger, Vector, chash

DIMENSIONS = 64
_WORD = re.compile(r"[A-Za-z0-9']+")

#: artifact types worth vectorising (retrieval units) — excludes pure containers/receipts.
VECTORIZABLE = ("atomic_fact", "narrative_allegation", "sentence", "conclusion", "context_object", "entity_mention")


class VectorProvider:
    provider = "base"
    model = "base"
    version = "v0"
    dimensions = DIMENSIONS

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError


class DeterministicLocalVectorProvider(VectorProvider):
    """Stable hashed-lexical vector — no network, no pip, deterministic across runs."""
    provider = "deterministic_local"
    model = "hashed_lexical"
    version = "v1"
    dimensions = DIMENSIONS

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dimensions
        for tok in _WORD.findall((text or "").lower()):
            h = int(hashlib.sha256(tok.encode()).hexdigest(), 16)
            vec[h % self.dimensions] += 1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [round(x / norm, 8) for x in vec]


def vectorize_artifact(provider: VectorProvider, artifact, *, now: str = EPOCH) -> Vector:
    vec = provider.embed(artifact.text or "")
    return Vector(vector_id=f"vec:{artifact.artifact_id}", tenant_id=artifact.tenant_id,
                  artifact_id=artifact.artifact_id, vector_provider=provider.provider, vector_model=provider.model,
                  vector_version=provider.version, dimensions=provider.dimensions, vector_json=vec,
                  content_hash=chash({"v": vec, "p": provider.provider, "m": provider.model}), created_at=now)


def vectorize_into_ledger(ledger: ArtifactGraphLedger, provider: VectorProvider, artifacts: Iterable,
                          *, types: tuple = VECTORIZABLE, now: str = EPOCH) -> int:
    n = 0
    for a in artifacts:
        if a.artifact_type in types:
            ledger.put_vector(vectorize_artifact(provider, a, now=now)); n += 1
    return n


def _cosine(a: list[float], b: list[float]) -> float:
    return round(sum(x * y for x, y in zip(a, b)), 8)  # both are L2-normalised → dot == cosine


def search_similar(ledger: ArtifactGraphLedger, provider: VectorProvider, tenant_id: str, *,
                   query_text: str | None = None, artifact_id: str | None = None,
                   artifact_types: tuple | None = None, k: int = 5) -> list[dict]:
    if query_text is not None:
        qv = provider.embed(query_text)
    elif artifact_id is not None:
        rows = ledger.vectors(tenant_id, artifact_id)
        if not rows:
            return []
        qv = rows[0]["vector_json"]
    else:
        return []
    allowed = None
    if artifact_types:
        allowed = {a["artifact_id"] for t in artifact_types for a in ledger.artifacts(tenant_id, t)}
    scored = []
    for v in ledger.vectors(tenant_id):
        if v["artifact_id"] == artifact_id:
            continue
        if allowed is not None and v["artifact_id"] not in allowed:
            continue
        scored.append({"artifact_id": v["artifact_id"], "score": _cosine(qv, v["vector_json"])})
    scored.sort(key=lambda r: (-r["score"], r["artifact_id"]))
    return scored[:k]
