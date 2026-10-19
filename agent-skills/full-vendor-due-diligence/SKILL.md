---
name: full-vendor-due-diligence
description: Run a vendor onboarding packet through ESG + AppSec + Legal review in
  one workflow. Surface vertical-level findings + overall verdict.
when_to_use: 'Pipeline kind: compound_review.'
---

# Full vendor due-diligence (ESG + AppSec + Legal — kitchen-sink)

Cross-vertical kitchen-sink pipeline. Accepts a vendor onboarding
packet containing (a) ESG/supply-chain disclosure, (b) representative
code bundle, (c) draft MSA, and runs each through its specialized
grading pipeline. Aggregates the three vertical grades into a
single onboarding verdict + composite success-criteria that
require all three sub-pipelines to pass.

Demonstrates that pipelines can be chained — the `pipeline` step
kind invokes a sub-pipeline with resolved inputs.

## Task

Run a vendor onboarding packet through ESG + AppSec + Legal review
in one workflow. Surface vertical-level findings + overall verdict.

## Steps

1. **esg_review** — `pipeline` → `pipeline/supplier-policy-grading`
2. **appsec_review** — `pipeline` → `pipeline/code-security-review`
3. **legal_review** — `pipeline` → `pipeline/contract-clause-review`
4. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst

## Success criteria

- deterministic `$.steps.esg_review.output.sub_aggregate` is_truthy `None`
- deterministic `$.steps.appsec_review.output.sub_aggregate` is_truthy `None`
- deterministic `$.steps.legal_review.output.sub_aggregate` is_truthy `None`
- composite `OR` over 2 child criteria

## Provenance

- Hub component: `pipeline/full-vendor-due-diligence` v0.1.0
- License: `MIT`
- Industry: cross_industry, compliance, supply_chain, security, legal
- Full source manifest: see `references/manifest.yaml`
