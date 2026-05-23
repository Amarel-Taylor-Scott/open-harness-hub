# Personal corpus search pipeline (RAG over user's own data)

*pipeline* · `pipeline/personal-search-pipeline` · v0.1.0 · experimental

Concrete pipeline wrapping `harness/personal-corpus-search` for
answering user queries from their own files / notes / emails /
calendar / contacts. Local-first; opt-in for hosted models.

| axis | value |
|---|---|
| industry | personal_productivity, cross_industry |
| capability | retrieval, reasoning, memory |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Search the user's personal corpus + emit cited answer.

**pipeline_kind:** `rag`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load_prefs` | processor | `processor/preference-loader` | — |
| 2 | `search` | harness | `harness/personal-corpus-search` | — |
| 3 | `leakage_check` | rule_pack | `rule-pack/grep-personal-info-leakage` | — |
| 4 | `audit` | processor | `processor/audit-trace-emitter` | — |

