---
name: radiology-report-grading
description: 'Given a radiology report (string OR structured dict), grade it against
  the radiology-report-quality rubric. Output: per-dimension score + findings (missing-RADS,
  missing-followup, etc.) + citations to the relevant ACR / Fleischner / RADS guideline.'
when_to_use: 'Pipeline kind: grading.'
---

# Radiology report grading (RADS-aware, Fleischner-aware)

Grade a radiology report against `rubric/radiology-report-quality-
v1`. The pipeline reuses the SAME primitives as the ESG grading
pipeline:
 1. `processor/structured-to-prose` — flatten any structured input
 2. `processor/redact-pii-text` + `rule-pack/phi-hipaa-en` —
    strip PHI
 3. `rule-pack/grep-radiology-report-red-flags` — incidental
    findings + missing-RADS + Fleischner non-compliance heuristics
 4. RAG against `knowledge-pack/radiology-acrac-fleischner`
 5. `processor/llm-judge` against the rubric
 6. `processor/audit-trace-emitter` for record-keeping

Demonstrates the architecture's cross-vertical reusability: the
exact same harness/GREP/RAG/judge chain that grades ESG supplier
disclosures also grades radiology reports — only the rubric,
knowledge pack, and rule pack change.

## Task

Given a radiology report (string OR structured dict), grade it
against the radiology-report-quality rubric. Output: per-dimension
score + findings (missing-RADS, missing-followup, etc.) + citations
to the relevant ACR / Fleischner / RADS guideline.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_phi** — `processor` → `processor/redact-pii-text`
3. **grep_phi** — `rule_pack` → `rule-pack/phi-hipaa-en`
4. **grep_radiology_red_flags** — `rule_pack` → `rule-pack/grep-radiology-report-red-flags`
5. **rag_against_acrac** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/radiologist-cite-first
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/phi-hipaa-en`, `rule-pack/grep-radiology-report-red-flags`
- **knowledge_packs**: `knowledge-pack/radiology-acrac-fleischner`

## Success criteria

- rubric `rubric/radiology-report-quality-v1` threshold 0.7

## Provenance

- Hub artifact: `pipeline/radiology-report-grading` v0.1.0
- License: `MIT`
- Industry: healthcare, healthcare.radiology
- Full source manifest: see `references/manifest.yaml`
