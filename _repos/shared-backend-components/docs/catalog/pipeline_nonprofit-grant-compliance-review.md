# Nonprofit Grant Compliance review pipeline

*pipeline* · `pipeline/nonprofit-grant-compliance-review` · v0.1.0 · experimental

End-to-end nonprofit grant compliance review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

| axis | value |
|---|---|
| industry | nonprofit |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review nonprofit grant files for allowable costs, subrecipient monitoring, reporting deadlines, and restricted-fund controls.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-nonprofit-grant-compliance-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-nonprofit-grant-compliance-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/nonprofit-grant-compliance-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

