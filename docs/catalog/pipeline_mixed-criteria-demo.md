# Mixed success-criteria demo (regex + semantic + deterministic + LLM + composite)

*pipeline* · `pipeline/mixed-criteria-demo` · v0.1.0 · experimental

Demonstrates `pattern/composable-success-criteria`. The pipeline
runs the contract-clause-review chain, then evaluates its output
against EVERY criterion kind:

 - regex:         output text contains "indemnif" (sanity check)
 - semantic:      output covers ("uncapped indemnity", "DPA")
 - deterministic: output.fired count >= 5
 - llm_judge:     judge contract via rubric, score >= 0.5
 - composite:     (PHI-redact-fired AND no-critical) OR
                 (critical-found AND remediation-proposed)

Each criterion emits its own pass/fail record. The aggregate is
reported alongside the per-criterion breakdown.

| axis | value |
|---|---|
| industry | cross_industry, compliance, legal |
| capability | verification, evaluation |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Run contract review + evaluate 5 mixed-kind success criteria.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-contract-red-flags` | — |
| 4 | `grade` | processor | `processor/llm-judge` | — |

