# ICD-10 code grounder

*processor* · `processor/icd10-code-grounder` · v0.1.0 · experimental

Resolve each candidate diagnosis to an ICD-10-CM code via exact-id lookup against a terminology corpus and link it to the documented evidence span. Undocumented diagnoses are left UNCODED (abstain) — eliminates the bare model's habit of fabricating plausible-but-wrong codes.

Clinical decision-SUPPORT component — DEFENSIVE only: grounds on a governed corpus, fires a deterministic gate, and/or routes to a clinician; never autonomous medical advice. Lift is measured at the pipeline level.

| axis | value |
|---|---|
| industry | healthcare |
| capability | extraction, verification |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



