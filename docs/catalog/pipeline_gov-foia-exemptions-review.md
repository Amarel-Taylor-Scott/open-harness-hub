# Government FOIA Exemptions review pipeline

*pipeline* · `pipeline/gov-foia-exemptions-review` · v0.1.0 · experimental

End-to-end government foia exemptions review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

| axis | value |
|---|---|
| industry | government, government.foia, privacy |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review public-records release packets for exemption basis, segregability, privacy redaction, and appeal readiness.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-gov-foia-exemptions-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-gov-foia-exemptions-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/gov-foia-exemptions-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

