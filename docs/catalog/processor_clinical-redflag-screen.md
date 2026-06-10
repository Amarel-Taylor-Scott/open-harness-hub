# Clinical red-flag screen

*processor* · `processor/clinical-redflag-screen` · v0.1.0 · experimental

Deterministic pattern screen over a clinical note + vitals for time-critical RED-FLAG syndromes (ACS: chest pain + radiation + diaphoresis; sepsis: qSOFA; stroke: FAST; PE). On a fired flag it ESCALATES to a clinician and forbids reassurance — decision-support, not a diagnosis. The bare model's most dangerous failure is missing these; this gate catches them with no model call.

Clinical decision-SUPPORT component — DEFENSIVE only: grounds on a governed corpus, fires a deterministic gate, and/or routes to a clinician; never autonomous medical advice. Lift is measured at the pipeline level.

| axis | value |
|---|---|
| industry | healthcare |
| capability | safety_gating, classification |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



