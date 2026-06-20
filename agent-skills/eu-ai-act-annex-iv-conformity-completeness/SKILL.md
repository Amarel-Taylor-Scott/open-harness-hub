---
name: eu-ai-act-annex-iv-conformity-completeness
description: Check a high-risk AI system technical-documentation package for completeness
  against Article 11 / Annex IV of Regulation (EU) 2024/1689 and return a per-requirement
  present/partial/missing verdict with cited Annex IV points and supporting spans.
when_to_use: 'Pipeline kind: review.'
---

# EU AI Act Annex IV technical-documentation completeness check

Checks a high-risk AI system's technical-documentation package against the
Article 11 / Annex IV requirement list of Regulation (EU) 2024/1689, returns a
per-requirement present / partial / missing verdict, the cited Annex IV point
number, and the exact span in the submitted package that satisfies it (or an
evidence gap when nothing does).

Negative-space task: a bare LLM cannot reliably enumerate the nine Annex IV
points, map a provider's free-form documentation onto them, and refuse to mark
a point "present" without a citable span — it pattern-matches plausible-sounding
prose and silently passes incomplete dossiers. This pipeline runs a
high-precision legal-RAG bundle (Bundle B): deterministic redaction and
decomposition before the model, field-weighted + dense retrieval over the AI
Act corpus, a cite-or-abstain reviewer persona, then deterministic
citation-coverage and evidence-gap gates so an unsupported "present" cannot pass.

## Task

Check a high-risk AI system technical-documentation package for completeness against Article 11 / Annex IV of Regulation (EU) 2024/1689 and return a per-requirement present/partial/missing verdict with cited Annex IV points and supporting spans.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **chunk_doc** — `processor` → `processor/page-aware-chunker`
4. **decompose_requirements** — `processor` → `processor/sub-question-decomposer`
5. **retrieve_annex_iv** — `processor` → `processor/hybrid-bm25-vector-retrieve`
6. **rerank_context** — `processor` → `processor/cross-encoder-reranker`
7. **inject_schema** — `processor` → `processor/inject-output-schema`
8. **review_completeness** — `harness` → `harness/ai-red-team-findings-review`
9. **check_citation_spans** — `processor` → `processor/citation-span-checker`
10. **citation_coverage** — `processor` → `processor/citation-coverage`
11. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
12. **grade** — `processor` → `processor/llm-judge`
13. **summary** — `processor` → `processor/review-summary-composer`
14. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/ai-governance-auditor
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/ai-governance-frameworks`, `knowledge-pack/standards-regulatory-source-map`
- **rule_packs**: `rule-pack/web-search-allowlist-default`

## Success criteria

- rubric `rubric/ai-governance-quality-v1` threshold 0.72
- deterministic `$.steps.check_citation_spans.output.result.pass` == `True`
- deterministic `$.steps.citation_coverage.output.passes` == `True`

## Provenance

- Hub component: `pipeline/eu-ai-act-annex-iv-conformity-completeness` v0.1.0
- License: `MIT`
- Industry: ai_governance, ai_governance.eu_act, legal.compliance, government.regulatory
- Full source manifest: see `references/manifest.yaml`
