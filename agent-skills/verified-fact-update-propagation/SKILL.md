---
name: verified-fact-update-propagation
description: Propagate vetted source-of-truth updates such as government rule changes
  into dependent Open Harness Hub pipelines and indexes.
when_to_use: 'Pipeline kind: research_web.verified_fact_update.'
---

# Verified fact update propagation

Ingests a signed verified fact update from a vetted publisher, updates source-governed knowledge records, finds dependent pipelines, emits review tickets, and prepares re-index or redeployment plans.

## Task

Propagate vetted source-of-truth updates such as government rule changes into dependent Open Harness Hub pipelines and indexes.

## Steps

1. **verify-publisher-submission** — `tool` → `tool/verified-source-publisher-intake`
2. **signed-object-intake** — `tool` → `tool/signed-knowledge-object-intake`
3. **index-signed-knowledge** — `pipeline` → `pipeline/signed-knowledge-object-to-index`
4. **propagate-impact** — `tool` → `tool/verified-fact-impact-propagator`
5. **emit-index-delta** — `tool` → `tool/index-record-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/local-demo-verified-fact-patterns`, `knowledge-pack/signed-knowledge-network-patterns`

## Success criteria

- deterministic `$.affected_components` != `None`
- deterministic `$.review_tickets` != `None`

## Provenance

- Hub component: `pipeline/verified-fact-update-propagation` v0.1.0
- License: `MIT`
- Industry: ai, government, legal, cross_industry
- Full source manifest: see `references/manifest.yaml`
