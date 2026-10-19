---
name: expert-email-grounded-knowledge-verification
description: Verify a high-risk knowledge object using consented expert email review,
  grounded search, multiple model reviewers, source conflict checks, and indexed review
  evidence.
when_to_use: 'Pipeline kind: research_web.verified_knowledge_object_review.'
---

# Expert email and grounded knowledge verification

Routes high-risk knowledge objects through source governance, grounded search, multi-model verification, consented expert email review, inbound response digestion, dedupe, indexing, and review-ticket routing.

## Task

Verify a high-risk knowledge object using consented expert email review, grounded search, multiple model reviewers, source conflict checks, and indexed review evidence.

## Steps

1. **govern-knowledge-object** — `tool` → `tool/source-record-governance-router`
2. **run-grounded-multimodel-gate** — `tool` → `tool/grounded-multimodel-verification-gate`
3. **create-expert-review-campaign** — `tool` → `tool/expert-email-review-campaign-manager`
4. **digest-inbound-review** — `tool` → `tool/inbound-email-review-digester`
5. **dedupe-evidence** — `tool` → `tool/fuzzy-dedupe-clusterer`
6. **emit-review-index** — `tool` → `tool/index-record-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/expert-email-grounded-verification-patterns`

## Success criteria

- semantic must_cover ['grounded search', 'multiple model reviewers', 'expert email review', 'source conflicts', 'review tickets'] against `$.verification_packet`
- deterministic `$.review_tickets` is_truthy `True`

## Provenance

- Hub component: `pipeline/expert-email-grounded-knowledge-verification` v0.1.0
- License: `MIT`
- Industry: ai, government, humanitarian, legal, healthcare, cross_industry
- Full source manifest: see `references/manifest.yaml`
