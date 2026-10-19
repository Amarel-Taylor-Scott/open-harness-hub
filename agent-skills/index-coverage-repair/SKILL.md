---
name: index-coverage-repair
description: Find missing keyword, vector, graph, facet, or quality index records
  in staged component rows and produce repair JSONL without mutating a database.
when_to_use: 'Pipeline kind: research_web.index_coverage_repair.'
---

# Index coverage repair

Audits staged component candidate batches and emits missing hybrid-search index records before promotion readiness or database loading.

## Task

Find missing keyword, vector, graph, facet, or quality index records in staged component rows and produce repair JSONL without mutating a database.

## Steps

1. **load-index-coverage-patterns** — `knowledge_pack` → `knowledge-pack/index-coverage-repair-patterns`
2. **plan-index-coverage-repair** — `tool` → `tool/index-coverage-repair-planner`
3. **route-repair-output** — `tool` → `tool/object-factory-job-router`

## Defaults

- **knowledge_packs**: `knowledge-pack/index-coverage-repair-patterns`

## Success criteria

- deterministic `$.index_coverage_repair_plan.counts.normalized_objects` > `0`
- deterministic `$.index_coverage_repair_plan.counts.missing_index_records_emitted` >= `0`
- semantic must_cover ['keyword index', 'vector index', 'graph index', 'facet index', 'quality index', 'no database side effects'] against `$.index_coverage_repair_plan`

## Provenance

- Hub component: `pipeline/index-coverage-repair` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
