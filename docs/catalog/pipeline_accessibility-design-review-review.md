# Accessibility Design Review review pipeline

*pipeline* · `pipeline/accessibility-design-review-review` · v0.1.0 · experimental

End-to-end accessibility design review review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | design_ops, design_ops.accessibility |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review product designs for accessibility risks, inclusive interaction patterns, and remediation evidence.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-accessibility-design-review-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-accessibility-design-review-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/accessibility-design-review-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

