# Commercial contract clause review (cite-first redlining)

*pipeline* · `pipeline/contract-clause-review` · v0.1.0 · experimental

Review a commercial contract against `rubric/contract-review-quality-
v1`. Reuses the SAME primitives as the ESG + radiology grading
pipelines: structured-to-prose → PII redact → GREP → RAG → judge →
audit. Only persona / rule pack / knowledge pack / rubric change.

Third proof point of the architecture's industry-agnosticism:
ESG (CSDDD) + Healthcare (RADS/Fleischner) + Legal (contract
clauses) all share the same chain.

| axis | value |
|---|---|
| industry | legal, legal.contract, legal.compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given a commercial contract (NDA / MSA / SOW / DPA / vendor /
employment), surface red-flag clauses, propose redlines, cite the
playbook entry that grounds each finding, score against the
rubric.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-contract-red-flags` | — |
| 4 | `rag_against_clause_library` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

