# Allergy / contraindication check

*processor* · `processor/allergy-contraindication-check` · v0.1.0 · experimental

Check ordered medications/procedures against the patient's documented allergies and contraindicated conditions (e.g. NSAID with CKD, penicillin allergy). Deterministic conflict detection with the documented source — blocks contraindicated orders, routes to review.

Clinical decision-SUPPORT component — DEFENSIVE only: grounds on a governed corpus, fires a deterministic gate, and/or routes to a clinician; never autonomous medical advice. Lift is measured at the pipeline level.

| axis | value |
|---|---|
| industry | healthcare |
| capability | verification, safety_gating |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



