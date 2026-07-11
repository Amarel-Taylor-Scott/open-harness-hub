# Dense bi-encoder retrieve (ANN)

*processor* · `processor/dense-vector-retrieve` · v0.1.0 · experimental

Embed the query and ANN-search (HNSW/IVF) a dense vector index for paraphrase/synonymy recall BM25 misses. Sub-ms semantic recall; single-vector bottleneck on exact tokens. Pair with a lexical leg (hybrid).

Retrieval/prompt taxonomy step R1 (see docs/concepts/retrieval-and-prompt-taxonomy.md). One swappable method-component for the governed-model-call recipe; lift is measured at the pipeline level, not on this component.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | retrieval, embedding |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



