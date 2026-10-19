---
name: showcase-candidate-coverage-audit
description: Audit whether generated showcase pipelines have enough staged component
  candidates to become credible off-the-shelf product templates.
when_to_use: 'Pipeline kind: research_web.showcase_candidate_coverage_audit.'
---

# Showcase candidate coverage audit

Compares daily showcase pipeline templates with staged component candidates and emits missing-component generation requests for weak template steps.

## Task

Audit whether generated showcase pipelines have enough staged component candidates to become credible off-the-shelf product templates.

## Steps

1. **load-coverage-checks** — `knowledge_pack` → `knowledge-pack/showcase-candidate-coverage-patterns`
2. **score-showcase-coverage** — `tool` → `tool/showcase-candidate-coverage-reporter`

## Defaults

- **knowledge_packs**: `knowledge-pack/showcase-candidate-coverage-patterns`

## Success criteria

- deterministic `$.score-showcase-coverage.template_count` >= `5`
- deterministic `$.score-showcase-coverage.candidate_count` >= `1000`
- semantic must_cover ['covered', 'partial', 'missing', 'generation requests', 'no promotion side effect'] against `$.score-showcase-coverage`

## Provenance

- Hub component: `pipeline/showcase-candidate-coverage-audit` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
