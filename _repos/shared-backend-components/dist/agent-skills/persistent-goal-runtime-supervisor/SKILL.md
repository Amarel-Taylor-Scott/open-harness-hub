---
name: persistent-goal-runtime-supervisor
description: Harness pattern for long-running coding-agent work where a durable goal
  object, completion audit, budget guard, and checkpoint log survive ordinary chat
  compaction and terminal restarts.
when_to_use: Use when the user needs governance. Use when the user needs evaluation.
  Use when the user needs serving. Particularly relevant for ai. Particularly relevant
  for software.devops.
---

# Persistent goal runtime supervisor

Harness pattern for long-running coding-agent work where a durable goal object, completion audit, budget guard, and checkpoint log survive ordinary chat compaction and terminal restarts.

## Applied layers

- `tools`
- `privacy`
- `heuristic`

## Privacy boundaries

- **raw_input**: Goal state may include repository paths and operational details; keep local unless deployment explicitly exports traces.
- **derived_output**: Checkpoint summaries may be shared after redacting secrets, file-system-sensitive paths, and private user notes.
- **external_calls**: No external calls are required by the harness itself.

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `none` | `none` | local | False | True |

## Provenance

- Hub component: `harness/persistent-goal-runtime-supervisor` v0.1.0
- License: `MIT`
- Lifecycle: `experimental`
- Full source manifest: see `references/manifest.yaml`
