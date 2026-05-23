# Climate disclosure review (TCFD + ISSB IFRS S2 + ESRS E1)

*pipeline* · `pipeline/climate-disclosure-review` · v0.1.0 · experimental

Grade a corporate climate disclosure against the rubric.
Sixth vertical proving the architecture's industry-agnosticism.
Same 6-step chain: prose → PII redact → GREP → RAG → judge → audit.

| axis | value |
|---|---|
| industry | climate, esg, finance, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given a corporate climate disclosure (10-K climate section, CDP
response, sustainability report excerpt), grade against the
rubric + cite TCFD recommendation / ISSB paragraph / ESRS
standard for each finding.

**pipeline_kind:** `grading`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_climate_gaps` | rule_pack | `rule-pack/grep-climate-disclosure-gaps` | — |
| 4 | `rag_against_frameworks` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

