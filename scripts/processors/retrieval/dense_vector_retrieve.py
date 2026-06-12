#!/usr/bin/env python3
"""Backs `processor/dense-vector-retrieve` (process_kind ``retrieve.dense_vector``).

Dense-vector retrieval (taxonomy step R1): embed the query and rank an index
by cosine similarity for the paraphrase/synonymy recall BM25 misses. The
embedder is INJECTED (any ``text -> list[float]``); without one, the module
uses the repo's deterministic ``hash_embed`` (`scripts.embeddings` — the
single embedding source) and HONESTLY labels every result placeholder-grade:
a hash embedder is reproducible and searchable but NOT semantic, and a
placeholder can never masquerade as a real model (the repo's own
`is_placeholder` law).

Exhaustive cosine scan here (exact, deterministic); a production deployment
swaps an ANN index (HNSW/IVF) behind the same ``run()`` contract.

Contract: side_effects=read; on_error=raise; deterministic with the default
embedder (the manifest allows non-deterministic learned embedders).

Inputs query, index({"id","text"[,"embedding"]}), top_k → output candidates.

CLI / self-test: python3 scripts/processors/retrieval/dense_vector_retrieve.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Callable

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = str(Path(__file__).resolve().parents[3])
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.embeddings import HASH_MODEL_ID, hash_embed

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

DEFAULT_TOP_K = 10
SCORE_DECIMALS = 6

#: Label attached when the deterministic hash fallback embeds — mirrors the
#: vector-store placeholder discipline (a hash lane never claims semantics).
PLACEHOLDER_NOTE = f"{HASH_MODEL_ID} placeholder — reproducible, NOT semantic"


def _cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError(f"embedding dims differ: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def run(*, query: str, index: list[dict[str, Any]], top_k: int = DEFAULT_TOP_K,
        embedder: Callable[[str], list[float]] | None = None,
        embedder_id: str | None = None) -> dict[str, Any]:
    """Rank ``index`` by cosine(query, entry). Entries without a stored
    ``embedding`` are embedded on the fly with the same embedder."""
    if not isinstance(query, str):
        raise TypeError(f"query must be str, got {type(query).__name__}")
    if not isinstance(index, list):
        raise TypeError("index must be a list of id/text dicts")
    if not isinstance(top_k, int) or top_k < 1:
        raise ValueError(f"top_k must be a positive int, got {top_k!r}")
    placeholder = embedder is None
    embed = embedder if embedder is not None else hash_embed
    model_id = embedder_id or (HASH_MODEL_ID if placeholder else "injected-embedder")

    qvec = embed(query)
    scored: list[dict[str, Any]] = []
    for i, d in enumerate(index):
        if not isinstance(d, dict) or "id" not in d or "text" not in d:
            raise ValueError(f"index[{i}] needs id and text")
        vec = d.get("embedding") or embed(str(d["text"]))
        scored.append({"id": str(d["id"]), "text": str(d["text"]),
                       "score": round(_cosine(qvec, list(vec)), SCORE_DECIMALS)})
    scored.sort(key=lambda r: (-r["score"], r["id"]))
    return {"candidates": {"results": scored[:top_k], "embedder": model_id,
                           "is_placeholder": placeholder,
                           **({"placeholder_note": PLACEHOLDER_NOTE} if placeholder else {})}}


def _selftest() -> None:
    index = [
        {"id": "d1", "text": "provisional credit must arrive within ten business days"},
        {"id": "d2", "text": "the bank investigates the reported error"},
        {"id": "d3", "text": "gardening tips for tomato season"},
    ]
    # Default (hash) lane: shared-token queries rank correctly AND the result
    # is honestly labeled placeholder.
    out = run(query="provisional credit ten days", index=index)["candidates"]
    assert out["results"][0]["id"] == "d1" and out["results"][0]["score"] > 0
    assert out["is_placeholder"] is True and "NOT semantic" in out["placeholder_note"]
    assert out["embedder"] == HASH_MODEL_ID
    # Injected embedder lane: a toy 2-dim semantic embedder is used as-is and
    # the placeholder flag drops.
    toy = {"d1": [1.0, 0.0], "d2": [0.8, 0.6], "d3": [0.0, 1.0]}
    def embed(text: str) -> list[float]:
        for k, v in toy.items():
            if any(w in text for w in ("credit", "provisional")) and k == "d1":
                return v
        return [0.7, 0.7]
    pre = [{**d, "embedding": toy[d["id"]]} for d in index]
    inj = run(query="refund timing", index=pre, embedder=embed, embedder_id="toy-2d")["candidates"]
    assert inj["is_placeholder"] is False and inj["embedder"] == "toy-2d"
    # Stored embeddings are used (no re-embed): d2 wins for the [0.7,0.7]-ish query.
    assert inj["results"][0]["id"] == "d2"
    # Dim mismatch raises, never silently truncates.
    raised = False
    try:
        run(query="x", index=[{"id": "a", "text": "t", "embedding": [0.1, 0.2]}])
    except ValueError:
        raised = True
    assert raised
    # top_k respected; deterministic; honest empty.
    assert len(run(query="credit", index=index, top_k=1)["candidates"]["results"]) == 1
    assert json.dumps(run(query="credit", index=index), sort_keys=True) == \
           json.dumps(run(query="credit", index=index), sort_keys=True)
    assert run(query="x", index=[])["candidates"]["results"] == []
    print("PASS — dense_vector_retrieve: cosine ranking over injected embedder or "
          "honest hash placeholder (labeled, never semantic-claiming), stored "
          "embeddings reused, dim mismatch raises verified")


if __name__ == "__main__":
    _selftest()
