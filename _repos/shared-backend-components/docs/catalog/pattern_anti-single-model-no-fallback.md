# Anti-pattern: Single-model dependency with no fallback

*pattern* · `pattern/anti-single-model-no-fallback` · v0.1.0 · stable

Pipeline hard-codes one model adapter. Production fails entirely when the model has an outage, rate-limit, region-block, deprecation, or quality regression. No graceful degradation, no second-best path.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | generation |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



