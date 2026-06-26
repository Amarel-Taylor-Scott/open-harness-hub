---
name: community-moderation-knowledge-object-intake
description: Normalize community moderation source material into candidate knowledge
  objects with governance, entity linking, dedupe, index records, and high-risk review
  routing.
when_to_use: 'Pipeline kind: research_web.community_moderation_knowledge_object_intake.'
---

# Community moderation knowledge object intake

Turns social media and group moderation policies, rules, appeals, escalation triggers, and transparency requirements into governed candidate knowledge objects.

## Task

Normalize community moderation source material into candidate knowledge objects with governance, entity linking, dedupe, index records, and high-risk review routing.

## Steps

1. **govern-moderation-sources** — `tool` → `tool/source-record-governance-router`
2. **normalize-moderation-objects** — `tool` → `tool/community-moderation-object-normalizer`
3. **link-moderation-entities** — `tool` → `tool/entity-recognition-linker`
4. **dedupe-moderation-objects** — `tool` → `tool/fuzzy-dedupe-clusterer`
5. **emit-moderation-index-records** — `tool` → `tool/index-record-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/community-moderation-knowledge-objects`

## Success criteria

- semantic must_cover ['community rule', 'moderator checklist', 'escalation trigger', 'appeal review', 'transparency log'] against `$.normalized_objects`

## Provenance

- Hub component: `pipeline/community-moderation-knowledge-object-intake` v0.1.0
- License: `MIT`
- Industry: media, retail, security, cross_industry
- Full source manifest: see `references/manifest.yaml`
