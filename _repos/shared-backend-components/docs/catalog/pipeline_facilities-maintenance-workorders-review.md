# Facilities Maintenance Workorders review pipeline

*pipeline* · `pipeline/facilities-maintenance-workorders-review` · v0.1.0 · experimental

End-to-end facilities maintenance workorders review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | facilities.maintenance, infrastructure |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review maintenance work orders for priority, safety impact, preventive maintenance gaps, vendor evidence, and closure quality.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-facilities-maintenance-workorders-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-facilities-maintenance-workorders-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/facilities-maintenance-workorders-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

