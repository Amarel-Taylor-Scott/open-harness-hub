---
name: stateful-loop-continuity-harness
description: Harness pattern for simple recurring agent execution that re-reads instruction
  files, updates durable state files, and stops only when explicit completion, budget,
  or blocked criteria are met.
when_to_use: Use when the user needs governance. Use when the user needs evaluation.
  Use when the user needs serving. Particularly relevant for ai. Particularly relevant
  for software.devops.
---

# Stateful loop continuity harness

Harness pattern for simple recurring agent execution that re-reads instruction files, updates durable state files, and stops only when explicit completion, budget, or blocked criteria are met.

## Applied layers

- `tools`
- `privacy`
- `heuristic`

## Privacy boundaries

- **raw_input**: Loop state remains local by default.
- **derived_output**: Summaries can be published only after removing secrets and local-only notes.
- **external_calls**: No external calls are required by the harness itself.

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `none` | `none` | local | False | True |

## Provenance

- Hub component: `harness/stateful-loop-continuity-harness` v0.1.0
- License: `MIT`
- Lifecycle: `experimental`
- Full source manifest: see `references/manifest.yaml`
