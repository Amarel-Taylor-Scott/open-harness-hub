# Maritime safety review (IMO SOLAS / MARPOL / ISM / STCW)

*pipeline* · `pipeline/maritime-safety-review` · v0.1.0 · experimental

Vertical 20.

| axis | value |
|---|---|
| industry | maritime, maritime.safety |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review vessel inspection / PSC / ISM audit packet.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-maritime-safety-flags` | — |
| 4 | `rag_against_imo` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

