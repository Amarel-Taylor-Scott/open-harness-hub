---
name: agentic-orchestration-harness-intake
description: Convert agentic orchestration landscape notes into reusable harness patterns
  and generated rows for the million-object factory.
when_to_use: 'Pipeline kind: agent_loop.'
---

# Agentic orchestration harness intake

Normalizes long-running agent orchestration patterns into reusable harness manifests, generated database rows, budget controls, and review tickets.

## Task

Convert agentic orchestration landscape notes into reusable harness patterns and generated rows for the million-object factory.

## Steps

1. **persistent-goal-runtime** — `harness` → `harness/persistent-goal-runtime-supervisor`
2. **stateful-loop-baseline** — `harness` → `harness/stateful-loop-continuity-harness`
3. **campaign-orchestration** — `harness` → `harness/campaign-worktree-orchestrator`
4. **meta-harness-evolution** — `harness` → `harness/meta-harness-evolver`
5. **record-campaign-state** — `tool` → `tool/agent-campaign-state-recorder`
6. **guard-budget** — `tool` → `tool/agent-harness-budget-guard`

## Defaults

- **knowledge_packs**: `knowledge-pack/agentic-orchestration-harness-patterns`

## Success criteria

- semantic must_cover ['persistent goal runtime', 'stateful loop continuity', 'campaign worktree orchestration', 'meta-harness evolution', 'budget and permission guardrails'] against `$.harness_manifests`
- deterministic `$.campaign_state` is_truthy `True`

## Provenance

- Hub component: `pipeline/agentic-orchestration-harness-intake` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
