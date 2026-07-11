# Stateful loop continuity harness

*harness* · `harness/stateful-loop-continuity-harness` · v0.1.0 · experimental

Harness pattern for simple recurring agent execution that re-reads instruction files, updates durable state files, and stops only when explicit completion, budget, or blocked criteria are met.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, evaluation, serving |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | dated |
| license | MIT |

**Contributes to:** `pipeline/agentic-orchestration-harness-intake`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `none` | `none` | local | False | True |

## Privacy boundaries

- **raw_input**: Loop state remains local by default.
- **derived_output**: Summaries can be published only after removing secrets and local-only notes.
- **external_calls**: No external calls are required by the harness itself.

