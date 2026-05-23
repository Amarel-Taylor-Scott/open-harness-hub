# Nuclear safety review (NRC 10 CFR + IAEA + INPO)

*pipeline* · `pipeline/nuclear-safety-review` · v0.1.0 · experimental

Vertical 27 — nuclear-plant compliance: LCO/LER, scram, physical security, SNM accounting.

| axis | value |
|---|---|
| industry | nuclear, nuclear.power, nuclear.security, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review nuclear plant compliance packet (LCO + LER + scram analysis + physical security + SNM inventory).

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-nuclear-safety-flags` | — |
| 4 | `rag_against_nrc` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

