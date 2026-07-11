# Auto Warranty Triage review pipeline

*pipeline* · `pipeline/auto-warranty-triage-review` · v0.1.0 · experimental

End-to-end auto warranty triage review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | automotive, automotive.warranty |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review warranty claims for coverage, repeat repair, field-quality signal, and fraud/evidence gaps.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-auto-warranty-triage-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-auto-warranty-triage-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/auto-warranty-triage-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

