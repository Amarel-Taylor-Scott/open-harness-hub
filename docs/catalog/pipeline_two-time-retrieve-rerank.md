# Two-time retrieval + cross-encoder rerank

*pipeline* · `pipeline/two-time-retrieve-rerank` · v0.1.0 · beta

Generic two-pass retrieval pipeline distilled from the EEDI-AWQ
shape. First-pass: retrieve top-K with the raw query. Refine the
query using LLM summary of pass-1. Second-pass: retrieve top-K' with
the refined query. Union, dedupe, cross-encoder rerank. Final
output ranked candidates.

Verified by Open Harness Hub mining of takanashihumbert "EEDI Qwen-2.5
32B AWQ two-time retrieval" (650 votes). The shape generalises to
any RAG task where the user's first query is under-specified.

| axis | value |
|---|---|
| industry | ai, education, scientific_research |
| capability | retrieval, reranking |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



## Task

Two-pass retrieval over a corpus, with LLM-driven query refinement
between passes and cross-encoder rerank at the end.

**pipeline_kind:** `rag`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `two_time` | processor | `processor/two-time-retrieval` | — |
| 2 | `rerank` | processor | `processor/cross-encoder-reranker` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

