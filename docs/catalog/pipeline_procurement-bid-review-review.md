# Procurement Bid Review review pipeline

*pipeline* · `pipeline/procurement-bid-review-review` · v0.1.0 · experimental

End-to-end procurement bid review review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | procurement, procurement.sourcing |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review sourcing packets for bid fairness, evaluation criteria, conflict risk, and award documentation.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-procurement-bid-review-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-procurement-bid-review-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/procurement-bid-review-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

