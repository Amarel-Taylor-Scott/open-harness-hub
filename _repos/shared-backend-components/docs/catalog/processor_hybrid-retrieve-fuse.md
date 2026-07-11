# Hybrid retrieve (lexical + dense)

*processor* · `processor/hybrid-retrieve-fuse` · v0.1.0 · experimental

Run a lexical (BM25) leg and a dense leg in parallel and hand both candidate lists to fusion (R3). The recommended default: exact-term safety + semantic recall. Most tasks start here.

Retrieval/prompt taxonomy step R1 (see docs/concepts/retrieval-and-prompt-taxonomy.md). One swappable method-component for the governed-model-call recipe; lift is measured at the pipeline level, not on this component.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | retrieval |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



