# RCRA hazardous waste review (40 CFR 260-279 + e-Manifest + DOT HMR)

*pipeline* · `pipeline/rcra-waste-review` · v0.1.0 · experimental

Vertical 34 — LQG/SQG/TSDF + Universal Waste compliance.

| axis | value |
|---|---|
| industry | waste, waste.rcra_tsdf, waste.generator, waste.universal, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review RCRA hazardous waste generator / TSDF compliance packet.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-rcra-waste-flags` | — |
| 4 | `rag_against_rcra` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

