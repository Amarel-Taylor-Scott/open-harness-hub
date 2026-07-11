# Anti-pattern: Missing determinism / seed control

*pattern* · `pattern/anti-missing-determinism-seed` · v0.1.0 · stable

Pipeline reports a finding 'pesticide REI violation' on Tuesday + clean on Wednesday for the same input. Temperature > 0, no seed, no run-id, no model-version pin. Disagreements between runs cannot be diagnosed: was it the input, the model, the temperature, the sampling, the load balancer?

| axis | value |
|---|---|
| industry | cross_industry |
| capability | evaluation |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



