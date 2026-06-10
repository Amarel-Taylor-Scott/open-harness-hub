# Warehouse Safety Inventory review harness

*harness* · `harness/warehouse-safety-inventory-review` · v0.1.0 · experimental

Composable review harness for warehouse safety inventory packets using persona, grep, RAG, privacy, and evaluation layers.

| axis | value |
|---|---|
| industry | logistics, logistics.warehouse |
| capability | evaluation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Contributes to:** `pipeline/warehouse-safety-inventory-review`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `review_model` | `ollama` | local | True | True |

## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Review output may contain sensitive operational details and should be redacted before publication.
- **external_calls**: No external calls are required by this harness.

