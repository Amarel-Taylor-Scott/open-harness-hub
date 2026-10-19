---
name: partition-registry-replay-audit
description: Build or refresh a partition registry, replay index deltas, and emit
  a report that catches duplicate deltas, missing files, content-hash mismatches,
  and unsupported operations.
when_to_use: 'Pipeline kind: research_web.partition_registry_replay_audit.'
---

# Partition registry replay audit

Build a registry of partition manifests and replay their index deltas to prove additive ingestion can update affected index state without rebuilding the whole catalog.

## Task

Build or refresh a partition registry, replay index deltas, and emit a report that catches duplicate deltas, missing files, content-hash mismatches, and unsupported operations.

## Steps

1. **load_replay_audit_patterns** — `knowledge_pack` → `knowledge-pack/partition-replay-audit-patterns`
2. **build_registry_and_replay** — `tool` → `tool/partition-registry-replay-verifier`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/partition-replay-audit-patterns`

## Success criteria

- deterministic `$.outputs.replay_report.ok` == `True`
- deterministic `$.outputs.partition_registry.partition_count` >= `1`

## Provenance

- Hub component: `pipeline/partition-registry-replay-audit` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
