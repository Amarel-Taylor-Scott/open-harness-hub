# Flexible hierarchy label extension

*pipeline* · `pipeline/flexible-hierarchy-label-extension` · v0.1.0 · experimental

Assigns vertical, jurisdiction, workflow, risk, and deployment labels as flexible records so new domains do not require constant core vocabulary changes.

| axis | value |
|---|---|
| industry | ai, software.devops, energy, healthcare, legal, cross_industry |
| capability | classification, retrieval, routing, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | stable |
| license | MIT |



## Task

Apply flexible hierarchical labels and dimensions to subjects without expanding core capability or modality vocabularies.

**pipeline_kind:** `research_web.flexible_hierarchy_label_extension`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `assign-labels-and-dimensions` | tool | `tool/hierarchical-label-dimensioner` | - |
| 2 | `dedupe-label-records` | tool | `tool/fuzzy-dedupe-clusterer` | - |
| 3 | `emit-label-index` | tool | `tool/index-record-emitter` | - |

