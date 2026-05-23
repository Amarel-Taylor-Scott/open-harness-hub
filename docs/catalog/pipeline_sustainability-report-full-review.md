# Sustainability report full review (Climate + ESG-S + ESG-G chained)

*pipeline* · `pipeline/sustainability-report-full-review` · v0.1.0 · experimental

Chains 3 sub-pipelines for a comprehensive sustainability-report
audit: climate-disclosure-review + (a subset of) supplier-policy-
grading focused on social + (a subset of) governance. Aggregates
the per-dimension verdicts into a single report grade.

| axis | value |
|---|---|
| industry | climate, esg, compliance, finance |
| capability | evaluation, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Run a corporate sustainability report through climate-disclosure +
ESG-supplier-grading review in one workflow.

**pipeline_kind:** `compound_review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `climate_review` | pipeline | `pipeline/climate-disclosure-review` | — |
| 2 | `esg_review` | pipeline | `pipeline/supplier-policy-grading` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

