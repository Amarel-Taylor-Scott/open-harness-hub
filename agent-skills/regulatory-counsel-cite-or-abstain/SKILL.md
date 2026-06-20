---
name: regulatory-counsel-cite-or-abstain
description: Given a regulated entity's compliance question (entity type + jurisdiction
  + question), retrieve the controlling statutory / regulatory authority and return
  a per-sub-question answer in which EVERY load-bearing claim carries a citation to
  a retrieved authority, or abstain. Publication is blocked unless citation coverage
  clears threshold and the hallucination score is low.
when_to_use: 'Pipeline kind: rag_pack.'
---

# Cite-first regulatory counsel (cite-or-abstain)

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

## Task

Given a regulated entity's compliance question (entity type +
jurisdiction + question), retrieve the controlling statutory /
regulatory authority and return a per-sub-question answer in which
EVERY load-bearing claim carries a citation to a retrieved
authority, or abstain. Publication is blocked unless citation
coverage clears threshold and the hallucination score is low.

## Steps

1. **normalize** — `processor` → `processor/structured-to-prose`
2. **chunk_authorities** — `chunker` → `processor/page-aware-chunker`
3. **grep_ambiguity** — `rule_pack` → `rule-pack/grep-statute-ambiguity-flags`
4. **retrieve_authorities** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **rerank** — `processor` → `processor/cross-encoder-reranker`
6. **counsel** — `harness` → `harness/statute-clarity-review`
7. **citation_coverage** — `processor` → `processor/citation-coverage`
8. **hallucination_check** — `processor` → `processor/hallucination-scorer`
9. **grade** — `processor` → `processor/llm-judge`
10. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/bureaucracy-translator-cite-first
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/statute-citation-and-crossref-grounding`, `knowledge-pack/legal-interpretation-canons`
- **rule_packs**: `rule-pack/grep-statute-ambiguity-flags`, `rule-pack/hybrid-retrieval-policy`

## Success criteria

- rubric `rubric/statute-clarity-v1` threshold 0.7
- deterministic `$.steps.citation_coverage.output.passes` == `True`
- deterministic `$.steps.citation_coverage.output.coverage` >= `0.95`
- deterministic `$.steps.hallucination_check.output.overall_score` <= `0.2`

## Provenance

- Hub component: `pipeline/regulatory-counsel-cite-or-abstain` v0.1.0
- License: `MIT`
- Industry: legal, legal.compliance, government, government.regulatory
- Full source manifest: see `references/manifest.yaml`
