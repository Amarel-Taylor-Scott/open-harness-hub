# Deal Desk Discounting review pipeline

*pipeline* · `pipeline/deal-desk-discounting-review` · v0.1.0 · experimental

End-to-end deal desk discounting review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | sales_ops.discounting, legal.contract |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review discount and commercial exception packets for approval authority, margin impact, and precedent risk.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-deal-desk-discounting-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-deal-desk-discounting-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/deal-desk-discounting-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

