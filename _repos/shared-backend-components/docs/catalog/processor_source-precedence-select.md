# Source-precedence / recency select

*processor* · `processor/source-precedence-select` · v0.1.0 · experimental

Where governance shows up at read time: primary, signed, valid-through sources win ties; contradictions across sources are FLAGGED rather than silently averaged. Needs source metadata + a precedence policy. Deterministic.

Retrieval/prompt taxonomy step R5 (see docs/concepts/retrieval-and-prompt-taxonomy.md). One swappable method-component for the governed-model-call recipe; lift is measured at the pipeline level, not on this component.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | governance, routing |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



