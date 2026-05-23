# Construction safety review (OSHA 1926 / Focus Four)

*pipeline* · `pipeline/construction-safety-review` · v0.1.0 · experimental

Vertical 18.

| axis | value |
|---|---|
| industry | construction, construction.safety |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review a construction-site safety packet (JHA + toolbox talks + inspection notes + near-misses).

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-construction-safety-flags` | — |
| 4 | `rag_against_osha` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

