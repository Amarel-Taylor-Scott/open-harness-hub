---
name: public-fact-archive-versioning
description: Create dated, archived, hashable knowledge objects for public facts so
  pipelines can cite the source version valid at review time.
when_to_use: 'Pipeline kind: research_web.public_fact_archive_versioning.'
---

# Public fact archive versioning

Track volatile public facts by querying archived captures, optionally requesting new snapshots, hashing content, diffing versions, and emitting versioned knowledge objects for RAG.

## Task

Create dated, archived, hashable knowledge objects for public facts so pipelines can cite the source version valid at review time.

## Steps

1. **lookup_archived_captures** — `tool` → `tool/web-archive-capture-lookup`
2. **request_snapshot_if_allowed** — `tool` → `tool/web-archive-snapshot-request`
3. **normalize_versioned_fact** — `tool` → `tool/search-result-normalizer`
4. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/procedure-knowledge-object-patterns`
- **rule_packs**: `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- deterministic `$.outputs.versioned_fact` is_truthy `True`

## Provenance

- Hub component: `pipeline/public-fact-archive-versioning` v0.1.0
- License: `MIT`
- Industry: ai, government, healthcare.public_health, cross_industry
- Full source manifest: see `references/manifest.yaml`
