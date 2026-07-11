---
name: candidate-primitive-promotion-scoring
description: Score candidate primitives using usefulness, demand, complexity, time
  savings, deployment frequency, capability gap, cost savings, deployment value, model-swap
  value, privacy risk, license risk, and dedupe risk.
when_to_use: 'Pipeline kind: research_web.candidate_primitive_promotion_scoring.'
---

# Candidate primitive promotion scoring

Score normalized candidate primitives for promotion readiness and route them to promotion, review, hold, or reject queues with quality index records.

## Task

Score candidate primitives using usefulness, demand, complexity, time savings, deployment frequency, capability gap, cost savings, deployment value, model-swap value, privacy risk, license risk, and dedupe risk.

## Steps

1. **load_promotion_patterns** — `knowledge_pack` → `knowledge-pack/candidate-primitive-promotion-patterns`
2. **score_candidates** — `tool` → `tool/candidate-primitive-promotion-scorer`
3. **emit_quality_index** — `tool` → `tool/index-record-emitter`
4. **route_review** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/candidate-primitive-promotion-patterns`

## Success criteria

- deterministic `$.outputs.promotion_decisions` is_truthy `True`
- deterministic `$.outputs.index_records` is_truthy `True`

## Provenance

- Hub component: `pipeline/candidate-primitive-promotion-scoring` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
