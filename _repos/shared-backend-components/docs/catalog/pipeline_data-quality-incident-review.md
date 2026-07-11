# Data Quality Incident review pipeline

*pipeline* · `pipeline/data-quality-incident-review` · v0.1.0 · experimental

End-to-end data quality incident review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | data_governance, data_governance.quality |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review data quality incidents for lineage, blast radius, root cause, remediation, and consumer communication.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-data-quality-incident-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-data-quality-incident-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/data-quality-incident-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

