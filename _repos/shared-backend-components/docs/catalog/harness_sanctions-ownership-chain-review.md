# Sanctions Ownership Chain review harness

*harness* · `harness/sanctions-ownership-chain-review` · v0.1.0 · experimental

Harness for benchmarkable sanctions ownership chain review using persona, grep, RAG, privacy, and reusable review processors.

| axis | value |
|---|---|
| industry | trade.sanctions, finance.kyc |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/sanctions-ownership-chain-review`, `benchmark/sanctions-ownership-chain-bench`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Findings may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

