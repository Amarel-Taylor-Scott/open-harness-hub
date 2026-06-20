# ESG single-pillar (E / S / G) deep-dive disclosure review

*pipeline* · `pipeline/esg-pillar-deep-dive` · v0.1.0 · experimental

End-to-end pipeline reviewing ONE ESG pillar (Environmental,
Social, or Governance) of a sustainability disclosure at SASB-
industry + ISSB + TCFD + GRI depth, with greenwashing-pattern
scan and framework-coded findings.

Complements:
 - `pipeline/supplier-policy-grading` — regulatory enforcement
   (CSDDD/UFLPA E+S+G grading)
 - `pipeline/esg-disclosure-grading` (via harness/esg-disclosure-
   grading) — combined ESG voluntary disclosure grading

This pipeline is for going DEEP on ONE pillar at a time —
appropriate when an analyst, investor, or auditor wants pillar-
level detail rather than a roll-up.

Outputs:
 - per-topic disclosure status (disclosed / incomplete / not-
   material / missing) with SASB/ISSB/GRI/TCFD code citations
 - greenwashing-flag list with severity
 - double-materiality coverage table
 - target rigour assessment (SBTi check for climate)
 - assurance level + auditor
 - rubric score (rubric/esg-pillar-depth-v1)

| axis | value |
|---|---|
| industry | esg, esg.csrd, sustainability, climate, compliance |
| capability | evaluation, extraction, verification |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given a sustainability disclosure and a target pillar (E, S, or G),
produce a SASB-industry-specific, ISSB/GRI/TCFD-aligned, framework-
coded review with greenwashing-pattern scan and a rubric grade
against `rubric/esg-pillar-depth-v1`.

**pipeline_kind:** `grading`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `normalize` | processor | `processor/structured-to-prose` | - |
| 2 | `grep_greenwashing` | rule_pack | `rule-pack/grep-greenwashing-flags` | - |
| 3 | `rag_esg_frameworks` | rule_pack | `rule-pack/hybrid-retrieval-policy` | - |
| 4 | `review` | harness | `harness/esg-pillar-review` | - |
| 5 | `grade` | processor | `processor/llm-judge` | - |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | - |

