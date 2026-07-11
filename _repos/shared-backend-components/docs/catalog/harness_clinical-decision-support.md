# Clinical Decision Support

*harness* · `harness/clinical-decision-support` · v0.1.0 · experimental

Healthcare-specific harness for differential-diagnosis reasoning.
Composes the clinical-reasoner persona, red-flag classifier rules,
HIPAA PHI privacy gate, clinical-guideline RAG, ICD-10 lookup tool,
and a citation-first response policy. Educational / decision-
support framing; never a substitute for a licensed clinician.

| axis | value |
|---|---|
| industry | healthcare, healthcare.clinical |
| capability | reasoning, retrieval, safety_gating, tool_use |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |

**Consumes:** `persona_block`, `grep_rule`, `classifier_rule`, `rag_doc`, `citation_edge`, `tool_definition`

**Emits:** `reasoning_step`, `context_snippet`, `audit_template`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `self_hosted_gpu` | `transformers` | local | False | False |

## Logic paths

### Differential diagnosis with red-flag escalation  
*model_call: `required`*

1. redact PHI (rule-pack/phi-hipaa-en)
1. fire red-flag classifier (rule-pack/clinical-red-flags)
1. if any red flag fires → first sentence states the flag + recommend immediate evaluation
1. retrieve guideline chunks (knowledge-pack/clinical-guidelines-sample)
1. expand chunks with 1-hop citation graph
1. call ICD-10 lookup tool for code candidates
1. compose persona + retrieved chunks + tool results
1. call model
1. verify every claim cited by guideline section
1. produce ranked differential with prior probabilities

**consumes:** `persona_block`, `grep_rule`, `classifier_rule`, `rag_doc`, `citation_edge`, `tool_definition`

**emits:** `reasoning_step`, `context_snippet`, `audit_template`

**verification:** no PHI in output (re-scan), every differential has at least one cited section, red flag, if present, in first sentence



## Privacy boundaries

- **raw_input**: stays local; never sent to external API by default
- **derived_output**: stays local; only sharable after explicit user opt-in AND PHI re-scan
- **external_calls**: none by default; external judges require user opt-in
- **hipaa_safe_harbor**: applies — 18 identifier categories are redacted on input

