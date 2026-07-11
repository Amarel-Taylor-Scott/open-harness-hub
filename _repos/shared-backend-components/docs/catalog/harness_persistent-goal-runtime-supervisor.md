# Persistent goal runtime supervisor

*harness* · `harness/persistent-goal-runtime-supervisor` · v0.1.0 · experimental

Harness pattern for long-running coding-agent work where a durable goal object, completion audit, budget guard, and checkpoint log survive ordinary chat compaction and terminal restarts.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, evaluation, serving |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | dated |
| license | MIT |

**Contributes to:** `pipeline/agentic-orchestration-harness-intake`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `none` | `none` | local | False | True |

## Privacy boundaries

- **raw_input**: Goal state may include repository paths and operational details; keep local unless deployment explicitly exports traces.
- **derived_output**: Checkpoint summaries may be shared after redacting secrets, file-system-sensitive paths, and private user notes.
- **external_calls**: No external calls are required by the harness itself.

