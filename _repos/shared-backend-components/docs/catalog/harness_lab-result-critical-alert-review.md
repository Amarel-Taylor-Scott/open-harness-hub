# Lab Result Critical Alert review harness

*harness* · `harness/lab-result-critical-alert-review` · v0.1.0 · experimental

Harness for lab result critical alert review with redaction, retrieval, rule flags, reusable processors, and judge scoring.

| axis | value |
|---|---|
| industry | healthcare.clinical, healthcare.public_health |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/lab-result-critical-alert-review`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Outputs may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

