# Theory to component candidates

*pipeline* · `pipeline/theory-to-component-candidates` · v0.1.0 · experimental

Converts technical theories and postmortems into staged, database-backed component candidates that can be deduped, indexed, reviewed, embedded, and promoted.

| axis | value |
|---|---|
| industry | ai, software.devops, security.defensive, cross_industry |
| capability | generation, planning, governance, retrieval |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Turn a set of theory seeds into staged component candidate row families.

**pipeline_kind:** `research_web.theory_to_component_candidates`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `expand-theory-seeds` | tool | `tool/theory-component-seed-generator` | - |
| 2 | `audit-staged-rows` | tool | `tool/staged-vs-committed-load-auditor` | - |
| 3 | `emit-audit` | processor | `processor/audit-trace-emitter` | - |

