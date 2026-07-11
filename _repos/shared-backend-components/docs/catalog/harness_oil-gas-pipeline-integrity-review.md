# Oil Gas Pipeline Integrity review harness

*harness* · `harness/oil-gas-pipeline-integrity-review` · v0.1.0 · experimental

Harness for oil gas pipeline integrity review using persona, grep, RAG, privacy, reusable processors, and benchmarkable evaluation.

| axis | value |
|---|---|
| industry | energy.oil_gas, infrastructure |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/oil-gas-pipeline-integrity-review`, `benchmark/oil-gas-pipeline-integrity-bench`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Findings may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

