---
name: local-sentence-blueprint-output-records
description: Convert a user sentence and route matrix into normalized output records
  with governance, entity linking, fuzzy dedupe, index emission, and review ticket
  routing.
when_to_use: 'Pipeline kind: meta_build.local_blueprint_records.'
---

# Local sentence blueprint output records

Turns a local sentence-to-pipeline demo request into governed, normalized, deduplicated, indexed output records that can later be stored in Postgres and searched as reusable primitives.

## Task

Convert a user sentence and route matrix into normalized output records with governance, entity linking, fuzzy dedupe, index emission, and review ticket routing.

## Steps

1. **govern-source-prompt** — `tool` → `tool/source-record-governance-router`
2. **run-local-demo** — `tool` → `tool/sentence-to-pipeline-blueprint-runner`
3. **build-route-matrix** — `pipeline` → `pipeline/costed-blueprint-route-matrix`
4. **emit-output-records** — `tool` → `tool/blueprint-output-record-emitter`
5. **link-entities** — `tool` → `tool/entity-recognition-linker`
6. **dedupe-output-records** — `tool` → `tool/fuzzy-dedupe-clusterer`
7. **emit-index-records** — `tool` → `tool/index-record-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/local-blueprint-output-record-patterns`, `knowledge-pack/costed-blueprint-route-patterns`, `knowledge-pack/local-demo-verified-fact-patterns`

## Success criteria

- semantic must_cover ['model route record', 'prompt prefix cache profile', 'pricing snapshot', 'eval arm', 'verified fact dependency', 'review ticket'] against `$.normalized_objects`
- deterministic `$.index_records` is_truthy `True`

## Provenance

- Hub component: `pipeline/local-sentence-blueprint-output-records` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, government, finance, humanitarian, cross_industry
- Full source manifest: see `references/manifest.yaml`
