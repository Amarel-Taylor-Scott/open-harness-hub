---
name: platform-content-triage
description: Triage a piece of user-generated content into allow / restrict / remove
  / escalate.
when_to_use: 'Pipeline kind: review.'
---

# Platform content triage (Trust + Safety)

Review user-generated content against a documented platform policy. Detects illicit + harmful patterns, routes CSAM suspicion to the human queue + NCMEC referral packet without model classification, generates DSA Art 17 statement of reasons for every restriction.

## Task

Triage a piece of user-generated content into allow / restrict / remove / escalate.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_triage** — `rule_pack` → `rule-pack/grep-platform-moderation-flags`
4. **rag_policy** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **judge** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/trust-and-safety-reviewer
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-platform-moderation-flags`
- **knowledge_packs**: `knowledge-pack/platform-content-policy-frameworks`

## Success criteria

- rubric `rubric/platform-moderation-quality-v1` threshold 0.7

## Provenance

- Hub component: `pipeline/platform-content-triage` v0.1.0
- License: `MIT`
- Industry: compliance, media, privacy
- Full source manifest: see `references/manifest.yaml`
