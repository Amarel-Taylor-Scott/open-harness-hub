# Workplace Safety Incident review pipeline

*pipeline* · `pipeline/workplace-safety-incident-review` · v0.1.0 · experimental

End-to-end workplace safety incident review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | facilities, facilities.workplace_safety, ehs.audit |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review workplace incident packets for hazard correction, injury response, witness evidence, and recurrence controls.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-workplace-safety-incident-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-workplace-safety-incident-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/workplace-safety-incident-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

