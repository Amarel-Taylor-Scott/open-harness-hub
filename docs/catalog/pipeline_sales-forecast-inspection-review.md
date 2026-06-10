# Sales Forecast Inspection review pipeline

*pipeline* · `pipeline/sales-forecast-inspection-review` · v0.1.0 · experimental

End-to-end sales forecast inspection review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | sales_ops, sales_ops.forecasting |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review opportunity forecasts for stage hygiene, close-plan quality, risk flags, and commit confidence.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-sales-forecast-inspection-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-sales-forecast-inspection-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/sales-forecast-inspection-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

