---
name: clinical-decision-support
description: Healthcare-specific harness for differential-diagnosis reasoning. Composes
  the clinical-reasoner persona, red-flag classifier rules, HIPAA PHI privacy gate,
  clinical-guideline RAG, ICD-10 lookup tool, and a citation-first response policy.
  Educational / decision- support framing; never a substitute for a licensed clinician.
when_to_use: Use when the user needs reasoning. Use when the user needs retrieval.
  Use when the user needs safety_gating. Use when the user needs tool_use. Particularly
  relevant for healthcare. Particularly relevant for healthcare.clinical.
---

# Clinical Decision Support

Healthcare-specific harness for differential-diagnosis reasoning.
Composes the clinical-reasoner persona, red-flag classifier rules,
HIPAA PHI privacy gate, clinical-guideline RAG, ICD-10 lookup tool,
and a citation-first response policy. Educational / decision-
support framing; never a substitute for a licensed clinician.

## Applied layers

- `persona`
- `grep`
- `classifier`
- `rag`
- `tools`
- `privacy`

## Differential diagnosis with red-flag escalation

*model_call:* `required`

**Steps**

1. redact PHI (rule-pack/phi-hipaa-en)
2. fire red-flag classifier (rule-pack/clinical-red-flags)
3. if any red flag fires → first sentence states the flag + recommend immediate evaluation
4. retrieve guideline chunks (knowledge-pack/clinical-guidelines-sample)
5. expand chunks with 1-hop citation graph
6. call ICD-10 lookup tool for code candidates
7. compose persona + retrieved chunks + tool results
8. call model
9. verify every claim cited by guideline section
10. produce ranked differential with prior probabilities

**Verification**

- no PHI in output (re-scan)
- every differential has at least one cited section
- red flag, if present, in first sentence

## Privacy boundaries

- **raw_input**: stays local; never sent to external API by default
- **derived_output**: stays local; only sharable after explicit user opt-in AND PHI re-scan
- **external_calls**: none by default; external judges require user opt-in
- **hipaa_safe_harbor**: applies — 18 identifier categories are redacted on input

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `self_hosted_gpu` | `transformers` | local | False | False |

## Provenance

- Hub artifact: `harness/clinical-decision-support` v0.1.0
- License: `MIT`
- Lifecycle: `experimental`
- Full source manifest: see `references/manifest.yaml`
