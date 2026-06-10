# Extractive span selector

*processor* · `processor/extractive-span-selector` · v0.1.0 · experimental

Deterministically select the query-relevant spans from reranked chunks — cheap, faithful, keeps the EXACT citable text (no paraphrase). Preferred compression for governed pipelines (freezable).

Retrieval/prompt taxonomy step R4 (see docs/concepts/retrieval-and-prompt-taxonomy.md). One swappable method-component for the governed-model-call recipe; lift is measured at the pipeline level, not on this component.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | summarization, extraction |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



