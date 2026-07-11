# Statute cross-reference resolution (cite-or-abstain)

*pipeline* · `pipeline/statute-cross-reference-cite-or-abstain` · v0.1.0 · experimental

Resolve the internal cross-references in a statute or regulation
("subject to subsection (b)", "as defined in §3", "notwithstanding
paragraph (2)") and answer what the cross-referenced provision
actually says — with an EXACT-section citation for every resolved
reference, or abstain. High-precision legal/regulated RAG bundle
(Bundle B) with an exact-id retrieval leg as the load-bearing lock:

 - GREP/regex triage extracts the section/paragraph identifiers and
   defined-term references in the input;
 - hybrid retrieval (the exact-id leg matches §/¶ numbers that
   embeddings blur; the dense leg covers defined-term phrasing) over
   the statute citation + cross-reference grounding corpus, fused +
   cross-encoder reranked;
 - cite-first counsel persona + statute-clarity harness resolves each
   reference to the provision it points at, with a per-reference
   citation;
 - DETERMINISTIC cite-or-abstain gate: a resolved cross-reference
   with no citation to the target provision fails citation-coverage
   and blocks publication — the model may NOT assert what an
   unretrieved §X says.

Negative-space task: base models hallucinate the content of a
cross-referenced section ("§4(b) requires written notice") when the
section was never retrieved. Exact-id matching + cite-or-abstain
make the resolution verifiable instead of fluent-but-wrong.

NOT legal advice; descriptive over the cited authorities only.

| axis | value |
|---|---|
| industry | legal, legal.compliance, government, government.regulatory |
| capability | extraction, retrieval, verification, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Given a statute/regulation excerpt containing internal
cross-references, resolve each reference to the provision it points
at and state what that provision says, with an exact-section
citation per resolved reference, or abstain. Publication is blocked
unless citation coverage and the hallucination score clear
threshold.

**pipeline_kind:** `rag_pack`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `normalize` | processor | `processor/structured-to-prose` | - |
| 2 | `chunk_statute` | chunker | `processor/page-aware-chunker` | - |
| 3 | `grep_refs` | rule_pack | `rule-pack/grep-statute-ambiguity-flags` | - |
| 4 | `retrieve_targets` | rule_pack | `rule-pack/hybrid-retrieval-policy` | - |
| 5 | `rerank` | processor | `processor/cross-encoder-reranker` | - |
| 6 | `resolve` | harness | `harness/statute-clarity-review` | - |
| 7 | `citation_coverage` | processor | `processor/citation-coverage` | - |
| 8 | `hallucination_check` | processor | `processor/hallucination-scorer` | - |
| 9 | `grade` | processor | `processor/llm-judge` | - |
| 10 | `audit` | processor | `processor/audit-trace-emitter` | - |

