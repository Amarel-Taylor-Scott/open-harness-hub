# Customer Renewal Risk review harness

*harness* · `harness/customer-renewal-risk-review` · v0.1.0 · experimental

Composable review harness for customer renewal risk packets using persona, grep, RAG, privacy, and evaluation layers.

| axis | value |
|---|---|
| industry | customer_success, customer_success.renewal |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/customer-renewal-risk-review`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Review output may contain sensitive operational details and should be redacted before publication.
- **external_calls**: No external calls are required by this harness.

