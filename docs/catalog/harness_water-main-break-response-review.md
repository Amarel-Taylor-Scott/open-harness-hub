# Water Main Break Response review harness

*harness* · `harness/water-main-break-response-review` · v0.1.0 · experimental

Harness for benchmarkable water main break response review using persona, grep, RAG, privacy, and reusable review processors.

| axis | value |
|---|---|
| industry | water_utility.sdwa, environmental.water |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/water-main-break-response-review`, `benchmark/water-main-break-response-bench`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Findings may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

