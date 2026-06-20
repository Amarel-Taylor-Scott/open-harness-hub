---
name: statute-cross-reference-cite-or-abstain
description: Given a statute/regulation excerpt containing internal cross-references,
  resolve each reference to the provision it points at and state what that provision
  says, with an exact-section citation per resolved reference, or abstain. Publication
  is blocked unless citation coverage and the hallucination score clear threshold.
when_to_use: 'Pipeline kind: rag_pack.'
---

# Statute cross-reference resolution (cite-or-abstain)

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

## Task

Given a statute/regulation excerpt containing internal
cross-references, resolve each reference to the provision it points
at and state what that provision says, with an exact-section
citation per resolved reference, or abstain. Publication is blocked
unless citation coverage and the hallucination score clear
threshold.

## Steps

1. **normalize** — `processor` → `processor/structured-to-prose`
2. **chunk_statute** — `chunker` → `processor/page-aware-chunker`
3. **grep_refs** — `rule_pack` → `rule-pack/grep-statute-ambiguity-flags`
4. **retrieve_targets** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **rerank** — `processor` → `processor/cross-encoder-reranker`
6. **resolve** — `harness` → `harness/statute-clarity-review`
7. **citation_coverage** — `processor` → `processor/citation-coverage`
8. **hallucination_check** — `processor` → `processor/hallucination-scorer`
9. **grade** — `processor` → `processor/llm-judge`
10. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/legal-clarity-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/statute-citation-and-crossref-grounding`, `knowledge-pack/legal-interpretation-canons`
- **rule_packs**: `rule-pack/grep-statute-ambiguity-flags`, `rule-pack/hybrid-retrieval-policy`

## Success criteria

- rubric `rubric/statute-clarity-v1` threshold 0.7
- deterministic `$.steps.citation_coverage.output.passes` == `True`
- deterministic `$.steps.citation_coverage.output.coverage` >= `0.95`
- deterministic `$.steps.hallucination_check.output.overall_score` <= `0.15`

## Provenance

- Hub component: `pipeline/statute-cross-reference-cite-or-abstain` v0.1.0
- License: `MIT`
- Industry: legal, legal.compliance, government, government.regulatory
- Full source manifest: see `references/manifest.yaml`
