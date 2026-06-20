# Occupation to procedure primitive index

*pipeline* · `pipeline/occupation-to-procedure-primitive-index` · v0.1.0 · experimental

Convert occupation taxonomies, job descriptions, and role classifications into work atoms, procedure knowledge objects, candidate primitives, and searchable pipeline-building context.

| axis | value |
|---|---|
| industry | ai, hr, education, cross_industry |
| capability | retrieval, extraction, planning, evaluation, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Mine occupation and job-description sources for tasks, questions, facts, tools, evidence requirements, policies, outputs, evals, and candidate AI pipeline primitives.

**pipeline_kind:** `research_web.occupation_work_atom_index_build`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load_occupation_surfaces` | knowledge_pack | `knowledge-pack/occupation-source-surface-map` | - |
| 2 | `lookup_occupation_profiles` | tool | `tool/occupation-taxonomy-source-lookup` | - |
| 3 | `extract_work_atoms` | tool | `tool/job-description-work-atom-extractor` | - |
| 4 | `normalize_as_procedure_objects` | tool | `tool/procedure-object-normalizer` | - |
| 5 | `dedupe_existing_primitives` | tool | `tool/embedding-index-search` | - |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | - |

