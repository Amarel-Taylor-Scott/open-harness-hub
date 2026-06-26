---
name: saas-launch-critique
description: Given a SaaS product's landing-page copy, tagline, pricing copy, demo
  URL, and product category, produce a per-aspect launch- readiness review with anti-pattern
  flags, suggested rewrites, and a rubric grade against `rubric/saas-launch-quality-v1`.
when_to_use: 'Pipeline kind: grading.'
---

# SaaS / micro-SaaS / AI-app launch critique

End-to-end pipeline that reviews a SaaS product launch (landing
page + tagline + pricing + demo materials + GTM claims) against
corpus-norm anti-patterns and the saas-launch-quality-v1 rubric.

Use cases:
 - Pre-Product-Hunt launch readiness review
 - Pre-Show-HN sanity check
 - "Why isn't my landing page converting" diagnostic
 - Investor pitch landing-page review
 - Periodic re-review of a live SaaS landing page

Output:
 - per-aspect findings (tagline, ICP, value-prop, pricing, social
   proof, demo, competitive, onboarding, AI-specific)
 - severity per finding + launch-day-blocker flag
 - suggested rewrite per finding
 - anti-pattern hit list
 - rubric score (rubric/saas-launch-quality-v1)

## Task

Given a SaaS product's landing-page copy, tagline, pricing copy,
demo URL, and product category, produce a per-aspect launch-
readiness review with anti-pattern flags, suggested rewrites, and
a rubric grade against `rubric/saas-launch-quality-v1`.

## Steps

1. **normalize** — `processor` → `processor/structured-to-prose`
2. **grep_antipatterns** — `rule_pack` → `rule-pack/grep-saas-launch-antipatterns`
3. **rag_playbook** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
4. **review** — `harness` → `harness/saas-launch-review`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/saas-launch-critic
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-saas-launch-antipatterns`

## Success criteria

- rubric `rubric/saas-launch-quality-v1` threshold 0.7

## Provenance

- Hub component: `pipeline/saas-launch-critique` v0.1.0
- License: `MIT`
- Industry: software, creative, cross_industry
- Full source manifest: see `references/manifest.yaml`
