# Expert email and grounded knowledge verification

*pipeline* · `pipeline/expert-email-grounded-knowledge-verification` · v0.1.0 · experimental

Routes high-risk knowledge objects through source governance, grounded search, multi-model verification, consented expert email review, inbound response digestion, dedupe, indexing, and review-ticket routing.

| axis | value |
|---|---|
| industry | ai, government, humanitarian, legal, healthcare, cross_industry |
| capability | verification, retrieval, evaluation, governance, routing |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Verify a high-risk knowledge object using consented expert email review, grounded search, multiple model reviewers, source conflict checks, and indexed review evidence.

**pipeline_kind:** `research_web.verified_knowledge_object_review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-knowledge-object` | tool | `tool/source-record-governance-router` | - |
| 2 | `run-grounded-multimodel-gate` | tool | `tool/grounded-multimodel-verification-gate` | - |
| 3 | `create-expert-review-campaign` | tool | `tool/expert-email-review-campaign-manager` | - |
| 4 | `digest-inbound-review` | tool | `tool/inbound-email-review-digester` | - |
| 5 | `dedupe-evidence` | tool | `tool/fuzzy-dedupe-clusterer` | - |
| 6 | `emit-review-index` | tool | `tool/index-record-emitter` | - |

