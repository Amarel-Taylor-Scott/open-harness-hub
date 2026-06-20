# Prompt-injection screen

*processor* · `processor/prompt-injection-screen` · v0.1.0 · experimental

A guard before the model call: block (and route to review) if the input tries to extract or override the system prompt, or carries injection riding in retrieved chunks. Delimit + role-separate + heuristic/classifier screen. For governed pipelines, halt-on-detect, don't proceed.

Retrieval/prompt taxonomy step P5 (see docs/concepts/retrieval-and-prompt-taxonomy.md). One swappable method-component for the governed-model-call recipe; lift is measured at the pipeline level, not on this component.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | safety_gating |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



