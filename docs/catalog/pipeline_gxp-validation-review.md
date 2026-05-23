# GxP validation review (21-CFR-11 + Annex 11 + ALCOA+)

*pipeline* · `pipeline/gxp-validation-review` · v0.1.0 · experimental

Review a GxP-validated electronic-records system against the
rubric. Same 6-step chain as ESG / radiology / legal / AppSec —
fifth vertical proving the architecture's industry-agnosticism.

| axis | value |
|---|---|
| industry | pharma, pharma.gxp, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given a GxP system validation packet (system description + IQ/OQ/PQ
outputs + audit-trail samples + user-access reviews + change-
control history), grade against the rubric + cite the relevant
regulation section for each finding.

**pipeline_kind:** `grading`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_phi` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_phi` | rule_pack | `rule-pack/phi-hipaa-en` | — |
| 4 | `grep_gxp_red_flags` | rule_pack | `rule-pack/grep-gxp-data-integrity-red-flags` | — |
| 5 | `rag_against_cfr_11` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 6 | `grade` | processor | `processor/llm-judge` | — |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | — |

