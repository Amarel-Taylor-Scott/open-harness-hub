---
name: differential-diagnosis
description: Given a clinical vignette (presentation, history, exam), produce a PHI-safe,
  cite-or-omit differential diagnosis with red-flag escalation and ICD-10 code candidates.
when_to_use: 'Pipeline kind: classify.'
---

# Differential Diagnosis

Educational decision-support pipeline. Given (presentation, history,
exam) text, returns a ranked differential diagnosis with cited
guideline sections, ICD-10 code candidates, and red-flag
escalation. PHI is redacted before any model call.

Not a substitute for a licensed clinician. Intended as a
reproducible reference instance for the catalog.

## Task

Given a clinical vignette (presentation, history, exam), produce a
PHI-safe, cite-or-omit differential diagnosis with red-flag
escalation and ICD-10 code candidates.

## Steps

1. **redact_phi** — `harness` → `harness/redact-pii-text`
2. **red_flag_screen** — `rule_pack` → `rule-pack/clinical-red-flags`
3. **retrieve_guidelines** — `knowledge_pack` → `knowledge-pack/clinical-guidelines-sample`
4. **lookup_codes** — `tool` → `tool/lookup-icd10`
5. **reason** — `harness` → `harness/clinical-decision-support`

## Defaults

- **persona**: persona/clinical-reasoner
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/clinical-guidelines-sample`, `knowledge-pack/icd10-sample`
- **rule_packs**: `rule-pack/phi-hipaa-en`, `rule-pack/clinical-red-flags`

## Success criteria

- rubric `rubric/clinical-grounded-response-v1` threshold 0.8

## Provenance

- Hub artifact: `pipeline/differential-diagnosis` v0.1.0
- License: `MIT`
- Industry: healthcare, healthcare.clinical
- Full source manifest: see `references/manifest.yaml`
