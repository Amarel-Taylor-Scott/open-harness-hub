# Water utility compliance review (SDWA / NPDWR / LCRR / AWIA)

*pipeline* · `pipeline/water-utility-compliance-review` · v0.1.0 · experimental

Vertical 24 — drinking-water utility compliance + cyber.

| axis | value |
|---|---|
| industry | water_utility, water_utility.sdwa, water_utility.lcr, water_utility.scada, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review Public Water System compliance packet (operations + monitoring + LSL inventory + RRA/ERP + SCADA cyber).

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-water-utility-flags` | — |
| 4 | `rag_against_sdwa` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

