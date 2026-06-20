---
name: component-cdc-versioning
description: Create immutable component change records and derived index/review rows
  whenever a component definition or source-backed fact changes.
when_to_use: 'Pipeline kind: research_web.component_cdc_versioning.'
---

# Component CDC versioning

Compare component version rows, compute canonical hashes, record immutable change events, emit freshness and graph index records, and route risky updates to review.

## Task

Create immutable component change records and derived index/review rows whenever a component definition or source-backed fact changes.

## Steps

1. **route_source_governance** — `tool` → `tool/source-record-governance-router`
2. **plan_change_events** — `tool` → `tool/component-cdc-planner`
3. **emit_index_deltas** — `tool` → `tool/index-record-emitter`
4. **route_review** — `tool` → `tool/source-record-governance-router`

## Defaults

- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/component-cdc-versioning-patterns`
- **rule_packs**: `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- deterministic `$.outputs.component_change_events` is_truthy `True`
- deterministic `$.outputs.index_records` is_truthy `True`

## Provenance

- Hub component: `pipeline/component-cdc-versioning` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
