# Anti-pattern: LLM-as-judge without rubric

*pattern* · `pattern/anti-llm-as-judge-without-rubric` · v0.1.0 · stable

Asking an LLM 'is this output good?' with no rubric, no scoring dimensions, no calibration set. Scores drift by model version, sampling temperature, even prompt order. The judge becomes a different judge every release.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | evaluation |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



