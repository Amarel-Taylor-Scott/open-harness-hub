# HyDE query expander

*processor* · `processor/hyde-query-expander` · v0.1.0 · experimental

Generate a hypothetical answer-document with the model and embed it to bridge the short-query↔long-doc gap for dense retrieval. Strong zero-shot recall lift; one LLM call + hallucination risk, so reserve for short/conversational queries against long technical corpora.

Retrieval/prompt taxonomy step R0 (see docs/concepts/retrieval-and-prompt-taxonomy.md). One swappable method-component for the governed-model-call recipe; lift is measured at the pipeline level, not on this component.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | generation, retrieval |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



