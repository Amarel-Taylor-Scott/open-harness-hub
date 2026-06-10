# Campaign worktree orchestrator

*harness* · `harness/campaign-worktree-orchestrator` · v0.1.0 · experimental

Harness pattern for coordinating multiple long-running coding agents across isolated worktrees with campaign state, worker queues, merge policy, retries, and audit logs.

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

- **raw_input**: Campaign state may include repo paths, logs, and operational traces; keep tenant-scoped.
- **derived_output**: Published summaries must omit secrets, private paths, and unreviewed user data.
- **external_calls**: External calls depend on configured worker adapters and must be declared per worker.

