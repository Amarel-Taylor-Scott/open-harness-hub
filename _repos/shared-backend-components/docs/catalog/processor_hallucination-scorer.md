# Hallucination scorer (SelfCheckGPT-style)

*processor* · `processor/hallucination-scorer` · v0.1.0 · experimental

Score per-sentence hallucination probability by sampling N alternative
generations from the same model, then measuring semantic agreement
between them. Sentences that vary widely across samples are flagged as
likely hallucinations. Based on SelfCheckGPT (Manakul et al. 2023).

| axis | value |
|---|---|
| industry | cross_industry |
| capability | verification, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



