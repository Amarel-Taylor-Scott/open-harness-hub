# Hybrid retrieval policy (BM25 + dense + RRF)

*rule-pack* · `rule-pack/hybrid-retrieval-policy` · v0.1.0 · beta

A RAG retrieval policy pack: BM25 sparse + dense vector + Reciprocal
Rank Fusion + optional cross-encoder reranking + 1-hop citation
graph expansion. Pipelines and harnesses reference this pack to keep
retrieval behaviour consistent across the catalog.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | retrieval |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



**family:** `rag`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `bm25_default` | info | retrieval.sparse | `bm25(k1=1.2, b=0.75)` |
| `dense_optional` | info | retrieval.dense | `dense(embedder='processor/embedder-minilm', top_k=20)` |
| `rrf_merge` | info | retrieval.fusion | `rrf(k=60, top_k=10)` |
| `rerank_optional` | info | retrieval.rerank | `rerank(model='processor/cross-encoder-reranker', top_k=10, output_k=5)` |
| `citation_graph_expand` | info | retrieval.graph | `citation_graph(hops=1, max_expand=5)` |
| `redact_chunks_if_pii` | high | retrieval.safety | `redact(rule_pack='rule-pack/privacy-pii-text-en')` |
| `freshness_window_default` | info | retrieval.freshness | `freshness_days=180` |
| `top_k_default` | info | retrieval.budget | `top_k=10` |
| `max_chunk_tokens_default` | info | retrieval.budget | `max_chunk_tokens=512` |
| `min_score_threshold` | low | retrieval.quality | `min_score=0.30` |

