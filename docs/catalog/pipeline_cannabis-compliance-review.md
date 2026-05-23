# Cannabis compliance review (state + §280E + METRC + FinCEN)

*pipeline* · `pipeline/cannabis-compliance-review` · v0.1.0 · experimental

Vertical 31 — licensed cannabis operator compliance.

| axis | value |
|---|---|
| industry | cannabis, cannabis.cultivation, cannabis.retail, cannabis.testing, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review cannabis operator compliance packet.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-cannabis-compliance-flags` | — |
| 4 | `rag_against_state` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

