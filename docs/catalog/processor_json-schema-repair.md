# JSON Schema repair + validate

*processor* · `processor/json-schema-repair` · v0.1.0 · beta

Parse and repair JSON inside a model response, then validate against
a JSON Schema. On failure, returns `valid: false` plus the schema
errors so the upstream harness can re-prompt with the diff.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | format_conversion, verification |
| modality | text, structured |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



