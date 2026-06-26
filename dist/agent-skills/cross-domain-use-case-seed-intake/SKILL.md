---
name: cross-domain-use-case-seed-intake
description: Convert broad use-case seed surfaces into normalized candidate primitives
  with governance, entity linking, dedupe, indexing, and review routing.
when_to_use: 'Pipeline kind: research_web.cross_domain_use_case_seed_intake.'
---

# Cross-domain use case seed intake

Normalizes banking-law, jurisdictional-law, moderation, creative, brainstorming, competition-analysis, and geographic-analysis seeds into candidate primitives while excluding insurance scope.

## Task

Convert broad use-case seed surfaces into normalized candidate primitives with governance, entity linking, dedupe, indexing, and review routing.

## Steps

1. **govern-use-case-seed** — `tool` → `tool/source-record-governance-router`
2. **normalize-seed** — `tool` → `tool/use-case-seed-normalizer`
3. **link-seed-entities** — `tool` → `tool/entity-recognition-linker`
4. **dedupe-seed** — `tool` → `tool/fuzzy-dedupe-clusterer`
5. **emit-seed-index** — `tool` → `tool/index-record-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/cross-domain-use-case-seeds`

## Success criteria

- semantic must_cover ['domain', 'risk tier', 'excluded scope', 'candidate primitive'] against `$.normalized_object`
- deterministic `$.index_records` is_truthy `True`

## Provenance

- Hub component: `pipeline/cross-domain-use-case-seed-intake` v0.1.0
- License: `MIT`
- Industry: finance, legal, media, creative, government, cross_industry
- Full source manifest: see `references/manifest.yaml`
