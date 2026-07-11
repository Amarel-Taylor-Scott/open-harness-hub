---
name: recursive-encoded-payload-triage
description: Decide whether a prompt or tool request containing possible encoded spans
  can be safely routed to an edge AI model.
when_to_use: 'Pipeline kind: edge_ai.recursive_encoded_payload_triage.'
---

# Recursive encoded payload triage

Pre-LLM guardrail pipeline that recursively sanitizes encoded spans, routes checks through an edge micro-model, and escalates uncertain or high-risk decoded content.

## Task

Decide whether a prompt or tool request containing possible encoded spans can be safely routed to an edge AI model.

## Steps

1. **sanitize-encoded-spans** — `tool` → `tool/recursive-encoding-sanitizer`
2. **route-edge-authorization** — `tool` → `tool/edge-micro-model-authorization-router`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/edge-ai-semantic-gap-guardrail-patterns`

## Success criteria

- rubric `rubric/edge-ai-guardrail-quality-v1` threshold 0.8

## Provenance

- Hub component: `pipeline/recursive-encoded-payload-triage` v0.1.0
- License: `MIT`
- Industry: ai, security.defensive, media, cross_industry
- Full source manifest: see `references/manifest.yaml`
