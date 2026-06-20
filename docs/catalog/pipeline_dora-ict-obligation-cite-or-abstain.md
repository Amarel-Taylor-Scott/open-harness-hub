# EU DORA ICT third-party obligation answer (cite-or-abstain)

*pipeline* · `pipeline/dora-ict-obligation-cite-or-abstain` · v0.1.0 · experimental

Answer whether a specific EU DORA (Digital Operational Resilience
Act) ICT third-party / operational-resilience obligation applies to
a financial entity's stated arrangement, grounded ONLY in cited DORA
obligation provisions — otherwise abstain. High-precision regulated
RAG bundle (Bundle B) wired as a governed gate for a volatile,
regulation-specific domain a base model has no reliable map of:

 - structured-to-prose on the arrangement description;
 - hybrid retrieval over the DORA ICT-resilience obligations corpus,
   fused + cross-encoder reranked to the controlling article(s);
 - cite-first regulatory persona + statute-clarity harness produces a
   yes / no / conditional applicability answer with a per-claim
   citation to the DORA article it rests on;
 - DETERMINISTIC cite-or-abstain gate: an applicability claim with
   no citation to a retrieved DORA provision fails citation-coverage
   and blocks publication — the model may NOT assert "Article 28
   requires X" without the provision behind it.

Negative-space task: DORA is recent, dense, and entity-type
conditional; base models confidently mis-state which article governs
ICT third-party risk and fabricate article numbers. Grounding every
applicability claim in a cited provision, or abstaining, is the
capability the bare model lacks.

NOT legal advice; descriptive over the cited DORA provisions only.

| axis | value |
|---|---|
| industry | legal, legal.compliance, finance, compliance |
| capability | retrieval, extraction, verification, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Given a financial entity's ICT arrangement description plus an
applicability question, answer whether the specified DORA ICT
third-party / operational-resilience obligation applies, grounding
each applicability claim in a cited DORA provision, or abstain.
Publication is blocked unless citation coverage and the
hallucination score clear threshold.

**pipeline_kind:** `rag_pack`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `normalize` | processor | `processor/structured-to-prose` | - |
| 2 | `grep_terms` | rule_pack | `rule-pack/grep-statute-ambiguity-flags` | - |
| 3 | `retrieve_provisions` | rule_pack | `rule-pack/hybrid-retrieval-policy` | - |
| 4 | `rerank` | processor | `processor/cross-encoder-reranker` | - |
| 5 | `answer` | harness | `harness/statute-clarity-review` | - |
| 6 | `citation_coverage` | processor | `processor/citation-coverage` | - |
| 7 | `hallucination_check` | processor | `processor/hallucination-scorer` | - |
| 8 | `grade` | processor | `processor/llm-judge` | - |
| 9 | `audit` | processor | `processor/audit-trace-emitter` | - |

