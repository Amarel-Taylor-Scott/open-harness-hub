# Drug-interaction checker

*processor* · `processor/drug-interaction-checker` · v0.1.0 · experimental

Deterministic lookup of every drug pair in a medication list against a governed interaction corpus (e.g. warfarin × azole-antifungals → CYP2C9 → major). Returns severity-tiered hits with the corpus citation + a prescriber-flag action — never a model guess about safety.

Clinical decision-SUPPORT component — DEFENSIVE only: grounds on a governed corpus, fires a deterministic gate, and/or routes to a clinician; never autonomous medical advice. Lift is measured at the pipeline level.

| axis | value |
|---|---|
| industry | healthcare |
| capability | verification |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



