---
name: meta-harness-evolver
description: Harness pattern that proposes, benchmarks, compares, and safely updates
  other harnesses using isolated branches, rollback paths, and human review gates.
when_to_use: Use when the user needs governance. Use when the user needs evaluation.
  Use when the user needs serving. Particularly relevant for ai. Particularly relevant
  for software.devops.
---

# Meta-harness evolver

Harness pattern that proposes, benchmarks, compares, and safely updates other harnesses using isolated branches, rollback paths, and human review gates.

## Applied layers

- `tools`
- `privacy`
- `heuristic`
- `classifier`

## Privacy boundaries

- **raw_input**: Harness traces may include sensitive repo and run context; keep local or tenant-scoped.
- **derived_output**: Publish only reviewed benchmark deltas and sanitized proposal summaries.
- **external_calls**: External calls depend on configured proposer and evaluator adapters.

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `none` | `none` | local | False | True |

## Provenance

- Hub component: `harness/meta-harness-evolver` v0.1.0
- License: `MIT`
- Lifecycle: `experimental`
- Full source manifest: see `references/manifest.yaml`
