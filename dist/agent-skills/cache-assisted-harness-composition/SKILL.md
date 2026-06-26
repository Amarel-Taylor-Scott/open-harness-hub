---
name: cache-assisted-harness-composition
description: Retrieve and verify reusable trajectory fragments so recurring harness
  and pipeline subproblems can be served with less model inference.
when_to_use: 'Pipeline kind: agent_loop.'
---

# Cache-assisted harness composition

Uses the OpenHubForAI object database as a trajectory-fragment cache: extract solved fragments, retrieve similar subproblems, compose candidates cheaply, verify them, and fall back to stronger models when needed.

## Task

Retrieve and verify reusable trajectory fragments so recurring harness and pipeline subproblems can be served with less model inference.

## Steps

1. **extract-fragments** — `tool` → `tool/trajectory-fragment-extractor`
2. **retrieve-fragments** — `tool` → `tool/fragment-cache-retriever`
3. **route-model** — `tool` → `tool/model-capability-router`
4. **stitch-and-verify** — `tool` → `tool/cache-stitch-verify-composer`
5. **emit-index** — `tool` → `tool/index-record-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/trajectory-fragment-cache-patterns`

## Success criteria

- semantic must_cover ['retrieved fragments', 'cheap composition', 'verification', 'fallback model', 'privacy boundary'] against `$.composition`
- deterministic `$.cache_reuse_event` is_truthy `True`

## Provenance

- Hub component: `pipeline/cache-assisted-harness-composition` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
