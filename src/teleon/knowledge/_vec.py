"""knowledge._vec — shared embedding + cosine helpers for the Global Software Knowledge Graph.

The embedder is a PLANE (fork/variation law): runtime defaults to best_embedder() (local Ollama nomic-embed when
present, lexical floor otherwise), but any callable can be injected — proofs inject the deterministic lexical floor
so the gate is embedder-agnostic and fast (no network)."""
from __future__ import annotations

import math

_DEFAULT = None


def _default_embedder():
    global _DEFAULT
    if _DEFAULT is None:
        from ..retrieval.embedding_port import best_embedder
        _DEFAULT = best_embedder()
    return _DEFAULT


def embed(text: str, embed_fn=None) -> list[float]:
    if embed_fn is not None:
        return embed_fn(text or "")
    return _default_embedder().embed(text or "")


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def lexical_embed_fn():
    """The deterministic, keyless lexical embedder (one fork) — used by proofs for reproducibility."""
    from ..retrieval.embedding_port import LexicalEmbedder
    return LexicalEmbedder().embed
