# ESG Disclosure Grading harness

*harness* · `harness/esg-disclosure-grading` · v0.1.0 · beta

Wraps the ESG supplier-policy-grading flow as a reusable harness
with persona + GREP + RAG + tools layers. Targets local-Ollama or
Anthropic/OpenAI for the judge model arm; emits citation-first
findings with CSDDD article + ILO indicator + national-law links.

| axis | value |
|---|---|
| industry | esg, supply_chain, compliance |
| capability | evaluation, verification, retrieval, reasoning |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Consumes:** `grep_rule`, `rag_doc`, `persona_block`, `response_policy`

**Emits:** `reasoning_step`, `context_snippet`

**Contributes to:** `pipeline/supplier-policy-grading`, `pipeline/deep-tier-supplier-audit`, `pipeline/full-vendor-due-diligence`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_judge` | `anthropic` | external | False | False |

## Logic paths

### supplier-pack → red flags → CSDDD citations → grade + remediation  
*model_call: `required`*

1. structured-to-prose normalize
1. redact PII per HIPAA Safe Harbor + DPV
1. fire S+E+G GREP packs
1. RAG against CSDDD + corridors + lead-company code
1. judge against esg-supplier-compliance rubric
1. propose Art-10 remediation with milestones
1. emit audit trace per CSDDD Art-26

**consumes:** `grep_rule`, `rag_doc`, `persona_block`, `response_policy`

**emits:** `reasoning_step`, `context_snippet`

**verification:** every severity ≥ medium finding has ILO indicator + CSDDD article + national-law citations, no PII in quoted grievance snippets, CSDDD-Art.10 right-of-reply path proposed



## Privacy boundaries

- **raw_input**: stays local to the running pipeline
- **derived_output**: may sync to hub only after anonymization gate
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

