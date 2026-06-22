"""hybrid — Reciprocal Rank Fusion (RRF), the standard hybrid-retrieval combine (Milvus / Llama Stack / Elastic):
merge a VECTOR ranking and a LEXICAL (BM25) ranking into one. A doc strong on EITHER signal ranks well, and — because
RRF fuses on RANK, not score — no score-scale calibration between the two retrievers is needed (the classic failure of
naive score-blending). Deterministic, pure-Python, always available (both baselines are the wired lexical ports — no
network). serves_truth=false: this RANKS candidates, it does not verify them.

  reciprocal_rank_fusion([rankA, rankB])  ->  [(key, rrf_score), ...]  best-first
  hybrid_search(query, docs)              ->  [(doc_index, rrf_score), ...]  best-first
"""
from __future__ import annotations

import math

RRF_K = 60   # the standard damping constant (Cormack et al. 2009); larger k flattens the rank weighting


def reciprocal_rank_fusion(rankings: list, k: int = RRF_K) -> list:
    """rankings: a list of ranked lists, each a sequence of doc KEYS best-first. Returns [(key, rrf_score)] best-first.
    score(d) = Σ_lists 1/(k + rank(d)) with rank 1-based; a doc absent from a list contributes nothing from that list."""
    scores: dict = {}
    for ranked in rankings:
        for rank, key in enumerate(ranked, start=1):
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: (-kv[1], str(kv[0])))   # ties broken stably by key


def _cosine(a: list, b: list) -> float:
    num = sum(x * y for x, y in zip(a, b))
    da, db = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return num / (da * db) if da and db else 0.0


def hybrid_search(query: str, docs: list, *, embedder=None, reranker=None, k: int = RRF_K, top: int | None = None) -> list:
    """Fuse a VECTOR ranking (embedding cosine) and a LEXICAL ranking (reranker/BM25) over `docs` via RRF.
    docs: list[str]. Returns [(doc_index, rrf_score)] best-first. Both retrievers default to the always-available
    lexical baselines (no network); a future real embedder/cross-encoder drops in via the ports with zero change here."""
    from src.teleon.retrieval.embedding_port import select_embedder
    from src.teleon.retrieval.reranker_port import select_reranker
    if not docs:
        return []
    emb = embedder or select_embedder("auto")
    rer = reranker or select_reranker("auto")
    qv = emb.embed(query)
    dvs = emb.embed_batch(docs)
    vec_ranking = [i for i, _ in sorted(enumerate(dvs), key=lambda t: -_cosine(qv, t[1]))]   # vector signal
    lex_ranking = [i for i, _ in rer.rank(query, docs)]                                       # lexical/BM25 signal
    fused = reciprocal_rank_fusion([vec_ranking, lex_ranking], k=k)
    return fused[:top] if top else fused
