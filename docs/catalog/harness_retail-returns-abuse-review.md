# Retail Returns Abuse review harness

*harness* · `harness/retail-returns-abuse-review` · v0.1.0 · experimental

Harness that combines persona, grep flags, RAG grounding, and judge scoring for retail returns abuse packets.

| axis | value |
|---|---|
| industry | retail, retail.support, security.fraud |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/retail-returns-abuse-review`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless the deployment explicitly configures an external model adapter.
- **derived_output**: Findings may contain sensitive operational details; publish only redacted summaries.
- **external_calls**: No external calls are required by the harness.

