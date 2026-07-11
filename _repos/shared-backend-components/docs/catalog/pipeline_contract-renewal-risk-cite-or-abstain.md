# Contract renewal-risk review (cite-or-abstain)

*pipeline* · `pipeline/contract-renewal-risk-cite-or-abstain` · v0.1.0 · experimental

Surface the renewal-risk clauses in a commercial contract + account
packet and ground EACH risk finding in a cited clause span or
renewal-risk framework entry — otherwise abstain. High-precision
legal/regulated RAG bundle (Bundle B) wired as a governed gate:

 - structured-to-prose + PII redaction (account packets carry names);
 - GREP triage for auto-renewal / notice-window / price-escalator /
   termination-for-convenience / assignment red flags;
 - hybrid retrieval over the contract-law clause library + the
   renewal-risk framework corpus, fused + cross-encoder reranked;
 - a renewal-risk analyst harness emits one finding per risk with a
   per-claim citation to the clause or framework span;
 - DETERMINISTIC cite-or-abstain gate: a renewal-risk finding that
   does not cite a clause/framework span fails citation-coverage and
   blocks publication, so an unsupported "this auto-renews in 30 days"
   claim cannot ship without the clause behind it.

Negative-space task: base models confidently assert renewal terms
("notice period is 60 days") that the contract does not contain.
Here every term must trace to the cited clause or be abstained.

NOT legal advice; descriptive over the provided contract only.

| axis | value |
|---|---|
| industry | legal, legal.contract, customer_success, customer_success.renewal |
| capability | extraction, retrieval, verification, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Given a commercial contract plus an account packet, surface
renewal-risk findings (auto-renewal, notice window, price escalator,
termination, assignment, value-realization gaps) where EACH finding
cites the clause span or renewal-risk framework entry that grounds
it, or abstain. Publication is blocked unless citation coverage and
the hallucination score clear threshold.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `chunk_contract` | chunker | `processor/page-aware-chunker` | - |
| 4 | `grep_flags` | rule_pack | `rule-pack/grep-customer-renewal-risk-flags` | - |
| 5 | `retrieve_context` | rule_pack | `rule-pack/hybrid-retrieval-policy` | - |
| 6 | `rerank` | processor | `processor/cross-encoder-reranker` | - |
| 7 | `review_harness` | harness | `harness/customer-renewal-risk-review` | - |
| 8 | `dedupe_findings` | processor | `processor/finding-deduplicator` | - |
| 9 | `calibrate_severity` | processor | `processor/severity-calibrator` | - |
| 10 | `check_citations` | processor | `processor/citation-span-checker` | - |
| 11 | `citation_coverage` | processor | `processor/citation-coverage` | - |
| 12 | `extract_evidence_gaps` | processor | `processor/evidence-gap-extractor` | - |
| 13 | `grade` | processor | `processor/llm-judge` | - |
| 14 | `redaction_audit` | processor | `processor/packet-redaction-audit` | - |
| 15 | `audit` | processor | `processor/audit-trace-emitter` | - |

