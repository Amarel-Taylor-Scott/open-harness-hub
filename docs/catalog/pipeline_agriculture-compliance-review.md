# Agriculture compliance review (FSMA + USDA NOP + GlobalGAP)

*pipeline* · `pipeline/agriculture-compliance-review` · v0.1.0 · experimental

Vertical 28 — farm + packing-house compliance: FSMA water, pesticide REI/PHI/MRL, organic, child labor.

| axis | value |
|---|---|
| industry | agriculture_compliance, agriculture_compliance.fsma, agriculture_compliance.organic, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review agriculture compliance packet (pesticide application + water quality + organic OSP + worker H+S).

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-agriculture-compliance-flags` | — |
| 4 | `rag_against_fsma` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

