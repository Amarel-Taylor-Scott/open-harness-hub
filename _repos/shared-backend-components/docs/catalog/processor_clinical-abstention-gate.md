# Clinical abstention gate

*processor* · `processor/clinical-abstention-gate` · v0.1.0 · experimental

Block a clinical answer when the documented/retrieved evidence is insufficient to support it, routing to 'insufficient evidence — clinician review' instead of guessing. The cite-or-abstain contract that converts retrieval into safe, governed clinical decision-support.

Clinical decision-SUPPORT component — DEFENSIVE only: grounds on a governed corpus, fires a deterministic gate, and/or routes to a clinician; never autonomous medical advice. Lift is measured at the pipeline level.

| axis | value |
|---|---|
| industry | healthcare |
| capability | safety_gating, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



