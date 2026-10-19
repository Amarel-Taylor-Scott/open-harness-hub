---
name: modern-slavery-statement-completeness
description: Score a published modern-slavery statement for completeness against the
  mandatory reporting criteria of the controlling law (covered | partial | missing),
  citing the statement span and the legal criterion for each.
when_to_use: 'Pipeline kind: evaluate.'
---

# Modern-slavery statement completeness screen (UK MSA §54 / AU MSA / Canada S-211 / CA SB-657)

HIGH-PRECISION legal-disclosure pipeline. Reads a company's *published
modern-slavery / forced-labour transparency statement* and checks it
against the mandatory reporting criteria of the relevant law, returning a
per-criterion covered / partial / missing verdict with the exact statement
span and the controlling legal citation for each.

Negative-space task: a bare model asked "is this statement compliant?"
produces a fluent but unreliable yes/no — it does not reliably enumerate
the *specific* mandated criteria (UK MSA §54(5) six areas; AU MSA seven
mandatory criteria; Canada S-211 §11 report contents; CA SB-657 five
disclosure areas), and it hallucinates coverage for criteria the document
silently omits. The expensive, durable lift is exact-criterion mapping:
each required criterion must be located in the text or explicitly marked
absent, every verdict tied to a primary-law span. That is precisely what
this pipeline freezes into deterministic retrieval + a cite-or-abstain
judge.

Bundle: High-precision legal / regulated RAG (taxonomy Bundle B) — query
decomposition over the multi-criterion checklist, hybrid retrieval against
the due-diligence regulatory pack with source-precedence (controlling law
wins), a checklist evaluator, and a strict cite-every-verdict-or-mark-
missing judge. Output is an auditable completeness scorecard, NOT a legal
opinion; "missing" means the criterion was not located in the document,
not that the company is non-compliant.

## Task

Score a published modern-slavery statement for completeness against the mandatory reporting criteria of the controlling law (covered | partial | missing), citing the statement span and the legal criterion for each.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **decompose_criteria** — `processor` → `processor/sub-question-decomposer`
4. **grep_disclosure_flags** — `rule_pack` → `rule-pack/grep-apparel-forced-labor-trace-flags`
5. **retrieve_legal_criteria** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
6. **rerank_criteria** — `processor` → `processor/cross-encoder-reranker`
7. **checklist_evaluate** — `processor` → `processor/checklist-evaluator`
8. **grade_completeness** — `harness` → `harness/esg-disclosure-grading`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **check_citations** — `processor` → `processor/citation-span-checker`
11. **citation_coverage** — `processor` → `processor/citation-coverage`
12. **grade** — `processor` → `processor/llm-judge`
13. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
14. **summary** — `processor` → `processor/review-summary-composer`
15. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/esg-auditor
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/csddd-and-forced-labor-indicators`
- **rule_packs**: `rule-pack/grep-apparel-forced-labor-trace-flags`, `rule-pack/hybrid-retrieval-policy`

## Success criteria

- rubric `rubric/esg-gov-v1` threshold 0.7
- deterministic `$.steps.check_citations.output.result.pass` == `True`
- deterministic `$.steps.citation_coverage.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/modern-slavery-statement-completeness` v0.1.0
- License: `MIT`
- Industry: esg.modern_slavery, esg.csddd, legal.compliance, supply_chain.due_diligence
- Full source manifest: see `references/manifest.yaml`
