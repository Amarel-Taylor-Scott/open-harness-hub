# Two-stage retrieve + constrained rerank

*pattern* · `pattern/two-stage-retrieve-rerank` · v0.1.0 · stable

Retrieve K candidates with a cheap embedder (BM25 / dense), then
rerank with a stronger but slower model. The reranker can be: a
cross-encoder, or an LLM CONSTRAINED to emit only one of the K
candidate IDs (via grammar / logits processor). The constrained-
LLM variant is what wins EEDI / similar fixed-corpus tasks because
the LLM can use rich reasoning but cannot hallucinate an unseen ID.

Two flavours of "second stage" — pick based on cost / quality
budget. The query-refinement variant (two-time retrieval) adds a
second retrieve pass after LLM query reformulation.

| axis | value |
|---|---|
| industry | ai, education, scientific_research |
| capability | retrieval, reranking |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | CC-BY-4.0 |



