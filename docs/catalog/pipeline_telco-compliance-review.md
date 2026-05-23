# Telco compliance review (FCC + CPNI + CALEA + STIR/SHAKEN)

*pipeline* · `pipeline/telco-compliance-review` · v0.1.0 · experimental

Vertical 25 — telecom-carrier compliance: CPNI breach, NORS outages, STIR/SHAKEN, CALEA, E911.

| axis | value |
|---|---|
| industry | telecommunications, telecommunications.fcc, telecommunications.cpni, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review telecom carrier compliance packet (CPNI handling + NORS outages + STIR/SHAKEN + CALEA + E911).

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-telco-compliance-flags` | — |
| 4 | `rag_against_fcc` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

