---
name: local-sentence-to-pipeline-demo
description: Convert a user sentence into cheap, balanced, and quality-first pipeline
  blueprints with guardrail and eval registry recommendations.
when_to_use: 'Pipeline kind: meta_build.local_blueprint_demo.'
---

# Local sentence-to-pipeline demo

Runs the downloadable local demo path: turn a plain-language request into costed LLM pipeline options with guardrails, eval kits, A/B cost-quality testing, and deployment bundle placeholders.

## Task

Convert a user sentence into cheap, balanced, and quality-first pipeline blueprints with guardrail and eval registry recommendations.

## Steps

1. **run-local-blueprint** — `tool` → `tool/sentence-to-pipeline-blueprint-runner`
2. **recommend-full-blueprint** — `pipeline` → `pipeline/llm-pipeline-saas-blueprint`
3. **screen-multimodal-safety** — `tool` → `tool/multimodal-safety-screen`
4. **cost-ab-test** — `processor` → `processor/cost-ceiling-gate`

## Defaults

- **knowledge_packs**: `knowledge-pack/local-demo-verified-fact-patterns`, `knowledge-pack/llm-pipeline-saas-blueprints`

## Success criteria

- semantic must_cover ['cheap option', 'balanced option', 'quality-first option', 'guardrails', 'eval kit', 'cost estimate'] against `$.options`
- deterministic `$.deployment_bundle` is_truthy `True`

## Provenance

- Hub component: `pipeline/local-sentence-to-pipeline-demo` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
