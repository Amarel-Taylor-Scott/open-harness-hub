# Deposition transcript page:line index with cited topic digest + contradiction flags

*pipeline* · `pipeline/deposition-page-line-index` · v0.1.0 · experimental

Negative-space task: turning a long deposition transcript into a usable
index for litigation. A bare LLM summarizes a deposition fluently but (a)
fabricates or mis-attributes the page:line citations that make a digest
admissible/usable, (b) loses the thread across hundreds of pages, and (c)
cannot reliably flag where a witness contradicts an earlier answer. This
pipeline extracts page-anchored text, chunks page-aware so every chunk keeps
its page:line, retrieves topic-relevant testimony with hybrid + rerank, and
produces a topic digest where EVERY assertion must carry a verbatim quote +
its page:line — verified deterministically so an entry with an unsupported
or unparseable citation fails the run rather than shipping.

Capability lift is structural: the durable lift is citation fidelity (every
index entry traces to a real page:line span) — a verification step, not a
model capability that closes on the next release. Extraction, page-aware
chunking, hybrid retrieval, rerank, and the citation-coverage check are
freezable and cost no model tokens beyond the digest call.

Bundle: High-precision legal RAG for regulated domains (taxonomy Bundle B) —
page/structure-aware chunking to preserve citable anchors, hybrid BM25 +
dense + rerank, cite-every-claim-or-abstain output, and a citation-coverage
gate.

| axis | value |
|---|---|
| industry | legal.litigation, legal.compliance |
| capability | extraction, retrieval, verification, summarization |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Given a deposition transcript PDF and a list of issue topics, produce a
topic-indexed digest where every assertion is backed by a verbatim quote
and its exact page:line citation, plus a list of intra-witness
contradictions (each pointing to the two conflicting page:line spans). Fail
if any index entry's citation cannot be resolved to a real page:line span.

**pipeline_kind:** `extract`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `pdf_extract` | processor | `processor/pdf-extract-with-ocr-fallback` | - |
| 2 | `page_aware_chunk` | processor | `processor/page-aware-chunker` | - |
| 3 | `embed_local` | processor | `processor/local-embedder` | - |
| 4 | `hybrid_retrieve` | rule_pack | `rule-pack/hybrid-retrieval-policy` | - |
| 5 | `rerank` | processor | `processor/cross-encoder-reranker` | - |
| 6 | `guard_chunks` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | - |
| 7 | `redact_chunks_pii` | rule_pack | `rule-pack/privacy-pii-text-en` | - |
| 8 | `build_index` | harness | `harness/text-safety-review` | - |
| 9 | `verify_citation_coverage` | processor | `processor/citation-coverage` | - |
| 10 | `check_citations` | processor | `processor/citation-span-checker` | - |
| 11 | `concept_graph` | processor | `processor/concept-graph-extractor` | - |
| 12 | `grade` | processor | `processor/llm-judge` | - |
| 13 | `audit` | processor | `processor/audit-trace-emitter` | - |

