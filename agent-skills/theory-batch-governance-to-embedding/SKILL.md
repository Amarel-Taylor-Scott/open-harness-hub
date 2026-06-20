---
name: theory-batch-governance-to-embedding
description: Prepare theory-derived component candidates for candidate-table load,
  review, and embedding execution.
when_to_use: 'Pipeline kind: research_web.theory_batch_governance_to_embedding.'
---

# Theory batch governance to embedding

Connects a theory-derived component batch to promotion readiness, review queues, embedding execution planning, and vector readiness without mutating Postgres.

## Task

Prepare theory-derived component candidates for candidate-table load, review, and embedding execution.

## Steps

1. **plan-governance-and-embeddings** — `tool` → `tool/theory-batch-governance-bridge`
2. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/theory-to-component-patterns`

## Success criteria

- deterministic `$.steps.plan-governance-and-embeddings.promotion.counts.candidate_load_ready` >= `1000`
- deterministic `$.steps.plan-governance-and-embeddings.embedding.planned_completion_rows` >= `1000`

## Provenance

- Hub component: `pipeline/theory-batch-governance-to-embedding` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, security.defensive, cross_industry
- Full source manifest: see `references/manifest.yaml`
