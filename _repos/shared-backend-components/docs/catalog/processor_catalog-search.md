# Catalog search (BM25 + tag-set Jaccard) — stage 1 of pipeline recommendation

*processor* · `processor/catalog-search` · v0.1.0 · experimental

Lightweight, stdlib-only retrieval over the OHH catalog. Stage 1 of
the pipeline-recommendation flow that powers "I need a pipeline to
do XYZ":

 1. catalog-search  — BM25 + tag-set Jaccard → top 30 candidates
 2. gemma-reranker  — Gemma 4 (or any local LLM) → top 5
 3. pipeline-recommender — composition sketch + rationale

Signals combined:
 - BM25 token overlap on (name + description + tags) — primary
 - Tag-set Jaccard on (industry, capability, modality, tags) — boost
 - Type bias — pipelines + harnesses + tools weighted up
 - Heuristic structural hints from the prompt (ESG, CSDDD, GDPR,
   etc. → industry/tag hints)

Cheap. No embedding model required. Optional embedding signal can
be added later by attaching a precomputed vector index.

| axis | value |
|---|---|
| industry | software, ai, cross_industry |
| capability | retrieval, reranking |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



