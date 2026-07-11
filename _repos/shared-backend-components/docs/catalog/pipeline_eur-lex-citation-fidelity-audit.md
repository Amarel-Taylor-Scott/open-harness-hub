# EUR-Lex citation-fidelity audit for compliance memos

*pipeline* · `pipeline/eur-lex-citation-fidelity-audit` · v0.1.0 · experimental

Audits a regulatory compliance memo's citations to EUR-Lex instruments
(e.g. "Art 9 Reg (EU) 2024/1689", "Art 35 GDPR") for fidelity: does each cited
article actually exist, and does its text support the claim the memo attaches
to it? Returns per-citation supported / unsupported / misattributed /
not-found, with the retrieved authoritative passage and a corrected citation
when the article number is wrong.

Negative-space task: a bare LLM invents plausible-looking article numbers and
attaches real-sounding obligations to the wrong provision — the classic
fabricated-legal-citation failure that is unacceptable in a regulated filing.
This pipeline runs a citation-fidelity bundle: it extracts each citation,
retrieves the controlling article text from the AI Act / governance corpus,
and runs a chain-of-verification pass that must quote the supporting span or
downgrade the citation — every claim is re-checked against the primary text
rather than trusted.

| axis | value |
|---|---|
| industry | ai_governance, ai_governance.eu_act, legal.compliance, government.regulatory |
| capability | verification, retrieval, evaluation, extraction |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | dated |
| license | MIT |



## Task

Audit each EUR-Lex citation in a compliance memo for fidelity (exists + supports the claim), returning supported/unsupported/misattributed/not-found with the authoritative passage and a corrected citation where needed.

**pipeline_kind:** `evaluate`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `extract_citations` | processor | `processor/entity-resolution-link` | - |
| 3 | `retrieve_article_text` | processor | `processor/hybrid-bm25-vector-retrieve` | - |
| 4 | `rerank_passages` | processor | `processor/cross-encoder-reranker` | - |
| 5 | `verify_citations` | loop | `pattern/chain-of-verification` | - |
| 6 | `citation_coverage` | processor | `processor/citation-coverage` | - |
| 7 | `official_sources` | processor | `processor/official-sources-checker` | - |
| 8 | `grade` | processor | `processor/llm-judge` | - |
| 9 | `summary` | processor | `processor/review-summary-composer` | - |
| 10 | `audit` | processor | `processor/audit-trace-emitter` | - |

