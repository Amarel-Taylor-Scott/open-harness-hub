# Analytics Metric Certification review harness

*harness* · `harness/analytics-metric-certification-review` · v0.1.0 · experimental

Harness for benchmarkable analytics metric certification review using persona, grep, RAG, privacy, and reusable review processors.

| axis | value |
|---|---|
| industry | data_governance.quality, sales_ops.forecasting |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/analytics-metric-certification-review`, `benchmark/analytics-metric-certification-bench`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Findings may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

