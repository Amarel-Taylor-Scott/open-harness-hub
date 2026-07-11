# Education Accommodations review pipeline

*pipeline* · `pipeline/education-accommodations-review` · v0.1.0 · experimental

End-to-end education accommodations review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

| axis | value |
|---|---|
| industry | education, education.higher, education.k12 |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review student accommodation packets for documented need, accessibility fit, privacy handling, and implementation accountability.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-education-accommodations-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-education-accommodations-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/education-accommodations-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

