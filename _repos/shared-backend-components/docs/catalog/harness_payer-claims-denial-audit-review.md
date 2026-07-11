# Payer Claims Denial Audit review harness

*harness* · `harness/payer-claims-denial-audit-review` · v0.1.0 · experimental

Harness for payer claims denial audit review using persona, grep, RAG, privacy, reusable processors, and benchmarkable evaluation.

| axis | value |
|---|---|
| industry | healthcare.payer, insurance.claims |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/payer-claims-denial-audit-review`, `benchmark/payer-claims-denial-audit-bench`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Findings may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

