# Legal IP Trademark review pipeline

*pipeline* · `pipeline/legal-ip-trademark-review` · v0.1.0 · experimental

End-to-end legal ip trademark review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

| axis | value |
|---|---|
| industry | legal, legal.ip |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review trademark clearance notes for confusion risk, goods/services proximity, descriptiveness, and evidence gaps.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-legal-ip-trademark-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-legal-ip-trademark-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/legal-ip-trademark-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

