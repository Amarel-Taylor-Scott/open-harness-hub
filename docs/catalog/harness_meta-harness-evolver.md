# Meta-harness evolver

*harness* · `harness/meta-harness-evolver` · v0.1.0 · experimental

Harness pattern that proposes, benchmarks, compares, and safely updates other harnesses using isolated branches, rollback paths, and human review gates.

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

- **raw_input**: Harness traces may include sensitive repo and run context; keep local or tenant-scoped.
- **derived_output**: Publish only reviewed benchmark deltas and sanitized proposal summaries.
- **external_calls**: External calls depend on configured proposer and evaluator adapters.

