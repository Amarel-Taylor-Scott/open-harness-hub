# School IEP Compliance review harness

*harness* · `harness/school-iep-compliance-review` · v0.1.0 · experimental

Harness for school iep compliance review with redaction, retrieval, rule flags, reusable processors, and judge scoring.

| axis | value |
|---|---|
| industry | education.k12 |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/school-iep-compliance-review`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Outputs may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

