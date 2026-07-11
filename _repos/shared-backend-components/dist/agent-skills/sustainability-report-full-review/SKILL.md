---
name: sustainability-report-full-review
description: Run a corporate sustainability report through climate-disclosure + ESG-supplier-grading
  review in one workflow.
when_to_use: 'Pipeline kind: compound_review.'
---

# Sustainability report full review (Climate + ESG-S + ESG-G chained)

Chains 3 sub-pipelines for a comprehensive sustainability-report
audit: climate-disclosure-review + (a subset of) supplier-policy-
grading focused on social + (a subset of) governance. Aggregates
the per-dimension verdicts into a single report grade.

## Task

Run a corporate sustainability report through climate-disclosure +
ESG-supplier-grading review in one workflow.

## Steps

1. **climate_review** — `pipeline` → `pipeline/climate-disclosure-review`
2. **esg_review** — `pipeline` → `pipeline/supplier-policy-grading`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/climate-risk-analyst

## Success criteria

- deterministic `$.steps.climate_review.output.sub_aggregate` is_truthy `None`
- deterministic `$.steps.esg_review.output.sub_aggregate` is_truthy `None`

## Provenance

- Hub component: `pipeline/sustainability-report-full-review` v0.1.0
- License: `MIT`
- Industry: climate, esg, compliance, finance
- Full source manifest: see `references/manifest.yaml`
