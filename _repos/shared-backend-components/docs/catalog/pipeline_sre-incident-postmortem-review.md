# SRE Incident Postmortem review pipeline

*pipeline* · `pipeline/sre-incident-postmortem-review` · v0.1.0 · experimental

End-to-end sre incident postmortem review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

| axis | value |
|---|---|
| industry | sre, sre.oncall, software.devops |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review incident postmortems for timeline accuracy, impact quantification, root cause, corrective actions, and recurrence controls.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-sre-incident-postmortem-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-sre-incident-postmortem-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/sre-incident-postmortem-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

