# Contract Obligation Tracking review harness

*harness* · `harness/contract-obligation-tracking-review` · v0.1.0 · experimental

Harness for benchmarkable contract obligation tracking review using persona, grep, RAG, privacy, and reusable review processors.

| axis | value |
|---|---|
| industry | legal.contract, procurement.contracting |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/contract-obligation-tracking-review`, `benchmark/contract-obligation-tracking-bench`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Findings may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

