# Warehouse Safety Inventory review pipeline

*pipeline* · `pipeline/warehouse-safety-inventory-review` · v0.1.0 · experimental

End-to-end warehouse safety inventory review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | logistics, logistics.warehouse |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review warehouse incident and inventory-control packets for safety hazards, shrink, cycle-count gaps, and remediation.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-warehouse-safety-inventory-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-warehouse-safety-inventory-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/warehouse-safety-inventory-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

