# Model Eval Regression review harness

*harness* · `harness/model-eval-regression-review` · v0.1.0 · experimental

Harness for model eval regression review with redaction, retrieval, rule flags, reusable processors, and judge scoring.

| axis | value |
|---|---|
| industry | ai, ai_governance |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/model-eval-regression-review`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Outputs may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

