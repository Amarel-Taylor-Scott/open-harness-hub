---
name: campaign-worktree-orchestrator
description: Harness pattern for coordinating multiple long-running coding agents
  across isolated worktrees with campaign state, worker queues, merge policy, retries,
  and audit logs.
when_to_use: Use when the user needs governance. Use when the user needs evaluation.
  Use when the user needs serving. Particularly relevant for ai. Particularly relevant
  for software.devops.
---

# Campaign worktree orchestrator

Harness pattern for coordinating multiple long-running coding agents across isolated worktrees with campaign state, worker queues, merge policy, retries, and audit logs.

## Applied layers

- `tools`
- `privacy`
- `heuristic`

## Privacy boundaries

- **raw_input**: Campaign state may include repo paths, logs, and operational traces; keep tenant-scoped.
- **derived_output**: Published summaries must omit secrets, private paths, and unreviewed user data.
- **external_calls**: External calls depend on configured worker adapters and must be declared per worker.

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `none` | `none` | local | False | True |

## Provenance

- Hub component: `harness/campaign-worktree-orchestrator` v0.1.0
- License: `MIT`
- Lifecycle: `experimental`
- Full source manifest: see `references/manifest.yaml`
