# Travel Disruption Care review harness

*harness* · `harness/travel-disruption-care-review` · v0.1.0 · experimental

Harness for travel disruption care review with redaction, retrieval, rule flags, reusable processors, and judge scoring.

| axis | value |
|---|---|
| industry | hospitality, transportation |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/travel-disruption-care-review`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Outputs may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

