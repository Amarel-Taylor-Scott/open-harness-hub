# System-prompt builder

*processor* · `processor/system-prompt-builder` · v0.1.0 · experimental

Assemble the instruction contract — task, hard constraints, the grounding/citation requirement, and an explicit abstention policy ('if the corpus doesn't support it, say so') — SEPARATE from the persona. The cite-or-abstain contract is what converts retrieval into governed output.

Retrieval/prompt taxonomy step P2 (see docs/concepts/retrieval-and-prompt-taxonomy.md). One swappable method-component for the governed-model-call recipe; lift is measured at the pipeline level, not on this component.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | generation, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



