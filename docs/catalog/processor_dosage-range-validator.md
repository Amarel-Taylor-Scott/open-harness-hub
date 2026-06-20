# Dosage-range validator

*processor* · `processor/dosage-range-validator` · v0.1.0 · experimental

Validate a medication dose against weight-/age-/renal-adjusted ranges from a governed dosing corpus, flagging out-of-range and suggesting the adjusted range with citation. Deterministic; decision-support for the prescriber, not an autonomous order.

Clinical decision-SUPPORT component — DEFENSIVE only: grounds on a governed corpus, fires a deterministic gate, and/or routes to a clinician; never autonomous medical advice. Lift is measured at the pipeline level.

| axis | value |
|---|---|
| industry | healthcare |
| capability | verification |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



