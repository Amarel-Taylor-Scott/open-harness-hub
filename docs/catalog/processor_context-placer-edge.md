# Edge context placement

*processor* · `processor/context-placer-edge` · v0.1.0 · experimental

Place the most-relevant evidence at the edges (first AND last) in structured, source-tagged, delimited blocks, with task instructions last — directly mitigates the 'lost in the middle' attention drop and enables per-claim citation. Deterministic.

Retrieval/prompt taxonomy step R6 (see docs/concepts/retrieval-and-prompt-taxonomy.md). One swappable method-component for the governed-model-call recipe; lift is measured at the pipeline level, not on this component.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | format_conversion |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



