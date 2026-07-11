# Cold Chain Excursion review pipeline

*pipeline* · `pipeline/cold-chain-excursion-review` · v0.1.0 · experimental

End-to-end cold chain excursion review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | logistics.cold_chain, food.safety |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review temperature excursion packets for product disposition, custody evidence, and corrective action.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-cold-chain-excursion-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-cold-chain-excursion-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/cold-chain-excursion-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

