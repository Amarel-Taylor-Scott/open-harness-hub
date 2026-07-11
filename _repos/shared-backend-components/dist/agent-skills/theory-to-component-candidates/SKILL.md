---
name: theory-to-component-candidates
description: Turn a set of theory seeds into staged component candidate row families.
when_to_use: 'Pipeline kind: research_web.theory_to_component_candidates.'
---

# Theory to component candidates

Converts technical theories and postmortems into staged, database-backed component candidates that can be deduped, indexed, reviewed, embedded, and promoted.

## Task

Turn a set of theory seeds into staged component candidate row families.

## Steps

1. **expand-theory-seeds** — `tool` → `tool/theory-component-seed-generator`
2. **audit-staged-rows** — `tool` → `tool/staged-vs-committed-load-auditor`
3. **emit-audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/theory-to-component-patterns`

## Success criteria

- deterministic `$.steps.expand-theory-seeds.seed_count` >= `1000`

## Provenance

- Hub component: `pipeline/theory-to-component-candidates` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, security.defensive, cross_industry
- Full source manifest: see `references/manifest.yaml`
