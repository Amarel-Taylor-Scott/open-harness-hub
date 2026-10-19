---
name: promotion-decisions-to-index-deltas
description: Emit replayable partition manifests and quality/facet/cost index deltas
  from promotion decisions so high-volume candidate scoring can update operational
  indexes without a full rebuild.
when_to_use: 'Pipeline kind: research_web.promotion_decisions_to_index_deltas.'
---

# Promotion decisions to index deltas

Convert promotion-decision JSONL shards into replayable quality, facet, and cost index deltas so candidate scoring updates search indexes incrementally.

## Task

Emit replayable partition manifests and quality/facet/cost index deltas from promotion decisions so high-volume candidate scoring can update operational indexes without a full rebuild.

## Steps

1. **load_promotion_delta_patterns** — `knowledge_pack` → `knowledge-pack/promotion-index-delta-patterns`
2. **emit_promotion_index_deltas** — `tool` → `tool/promotion-index-delta-emitter`
3. **replay_audit** — `tool` → `tool/partition-registry-replay-verifier`

## Defaults

- **knowledge_packs**: `knowledge-pack/promotion-index-delta-patterns`

## Success criteria

- deterministic `$.outputs.partition_manifest` is_truthy `True`
- deterministic `$.outputs.index_deltas` is_truthy `True`

## Provenance

- Hub component: `pipeline/promotion-decisions-to-index-deltas` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
