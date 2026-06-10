# Research Data Management review harness

*harness* · `harness/research-data-management-review` · v0.1.0 · experimental

Harness for benchmarkable research data management review using persona, grep, RAG, privacy, and reusable review processors.

| axis | value |
|---|---|
| industry | scientific_research.social, data_governance.lineage |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/research-data-management-review`, `benchmark/research-data-management-bench`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Findings may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

