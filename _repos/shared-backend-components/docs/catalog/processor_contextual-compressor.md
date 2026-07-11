# Contextual compressor

*processor* · `processor/contextual-compressor` · v0.1.0 · experimental

LLM extracts only the query-relevant content from each chunk to cut tokens and 'lost-in-the-middle' dilution. Strong token reduction; one model call + can drop nuance — use when extractive isn't enough.

Retrieval/prompt taxonomy step R4 (see docs/concepts/retrieval-and-prompt-taxonomy.md). One swappable method-component for the governed-model-call recipe; lift is measured at the pipeline level, not on this component.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | summarization |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



