# Public Health Vaccine Cold Chain review harness

*harness* · `harness/public-health-vaccine-cold-chain-review` · v0.1.0 · experimental

Harness for benchmarkable public health vaccine cold chain review using persona, grep, RAG, privacy, and reusable review processors.

| axis | value |
|---|---|
| industry | healthcare.public_health, logistics.cold_chain |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/public-health-vaccine-cold-chain-review`, `benchmark/public-health-vaccine-cold-chain-bench`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Findings may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

