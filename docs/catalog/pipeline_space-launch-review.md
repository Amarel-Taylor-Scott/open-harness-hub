# Space launch + range safety review (FAA Part 450 / NASA / ITAR)

*pipeline* · `pipeline/space-launch-review` · v0.1.0 · experimental

Vertical 30 — commercial space launch compliance: FSA / Ec / FTS / ITAR / 25-yr disposal / MPL.

| axis | value |
|---|---|
| industry | space, space.launch, space.export_control, space.orbital, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review commercial space launch readiness packet.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-space-launch-flags` | — |
| 4 | `rag_against_faa` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

