# Apparel Forced Labor Trace review harness

*harness* · `harness/apparel-forced-labor-trace-review` · v0.1.0 · experimental

Harness for apparel forced labor trace review using persona, grep, RAG, privacy, reusable processors, and benchmarkable evaluation.

| axis | value |
|---|---|
| industry | esg.modern_slavery, supply_chain.due_diligence |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/apparel-forced-labor-trace-review`, `benchmark/apparel-forced-labor-trace-bench`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Findings may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

