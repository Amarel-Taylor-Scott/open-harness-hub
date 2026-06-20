# Cite-first regulatory counsel (cite-or-abstain)

*pipeline* · `pipeline/regulatory-counsel-cite-or-abstain` · v0.1.0 · experimental

Answer a regulated entity's compliance question ONLY with answers
that trace to a primary statutory/regulatory authority — otherwise
abstain. This is the High-precision legal/regulated RAG bundle
(Bundle B) wired as a hard governed gate, not a rubric suggestion:

 - page/structure-aware chunking preserves citable section anchors;
 - hybrid retrieval (field-weighted lexical + dense) over a governed
   statute/canon corpus, fused + cross-encoder reranked;
 - a cite-first counsel persona + harness emits one finding per
   sub-question with a per-claim citation;
 - DETERMINISTIC cite-or-abstain gate: every load-bearing sentence
   must carry a citation marker (citation-coverage) AND the
   self-consistency hallucination score must stay below threshold —
   if either fails the pipeline does NOT pass, forcing an abstain /
   human-review outcome.

The negative-space task: a base model will fluently answer
"does requirement X apply to entity type Y?" with a plausible but
fabricated citation. Here the answer is structurally barred from
publication unless each claim is grounded in a retrieved authority.

NOT legal advice; descriptive; jurisdiction-bound to the cited
authorities only.

| axis | value |
|---|---|
| industry | legal, legal.compliance, government, government.regulatory |
| capability | retrieval, extraction, verification, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Given a regulated entity's compliance question (entity type +
jurisdiction + question), retrieve the controlling statutory /
regulatory authority and return a per-sub-question answer in which
EVERY load-bearing claim carries a citation to a retrieved
authority, or abstain. Publication is blocked unless citation
coverage clears threshold and the hallucination score is low.

**pipeline_kind:** `rag_pack`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `normalize` | processor | `processor/structured-to-prose` | - |
| 2 | `chunk_authorities` | chunker | `processor/page-aware-chunker` | - |
| 3 | `grep_ambiguity` | rule_pack | `rule-pack/grep-statute-ambiguity-flags` | - |
| 4 | `retrieve_authorities` | rule_pack | `rule-pack/hybrid-retrieval-policy` | - |
| 5 | `rerank` | processor | `processor/cross-encoder-reranker` | - |
| 6 | `counsel` | harness | `harness/statute-clarity-review` | - |
| 7 | `citation_coverage` | processor | `processor/citation-coverage` | - |
| 8 | `hallucination_check` | processor | `processor/hallucination-scorer` | - |
| 9 | `grade` | processor | `processor/llm-judge` | - |
| 10 | `audit` | processor | `processor/audit-trace-emitter` | - |

