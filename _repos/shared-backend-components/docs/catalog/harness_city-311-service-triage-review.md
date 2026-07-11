# City 311 Service Triage review harness

*harness* · `harness/city-311-service-triage-review` · v0.1.0 · experimental

Harness for benchmarkable city 311 service triage review using persona, grep, RAG, privacy, and reusable review processors.

| axis | value |
|---|---|
| industry | government.benefits, facilities.maintenance |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/city-311-service-triage-review`, `benchmark/city-311-service-triage-bench`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Findings may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

