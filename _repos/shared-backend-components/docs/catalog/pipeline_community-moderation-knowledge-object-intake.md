# Community moderation knowledge object intake

*pipeline* · `pipeline/community-moderation-knowledge-object-intake` · v0.1.0 · experimental

Turns social media and group moderation policies, rules, appeals, escalation triggers, and transparency requirements into governed candidate knowledge objects.

| axis | value |
|---|---|
| industry | media, retail, security, cross_industry |
| capability | classification, routing, governance, evaluation, retrieval |
| modality | text, image, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Normalize community moderation source material into candidate knowledge objects with governance, entity linking, dedupe, index records, and high-risk review routing.

**pipeline_kind:** `research_web.community_moderation_knowledge_object_intake`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-moderation-sources` | tool | `tool/source-record-governance-router` | - |
| 2 | `normalize-moderation-objects` | tool | `tool/community-moderation-object-normalizer` | - |
| 3 | `link-moderation-entities` | tool | `tool/entity-recognition-linker` | - |
| 4 | `dedupe-moderation-objects` | tool | `tool/fuzzy-dedupe-clusterer` | - |
| 5 | `emit-moderation-index-records` | tool | `tool/index-record-emitter` | - |

