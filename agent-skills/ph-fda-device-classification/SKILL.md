---
name: ph-fda-device-classification
description: Assign a medical device its Philippine FDA risk class (A/B/C/D) and registration
  pathway under the ASEAN-harmonised rules, with the governing rule cited and the
  matched intended-use/invasiveness factor, or abstain with a clarifying question
  when the description is insufficient.
when_to_use: 'Pipeline kind: classify.'
---

# Philippine FDA medical-device risk classification

Assigns a medical device its Philippine FDA risk class (Class A / B / C / D
under the ASEAN-harmonised classification rules adopted by FDA Circular and
AO 2018-0002) and the corresponding registration pathway, returning the
governing classification rule, the matched intended-use/invasiveness factor,
and the citable rule text — or an abstention plus a clarifying question when
the submitted device description is too thin to classify.

Negative-space task: a bare LLM conflates US FDA Class I/II/III with the ASEAN
A/B/C/D scheme the Philippines uses, guesses a class from the device name, and
never asks for the duration-of-contact / invasiveness facts the rules actually
turn on. This pipeline runs a high-precision regulated-RAG bundle with a
corrective-retrieval gate: deterministic normalization, field-weighted + dense
retrieval over the classification rules, a cite-first reviewer, and a
retrieval-quality Conditional that forces abstention-with-question instead of a
fabricated class when the matched rule does not cover the device's stated factors.

## Task

Assign a medical device its Philippine FDA risk class (A/B/C/D) and registration pathway under the ASEAN-harmonised rules, with the governing rule cited and the matched intended-use/invasiveness factor, or abstain with a clarifying question when the description is insufficient.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **normalize_country** — `processor` → `processor/iso-country-normalize`
3. **decompose_factors** — `processor` → `processor/sub-question-decomposer`
4. **retrieve_rules** — `rule_pack` → `rule-pack/rag-medical-device-complaint-retrieval-policy`
5. **rerank_rules** — `processor` → `processor/cross-encoder-reranker`
6. **inject_schema** — `processor` → `processor/inject-output-schema`
7. **classify_harness** — `harness` → `harness/medical-device-complaint-review`
8. **corrective_gate** — `branch` → `pattern/corrective-rag`
9. **check_citation_spans** — `processor` → `processor/citation-span-checker`
10. **grade** — `processor` → `processor/llm-judge`
11. **summary** — `processor` → `processor/review-summary-composer`
12. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/device-complaint-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/medical-device-complaint-frameworks`, `knowledge-pack/standards-regulatory-source-map`
- **rule_packs**: `rule-pack/rag-medical-device-complaint-retrieval-policy`

## Success criteria

- rubric `rubric/medical-device-complaint-quality-v1` threshold 0.7
- deterministic `$.steps.check_citation_spans.output.result.pass` == `True`
- regex `^(A|B|C|D)$` against `$.steps.corrective_gate.output.risk_class`

## Provenance

- Hub component: `pipeline/ph-fda-device-classification` v0.1.0
- License: `MIT`
- Industry: medical_devices, medical_devices.qms, government.regulatory, healthcare
- Full source manifest: see `references/manifest.yaml`
