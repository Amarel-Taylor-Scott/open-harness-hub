# Data Lineage Catalog review pipeline

*pipeline* · `pipeline/data-lineage-catalog-review` · v0.1.0 · experimental

End-to-end data lineage catalog review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | data_governance.lineage, software.devops |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review data catalog entries for ownership, lineage, freshness, classification, and usage context.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-data-lineage-catalog-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-data-lineage-catalog-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/data-lineage-catalog-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

