# STORM: persona-curation + outline-fanout article

*pipeline* · `pipeline/storm-persona-curation-article` · v0.1.0 · experimental

Stanford OVAL's STORM pattern. Generate N personas with different
perspectives → run simulated dialogue per persona to curate
knowledge → outline → parallel-expand each outline section →
polish into final article.

Verified by Open Harness Hub clone: `stanford-oval/storm` —
`knowledge_storm/storm_wiki/modules/{persona_generator,knowledge_curation,outline_generation,article_generation,article_polish}.py`.

| axis | value |
|---|---|
| industry | ai, media, education |
| capability | research, generation, summarization |
| modality | text |
| lifecycle | experimental |
| trust_boundary | external |
| license | MIT |



## Task

Given a research topic, produce a Wikipedia-style article with
multi-perspective knowledge curation, outlined sections expanded in
parallel, and a final polish pass.

**pipeline_kind:** `writing_long_form`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `redact_topic` | harness | `harness/redact-pii-text` | — |
| 2 | `generate_personas` | processor | `processor/persona-set-generator` | — |
| 3 | `curate_knowledge` | harness | `harness/text-safety-review` | — |
| 4 | `outline` | processor | `processor/skeleton-outliner` | — |
| 5 | `expand_sections` | harness | `harness/text-safety-review` | — |
| 6 | `polish` | processor | `processor/self-refine-critique` | — |
| 7 | `verify_citations` | processor | `processor/citation-coverage` | — |

