# Customer Escalation Quality review pipeline

*pipeline* · `pipeline/customer-escalation-quality-review` · v0.1.0 · experimental

End-to-end customer escalation quality review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | customer_success.escalation, retail.support |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review customer escalation handling for response quality, ownership, policy adherence, and recovery plan.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-customer-escalation-quality-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-customer-escalation-quality-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/customer-escalation-quality-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

