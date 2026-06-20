---
name: cfr-part11-records-control-gate
description: Gate an electronic-records system description against 21 CFR Part 11
  controls and return a per-control pass/fail/not-evidenced verdict with the cited
  subsection, plus a go/no-go disposition that blocks while any predicate control
  is unevidenced.
when_to_use: 'Pipeline kind: review.'
---

# 21 CFR Part 11 electronic-records control gate

Gates an electronic-records / electronic-signature system description against
the controls of 21 CFR Part 11 (FDA electronic records; electronic
signatures), returning a per-control pass / fail / not-evidenced verdict, the
cited Part 11 subsection, the matched control statement, and a go / no-go
disposition for whether the system may hold GxP records.

Negative-space task: a bare LLM treats Part 11 as a vibe ("you need audit
trails and e-signatures") and cannot map a specific control description onto
the enumerated §11.10 / §11.30 / §11.50 / §11.70 / §11.200 requirements, nor
refuse to pass a control it has no evidence for. This pipeline runs a
high-precision regulated-RAG bundle with a deterministic go/no-go checklist
gate: structure-aware retrieval over the Part 11 corpus, a records-retention
reviewer persona bound to cite-or-abstain, citation-span verification, and a
checklist gate that blocks a go disposition while any predicate control is
unevidenced.

## Task

Gate an electronic-records system description against 21 CFR Part 11 controls and return a per-control pass/fail/not-evidenced verdict with the cited subsection, plus a go/no-go disposition that blocks while any predicate control is unevidenced.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **chunk_controls** — `processor` → `processor/page-aware-chunker`
4. **decompose_controls** — `processor` → `processor/sub-question-decomposer`
5. **retrieve_part11** — `processor` → `processor/hybrid-bm25-vector-retrieve`
6. **rerank_part11** — `processor` → `processor/cross-encoder-reranker`
7. **inject_schema** — `processor` → `processor/inject-output-schema`
8. **review_controls** — `harness` → `harness/records-retention-disposition-review`
9. **check_citation_spans** — `processor` → `processor/citation-span-checker`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **go_nogo_gate** — `branch` → `pattern/go-nogo-checklist-gate`
12. **grade** — `processor` → `processor/llm-judge`
13. **summary** — `processor` → `processor/review-summary-composer`
14. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/records-retention-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/gxp-21-cfr-11-guidelines`, `knowledge-pack/standards-regulatory-source-map`
- **rule_packs**: `rule-pack/web-search-allowlist-default`

## Success criteria

- rubric `rubric/records-retention-disposition-quality-v1` threshold 0.72
- deterministic `$.steps.check_citation_spans.output.result.pass` == `True`
- regex `^(go|no-go)$` against `$.steps.go_nogo_gate.output.disposition`

## Provenance

- Hub component: `pipeline/cfr-part11-records-control-gate` v0.1.0
- License: `MIT`
- Industry: pharma.gxp, government.regulatory, medical_devices.qms, legal.compliance
- Full source manifest: see `references/manifest.yaml`
