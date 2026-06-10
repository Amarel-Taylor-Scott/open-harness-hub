# Vehicle Safety Defect review pipeline

*pipeline* · `pipeline/vehicle-safety-defect-review` · v0.1.0 · experimental

End-to-end vehicle safety defect review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | automotive, automotive.safety |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review vehicle incident and complaint packets for potential safety defect signals and escalation evidence.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-vehicle-safety-defect-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-vehicle-safety-defect-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/vehicle-safety-defect-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

