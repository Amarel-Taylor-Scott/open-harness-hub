# Candidate primitive promotion scoring

*pipeline* · `pipeline/candidate-primitive-promotion-scoring` · v0.1.0 · experimental

Score normalized candidate primitives for promotion readiness and route them to promotion, review, hold, or reject queues with quality index records.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | evaluation, governance, planning, routing, retrieval |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Score candidate primitives using usefulness, demand, complexity, time savings, deployment frequency, capability gap, cost savings, deployment value, model-swap value, privacy risk, license risk, and dedupe risk.

**pipeline_kind:** `research_web.candidate_primitive_promotion_scoring`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load_promotion_patterns` | knowledge_pack | `knowledge-pack/candidate-primitive-promotion-patterns` | - |
| 2 | `score_candidates` | tool | `tool/candidate-primitive-promotion-scorer` | - |
| 3 | `emit_quality_index` | tool | `tool/index-record-emitter` | - |
| 4 | `route_review` | processor | `processor/audit-trace-emitter` | - |

