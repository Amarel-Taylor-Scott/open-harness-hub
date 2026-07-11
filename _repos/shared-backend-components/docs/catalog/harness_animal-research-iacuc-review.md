# Animal Research IACUC review harness

*harness* · `harness/animal-research-iacuc-review` · v0.1.0 · experimental

Harness for animal research iacuc review using persona, grep, RAG, privacy, reusable processors, and benchmarkable evaluation.

| axis | value |
|---|---|
| industry | research.animal_welfare, scientific_research.bio |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/animal-research-iacuc-review`, `benchmark/animal-research-iacuc-bench`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Findings may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

