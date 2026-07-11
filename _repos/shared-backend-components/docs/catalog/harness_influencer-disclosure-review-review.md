# Influencer Disclosure Review review harness

*harness* · `harness/influencer-disclosure-review-review` · v0.1.0 · experimental

Harness for benchmarkable influencer disclosure review review using persona, grep, RAG, privacy, and reusable review processors.

| axis | value |
|---|---|
| industry | marketing_ops.claims, media.distribution |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/influencer-disclosure-review-review`, `benchmark/influencer-disclosure-review-bench`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Findings may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

