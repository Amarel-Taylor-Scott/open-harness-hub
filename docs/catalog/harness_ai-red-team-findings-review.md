# AI Red Team Findings review harness

*harness* · `harness/ai-red-team-findings-review` · v0.1.0 · experimental

Harness for benchmarkable ai red team findings review using persona, grep, RAG, privacy, and reusable review processors.

| axis | value |
|---|---|
| industry | ai, security.offensive |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/ai-red-team-findings-review`, `benchmark/ai-red-team-findings-bench`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Findings may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

