# Multi-document QA with sub-question decomposition

*pipeline* · `pipeline/multi-doc-qa-subquestion` · v0.1.0 · experimental

LlamaIndex's SubQuestionQueryEngine pattern in pipeline form. The user
asks a compound question; an LLM decomposes it into sub-questions;
each sub-question runs its own retrieval; per-sub-question answers
are aggregated with citations. Strong for "compare X across N docs"
questions where naive RAG fails.

Chain: persona → grep (input guard) → decompose → per-sub-Q retrieve
→ per-sub-Q answer → aggregate-cite → output verify.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | retrieval, reasoning, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Decompose a compound question into N sub-questions, run independent
retrieval per sub-question, generate per-sub-question answers, and
aggregate into a single cited synthesis.

**pipeline_kind:** `qa_documents`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard_question` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `decompose` | harness | `harness/text-safety-review` | — |
| 3 | `retrieve_per_subquestion` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 4 | `rerank_per_subquestion` | processor | `processor/cross-encoder-reranker` | — |
| 5 | `answer_per_subquestion` | harness | `harness/text-safety-review` | — |
| 6 | `aggregate` | harness | `harness/text-safety-review` | — |
| 7 | `verify_citation_coverage` | processor | `processor/citation-coverage` | — |

