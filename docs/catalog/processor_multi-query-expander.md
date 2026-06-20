# Multi-query / RAG-fusion expander

*processor* · `processor/multi-query-expander` · v0.1.0 · experimental

Rephrase the query into N variants, retrieve each, and union via RRF — covers multiple phrasings and lifts recall when a single transform is insufficient. N× retrieval; the recall escalation.

Retrieval/prompt taxonomy step R0 (see docs/concepts/retrieval-and-prompt-taxonomy.md). One swappable method-component for the governed-model-call recipe; lift is measured at the pipeline level, not on this component.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | generation, retrieval |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



