# Customs Valuation Review review harness

*harness* · `harness/customs-valuation-review-review` · v0.1.0 · experimental

Harness for benchmarkable customs valuation review review using persona, grep, RAG, privacy, and reusable review processors.

| axis | value |
|---|---|
| industry | customs.entry, trade.hts |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/customs-valuation-review-review`, `benchmark/customs-valuation-review-bench`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Findings may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

