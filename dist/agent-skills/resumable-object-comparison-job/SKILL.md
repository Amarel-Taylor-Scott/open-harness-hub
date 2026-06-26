---
name: resumable-object-comparison-job
description: Compare large sets of knowledge objects using blocking, leaf shards,
  and checkpoints so workers can resume record-by-record comparisons across runs.
when_to_use: 'Pipeline kind: research_web.resumable_object_comparison.'
---

# Resumable object comparison job

Plans blocked knowledge-object pairwise comparison leaves from normalized objects plus optional labels, dimensions, entity refs, and embedding buckets, compares leaf shards, emits checkpoints, and resumes without recomparing completed pairs.

## Task

Compare large sets of knowledge objects using blocking, leaf shards, and checkpoints so workers can resume record-by-record comparisons across runs.

## Steps

1. **govern-record-set** — `tool` → `tool/source-record-governance-router`
2. **plan-blocked-leaves** — `tool` → `tool/object-comparison-block-planner`
3. **compare-one-leaf** — `tool` → `tool/object-comparison-leaf-worker`
4. **dedupe-comparison-candidates** — `tool` → `tool/fuzzy-dedupe-clusterer`
5. **emit-comparison-index** — `tool` → `tool/index-record-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/object-comparison-job-patterns`, `knowledge-pack/hybrid-comparison-blocking-patterns`

## Success criteria

- semantic must_cover ['block_fields', 'block_mode', 'leaf_count', 'remaining_pair_count', 'skipped_completed_pair_count'] against `$.comparison_job`
- deterministic `$.checkpoints` is_truthy `True`

## Provenance

- Hub component: `pipeline/resumable-object-comparison-job` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, government, cross_industry
- Full source manifest: see `references/manifest.yaml`
