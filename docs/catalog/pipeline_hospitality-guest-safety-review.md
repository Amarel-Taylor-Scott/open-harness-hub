# Hospitality Guest Safety review pipeline

*pipeline* · `pipeline/hospitality-guest-safety-review` · v0.1.0 · experimental

End-to-end hospitality guest safety review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

| axis | value |
|---|---|
| industry | hospitality |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review hospitality incident packets for guest safety, duty-of-care evidence, escalation, and remediation tracking.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-hospitality-guest-safety-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-hospitality-guest-safety-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/hospitality-guest-safety-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

