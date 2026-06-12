#!/usr/bin/env python3
"""Backs `processor/hybrid-retrieve-fuse` (process_kind ``retrieve.hybrid``).

The recommended default retriever (taxonomy step R1): run the LEXICAL leg
(Okapi BM25 — exact-term safety) and the DENSE leg (vector cosine —
paraphrase recall) over the same corpus and fuse both candidate lists by
Reciprocal-Rank Fusion. Composed from the sibling processors — BM25, dense
and RRF each have ONE implementation in this package (single source), this
module only orchestrates them.

Contract: side_effects=read; on_error=raise; deterministic with the default
hash embedder (honestly labeled placeholder by the dense leg).

Inputs query, corpus, index(optional pre-embedded), top_k → candidates.

CLI / self-test: python3 scripts/processors/retrieval/hybrid_retrieve_fuse.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = str(Path(__file__).resolve().parents[3])
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.processors.retrieval.bm25_keyword_retrieve import run as bm25_run
from scripts.processors.retrieval.dense_vector_retrieve import run as dense_run
from scripts.processors.retrieval.rrf_fusion import DEFAULT_RRF_K, run as rrf_run

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

DEFAULT_TOP_K = 10

#: Each leg over-fetches by this factor before fusion so consensus items that
#: are mid-ranked in both legs can still reach the fused top_k.
LEG_OVERFETCH_FACTOR = 3


def run(*, query: str, corpus: list[dict[str, Any]],
        index: list[dict[str, Any]] | None = None,
        top_k: int = DEFAULT_TOP_K,
        embedder: Callable[[str], list[float]] | None = None) -> dict[str, Any]:
    """BM25 leg + dense leg + RRF fusion over one corpus."""
    if not isinstance(top_k, int) or top_k < 1:
        raise ValueError(f"top_k must be a positive int, got {top_k!r}")
    leg_k = top_k * LEG_OVERFETCH_FACTOR
    lex = bm25_run(query=query, corpus=corpus, top_k=leg_k)["candidates"]
    dense = dense_run(query=query, index=index if index is not None else corpus,
                      top_k=leg_k, embedder=embedder)["candidates"]
    fused = rrf_run(ranked_lists=[[c["id"] for c in lex],
                                  [c["id"] for c in dense["results"]]])["fused_list"]
    by_id = {str(c["id"]): str(c["text"]) for c in corpus}
    results = [{"id": f["id"], "text": by_id.get(f["id"], ""),
                "rrf_score": f["rrf_score"], "legs": f["legs"]}
               for f in fused[:top_k]]
    return {"candidates": {
        "results": results,
        "legs": {"lexical": [c["id"] for c in lex],
                 "dense": [c["id"] for c in dense["results"]]},
        "fusion": f"rrf(k={DEFAULT_RRF_K})",
        "dense_embedder": dense["embedder"],
        "dense_is_placeholder": dense["is_placeholder"],
    }}


def _selftest() -> None:
    corpus = [
        {"id": "d1", "text": "CVE-2024-3094 backdoor analysis for xz-utils"},
        {"id": "d2", "text": "provisional credit must arrive within ten business days"},
        {"id": "d3", "text": "banks investigate reported transfer errors quickly"},
        {"id": "d4", "text": "tomato gardening for beginners"},
    ]
    # Exact-term safety: the CVE query is carried by the lexical leg.
    out = run(query="CVE-2024-3094", corpus=corpus)["candidates"]
    assert out["results"][0]["id"] == "d1"
    assert "d1" in out["legs"]["lexical"]
    # Consensus beats single-leg: a query hitting d2 in both legs ranks d2 first.
    out2 = run(query="provisional credit ten days", corpus=corpus)["candidates"]
    assert out2["results"][0]["id"] == "d2" and out2["results"][0]["legs"] == 2
    # The dense leg's honesty surfaces in the envelope.
    assert out["dense_is_placeholder"] is True and "rrf(k=60)" == out["fusion"]
    # Texts ride along; top_k respected; deterministic.
    assert all(r["text"] for r in out2["results"])
    assert len(run(query="credit", corpus=corpus, top_k=2)["candidates"]["results"]) <= 2
    assert json.dumps(run(query="credit", corpus=corpus), sort_keys=True) == \
           json.dumps(run(query="credit", corpus=corpus), sort_keys=True)
    # on_error=raise propagates from the legs.
    raised = False
    try:
        run(query="x", corpus=[{"text": "no id"}])
    except ValueError:
        raised = True
    assert raised
    print("PASS — hybrid_retrieve_fuse: BM25 + dense legs composed from their single-"
          "source siblings, RRF consensus wins, exact-term safety, placeholder "
          "honesty surfaced verified")


if __name__ == "__main__":
    _selftest()
