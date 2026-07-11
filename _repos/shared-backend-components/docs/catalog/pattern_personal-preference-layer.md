# Personal preference layer

*pattern* · `pattern/personal-preference-layer` · v0.1.0 · beta

Treat individual user preferences as a first-class layer on top of any pipeline. The layer loads a preference knowledge pack at run-start, applies it to the persona system prompt, runs a personal-style GREP rule pack against generated output before delivery, and refuses to ship output that violates a hard-strictness preference. Preferences are stored locally, versioned, forkable.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | safety_gating, evaluation |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



