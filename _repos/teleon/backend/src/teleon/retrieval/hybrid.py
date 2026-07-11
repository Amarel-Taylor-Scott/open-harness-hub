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

py_const_src_teleon_retrieval_hybrid__RRF_K = 60   # the standard damping constant (Cormack et al. 2009); larger k flattens the rank weighting


def py_function_src_teleon_retrieval_hybrid__reciprocal_rank_fusion(py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__reciprocal_rank_fusion__rankings: list, k: int = py_const_src_teleon_retrieval_hybrid__RRF_K) -> list:
    """rankings: a list of ranked lists, each a sequence of doc KEYS best-first. Returns [(key, rrf_score)] best-first.
    score(d) = Σ_lists 1/(k + rank(d)) with rank 1-based; a doc absent from a list contributes nothing from that list."""
    py_local_src_teleon_retrieval_hybrid__reciprocal_rank_fusion__scores: dict = {}
    for py_local_src_teleon_retrieval_hybrid__reciprocal_rank_fusion__ranked in py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__reciprocal_rank_fusion__rankings:
        for py_local_src_teleon_retrieval_hybrid__reciprocal_rank_fusion__rank, py_local_src_teleon_retrieval_hybrid__reciprocal_rank_fusion__key in enumerate(py_local_src_teleon_retrieval_hybrid__reciprocal_rank_fusion__ranked, start=1):
            py_local_src_teleon_retrieval_hybrid__reciprocal_rank_fusion__scores[py_local_src_teleon_retrieval_hybrid__reciprocal_rank_fusion__key] = py_local_src_teleon_retrieval_hybrid__reciprocal_rank_fusion__scores.get(py_local_src_teleon_retrieval_hybrid__reciprocal_rank_fusion__key, 0.0) + 1.0 / (k + py_local_src_teleon_retrieval_hybrid__reciprocal_rank_fusion__rank)
    return sorted(py_local_src_teleon_retrieval_hybrid__reciprocal_rank_fusion__scores.items(), key=lambda py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__reciprocal_rank_fusion__kv: (-py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__reciprocal_rank_fusion__kv[1], str(py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__reciprocal_rank_fusion__kv[0])))   # ties broken stably by key


def py_function_src_teleon_retrieval_hybrid___cosine(py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__cosine__a: list, py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__cosine__b: list) -> float:
    py_local_src_teleon_retrieval_hybrid__cosine__num = sum(x * y for x, y in zip(py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__cosine__a, py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__cosine__b))
    py_local_src_teleon_retrieval_hybrid__cosine__da, py_local_src_teleon_retrieval_hybrid__cosine__db = math.sqrt(sum(x * x for x in py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__cosine__a)), math.sqrt(sum(y * y for y in py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__cosine__b))
    return py_local_src_teleon_retrieval_hybrid__cosine__num / (py_local_src_teleon_retrieval_hybrid__cosine__da * py_local_src_teleon_retrieval_hybrid__cosine__db) if py_local_src_teleon_retrieval_hybrid__cosine__da and py_local_src_teleon_retrieval_hybrid__cosine__db else 0.0


def py_function_src_teleon_retrieval_hybrid__hybrid_search(py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__hybrid_search__query: str, py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__hybrid_search__docs: list, *, py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__hybrid_search__embedder=None, py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__hybrid_search__reranker=None, py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__hybrid_search__k: int = py_const_src_teleon_retrieval_hybrid__RRF_K, top: int | None = None) -> list:
    """Fuse a VECTOR ranking (embedding cosine) and a LEXICAL ranking (reranker/BM25) over `docs` via RRF.
    docs: list[str]. Returns [(doc_index, rrf_score)] best-first. Both retrievers default to the always-available
    lexical baselines (no network); a future real embedder/cross-encoder drops in via the ports with zero change here."""
    from src.teleon.retrieval.embedding_port import py_function_src_teleon_retrieval_embedding_port__select_embedder
    from src.teleon.retrieval.reranker_port import py_function_src_teleon_retrieval_reranker_port__select_reranker
    if not py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__hybrid_search__docs:
        return []
    py_local_src_teleon_retrieval_hybrid__hybrid_search__emb = py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__hybrid_search__embedder or py_function_src_teleon_retrieval_embedding_port__select_embedder("auto")
    py_local_src_teleon_retrieval_hybrid__hybrid_search__rer = py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__hybrid_search__reranker or py_function_src_teleon_retrieval_reranker_port__select_reranker("auto")
    py_local_src_teleon_retrieval_hybrid__hybrid_search__qv = py_local_src_teleon_retrieval_hybrid__hybrid_search__emb.embed(py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__hybrid_search__query)
    py_local_src_teleon_retrieval_hybrid__hybrid_search__dvs = py_local_src_teleon_retrieval_hybrid__hybrid_search__emb.embed_batch(py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__hybrid_search__docs)
    py_local_src_teleon_retrieval_hybrid__hybrid_search__vec_ranking = [i for i, _ in sorted(enumerate(py_local_src_teleon_retrieval_hybrid__hybrid_search__dvs), key=lambda py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__hybrid_search__t: -py_function_src_teleon_retrieval_hybrid___cosine(py_local_src_teleon_retrieval_hybrid__hybrid_search__qv, py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__hybrid_search__t[1]))]   # vector signal
    py_local_src_teleon_retrieval_hybrid__hybrid_search__lex_ranking = [i for i, _ in py_local_src_teleon_retrieval_hybrid__hybrid_search__rer.rank(py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__hybrid_search__query, py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__hybrid_search__docs)]                                       # lexical/BM25 signal
    py_local_src_teleon_retrieval_hybrid__hybrid_search__fused = py_function_src_teleon_retrieval_hybrid__reciprocal_rank_fusion([py_local_src_teleon_retrieval_hybrid__hybrid_search__vec_ranking, py_local_src_teleon_retrieval_hybrid__hybrid_search__lex_ranking], k=py_arg_src_teleon_retrieval_hybrid__py_function_src_teleon_retrieval_hybrid__hybrid_search__k)
    return py_local_src_teleon_retrieval_hybrid__hybrid_search__fused[:top] if top else py_local_src_teleon_retrieval_hybrid__hybrid_search__fused
