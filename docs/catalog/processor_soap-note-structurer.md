# SOAP-note structurer

*processor* · `processor/soap-note-structurer` · v0.1.0 · experimental

Structure a dictated/free-text encounter into Subjective / Objective / Assessment / Plan sections, each item linked to its source span. Deterministic structuring; coded diagnoses are deferred to the ICD grounder so codes are never invented here.

Clinical decision-SUPPORT component — DEFENSIVE only: grounds on a governed corpus, fires a deterministic gate, and/or routes to a clinician; never autonomous medical advice. Lift is measured at the pipeline level.

| axis | value |
|---|---|
| industry | healthcare |
| capability | extraction, summarization |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



