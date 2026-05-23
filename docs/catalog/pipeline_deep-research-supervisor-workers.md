# Deep research: supervisor + parallel workers

*pipeline* · `pipeline/deep-research-supervisor-workers` · v0.1.0 · experimental

LangChain's open_deep_research pattern. A supervisor LLM decomposes
the user query into research briefs and dispatches N parallel
researcher subagents (each gets its own context + tools), then
compresses and writes the final report.

Verified by Open Harness Hub clone:
`langchain-ai/open_deep_research/src/open_deep_research/deep_researcher.py`
(~700 LOC) + `prompts.py`.

| axis | value |
|---|---|
| industry | ai, media, cross_industry |
| capability | research, retrieval, reasoning |
| modality | text |
| lifecycle | experimental |
| trust_boundary | external |
| license | MIT |



## Task

Given a research query, dispatch parallel research workers each
scoped to a sub-topic, compress their findings, write a synthesized
report with citations.

**pipeline_kind:** `research_web`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `redact_query` | harness | `harness/redact-pii-text` | — |
| 2 | `clarify` | harness | `harness/text-safety-review` | — |
| 3 | `brief_writer` | harness | `harness/text-safety-review` | — |
| 4 | `decompose_to_workers` | processor | `processor/sub-question-decomposer` | — |
| 5 | `dispatch_workers` | harness | `harness/text-safety-review` | — |
| 6 | `compress_notes` | processor | `processor/llmlingua-context-compressor` | — |
| 7 | `write_report` | harness | `harness/text-safety-review` | — |
| 8 | `verify_citations` | processor | `processor/citation-coverage` | — |

