# SimHash / LSH de-duplicate

*processor* · `processor/simhash-dedupe` · v0.1.0 · experimental

Remove near-duplicate chunks (SimHash fingerprint + exact-hash) that waste context budget before placement. Deterministic and cheap; threshold-tuned. Freezable.

Retrieval/prompt taxonomy step R5 (see docs/concepts/retrieval-and-prompt-taxonomy.md). One swappable method-component for the governed-model-call recipe; lift is measured at the pipeline level, not on this component.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | verification |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



