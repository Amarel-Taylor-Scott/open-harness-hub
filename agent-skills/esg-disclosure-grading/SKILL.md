---
name: esg-disclosure-grading
description: Wraps the ESG supplier-policy-grading flow as a reusable harness with
  persona + GREP + RAG + tools layers. Targets local-Ollama or Anthropic/OpenAI for
  the judge model arm; emits citation-first findings with CSDDD article + ILO indicator
  + national-law links.
when_to_use: Use when the user needs evaluation. Use when the user needs verification.
  Use when the user needs retrieval. Use when the user needs reasoning. Particularly
  relevant for esg. Particularly relevant for supply_chain. Particularly relevant
  for compliance.
---

# ESG Disclosure Grading harness

Wraps the ESG supplier-policy-grading flow as a reusable harness
with persona + GREP + RAG + tools layers. Targets local-Ollama or
Anthropic/OpenAI for the judge model arm; emits citation-first
findings with CSDDD article + ILO indicator + national-law links.

## Applied layers

- `persona`
- `grep`
- `rag`
- `tools`

## supplier-pack → red flags → CSDDD citations → grade + remediation

*model_call:* `required`

**Steps**

1. structured-to-prose normalize
2. redact PII per HIPAA Safe Harbor + DPV
3. fire S+E+G GREP packs
4. RAG against CSDDD + corridors + lead-company code
5. judge against esg-supplier-compliance rubric
6. propose Art-10 remediation with milestones
7. emit audit trace per CSDDD Art-26

**Verification**

- every severity ≥ medium finding has ILO indicator + CSDDD article + national-law citations
- no PII in quoted grievance snippets
- CSDDD-Art.10 right-of-reply path proposed

## Privacy boundaries

- **raw_input**: stays local to the running pipeline
- **derived_output**: may sync to hub only after anonymization gate
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_judge` | `anthropic` | external | False | False |

## Provenance

- Hub component: `harness/esg-disclosure-grading` v0.1.0
- License: `MIT`
- Lifecycle: `beta`
- Full source manifest: see `references/manifest.yaml`
