# Customer Renewal Risk review pipeline

*pipeline* · `pipeline/customer-renewal-risk-review` · v0.1.0 · experimental

End-to-end customer renewal risk review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | customer_success, customer_success.renewal |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review account packets for renewal risk, value realization, adoption gaps, and escalation actions.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-customer-renewal-risk-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-customer-renewal-risk-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/customer-renewal-risk-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

