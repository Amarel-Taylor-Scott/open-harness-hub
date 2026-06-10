# Elevator Maintenance Compliance review harness

*harness* · `harness/elevator-maintenance-compliance-review` · v0.1.0 · experimental

Harness for elevator maintenance compliance review using persona, grep, RAG, privacy, reusable processors, and benchmarkable evaluation.

| axis | value |
|---|---|
| industry | infrastructure.elevator, facilities.maintenance |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/elevator-maintenance-compliance-review`, `benchmark/elevator-maintenance-compliance-bench`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Findings may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

