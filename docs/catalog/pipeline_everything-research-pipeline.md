# Everything research pipeline (kitchen-sink, 22 passes)

*pipeline* · `pipeline/everything-research-pipeline` · v0.1.0 · experimental

A comprehensive research pipeline that demonstrates every layer the
hub supports — 22 distinct passes from raw input through model call
through iterative refinement to delivery.

This is the reference shape for "production-grade" RAG-with-everything:
pre-API the prompt goes through PII redact, prompt-injection guard,
abbreviation expansion, intent classification, query decomposition,
multi-query expansion, allowlist sanitization, hybrid retrieval,
cross-encoder rerank, citation-graph expansion, persona injection,
reasoning-framework selection, output-schema directive,
context-window packing, LLMLingua compression, cost-ceiling gate, and
trace attachment — THEN the LLM is called, THEN post-API the response
goes through citation extraction, hallucination scoring, official-source
verification, schema validation, self-refine critique loop, audit
emission, and delivery formatting.

Not every use case needs all 22 passes — pick the subset that fits.
Use this as a reference for what's possible.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | research, retrieval, reasoning, verification, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | mixed |
| license | MIT |



## Task

Given a research query, run it through every supported pre/post-API pass:
redact, guard, expand, classify, decompose, multi-query, sanitize, retrieve
(BM25+dense+RRF), rerank, citation-graph expand, persona, framework-select,
schema-inject, context-pack, compress, gate, LLM call, parse, hallucination-score,
official-source verify, schema-validate, iterative-revise, audit, deliver.

**pipeline_kind:** `research_entity`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `1_cost_gate` | processor | `processor/cost-ceiling-gate` | — |
| 2 | `2_redact_pii` | harness | `harness/redact-pii-text` | — |
| 3 | `3_grep_secrets` | rule_pack | `rule-pack/grep-ai-vendor-keys` | — |
| 4 | `4_guard_prompt_injection` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 5 | `5_expand_abbreviations` | knowledge_pack | `knowledge-pack/common-abbreviations` | — |
| 6 | `6_classify_intent` | processor | `processor/intent-dispatcher` | — |
| 7 | `7_decompose_subquestions` | processor | `processor/sub-question-decomposer` | — |
| 8 | `8_hyde_expand` | processor | `processor/hyde-query-expander` | — |
| 9 | `9_sanitize_search_query` | rule_pack | `rule-pack/web-search-allowlist-default` | — |
| 10 | `10_hybrid_retrieve` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 11 | `11_web_search` | tool | `tool/web-search` | — |
| 12 | `12_verify_official_sources` | processor | `processor/official-sources-checker` | — |
| 13 | `13_rerank` | processor | `processor/cross-encoder-reranker` | — |
| 14 | `14_select_framework` | processor | `processor/reasoning-framework-selector` | — |
| 15 | `15_pack_context` | processor | `processor/context-window-packer` | — |
| 16 | `16_compress_context` | processor | `processor/llmlingua-context-compressor` | — |
| 17 | `17_inject_schema` | processor | `processor/inject-output-schema` | — |
| 18 | `18_llm_call` | harness | `harness/text-safety-review` | — |
| 19 | `19_hallucination_score` | processor | `processor/hallucination-scorer` | — |
| 20 | `20_citation_coverage` | processor | `processor/citation-coverage` | — |
| 21 | `21_iterative_revise` | processor | `processor/iterative-revise-loop` | — |
| 22 | `22_audit_trace` | processor | `processor/audit-trace-emitter` | — |

