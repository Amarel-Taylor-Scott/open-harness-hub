# Full vendor due-diligence (ESG + AppSec + Legal — kitchen-sink)

*pipeline* · `pipeline/full-vendor-due-diligence` · v0.1.0 · experimental

Cross-vertical kitchen-sink pipeline. Accepts a vendor onboarding
packet containing (a) ESG/supply-chain disclosure, (b) representative
code bundle, (c) draft MSA, and runs each through its specialized
grading pipeline. Aggregates the three vertical grades into a
single onboarding verdict + composite success-criteria that
require all three sub-pipelines to pass.

Demonstrates that pipelines can be chained — the `pipeline` step
kind invokes a sub-pipeline with resolved inputs.

| axis | value |
|---|---|
| industry | cross_industry, compliance, supply_chain, security, legal |
| capability | evaluation, verification, reasoning |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Run a vendor onboarding packet through ESG + AppSec + Legal review
in one workflow. Surface vertical-level findings + overall verdict.

**pipeline_kind:** `compound_review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `esg_review` | pipeline | `pipeline/supplier-policy-grading` | — |
| 2 | `appsec_review` | pipeline | `pipeline/code-security-review` | — |
| 3 | `legal_review` | pipeline | `pipeline/contract-clause-review` | — |
| 4 | `audit` | processor | `processor/audit-trace-emitter` | — |

