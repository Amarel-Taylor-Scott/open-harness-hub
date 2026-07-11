# Reciprocal Rank Fusion

*processor* · `processor/rrf-fusion` · v0.1.0 · experimental

Merge multiple retrieval legs by reciprocal rank (k≈60) — no score normalization, robust across incompatible BM25/cosine scales, no labels needed. The default fusion; switch to convex combination once ≥50 labeled query-doc pairs exist. Deterministic (freezable).

Retrieval/prompt taxonomy step R3 (see docs/concepts/retrieval-and-prompt-taxonomy.md). One swappable method-component for the governed-model-call recipe; lift is measured at the pipeline level, not on this component.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | reranking |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



