# AML Investigation

*harness* · `harness/aml-investigation` · v0.1.0 · experimental

Harness for AML suspicious-transaction review. Composes the
AML-analyst persona, sanctions-screening heuristic, FATF-typology
classifier, financial-PII privacy gate, FATF-typology RAG,
sanctions-check tool, transaction-graph-query tool, and a
citation-first response policy. Output is a SAR-style narrative
draft and a structured risk score; never a SAR filing.

| axis | value |
|---|---|
| industry | finance, finance.aml |
| capability | reasoning, classification, verification, tool_use, safety_gating |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |

**Consumes:** `persona_block`, `grep_rule`, `classifier_rule`, `heuristic_rule`, `rag_doc`, `tool_definition`, `entity_signal`

**Emits:** `reasoning_step`, `extracted_fact`, `modus_operandi`, `audit_template`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `self_hosted` | `openai_compatible` | local | False | False |

## Logic paths

### Review a transaction bundle and produce a SAR-style narrative draft  
*model_call: `required`*

1. redact financial PII (rule-pack/financial-pii-en)
1. sanctions screen (rule-pack/sanctions-screening) — if hit, halt routine review and escalate
1. query transaction graph 2-hops (tool/transaction-graph-query)
1. score against FATF typologies (rule-pack/aml-typologies-fatf)
1. retrieve FATF typology RAG sections
1. compose persona + retrieved context + tool results + structured graph
1. call model
1. produce structured findings: typology matches, supporting evidence, escalation path
1. draft SAR-style narrative; never a final SAR
1. verify every claim cited

**consumes:** `persona_block`, `grep_rule`, `classifier_rule`, `heuristic_rule`, `rag_doc`, `tool_definition`, `entity_signal`

**emits:** `reasoning_step`, `extracted_fact`, `modus_operandi`, `audit_template`

**verification:** no financial PII in output, sanctions hit, if present, halts routine output and routes to escalation procedure, every typology match cites at least one FATF section and one transaction edge



## Privacy boundaries

- **raw_input**: stays inside the institution's perimeter
- **derived_output**: narrative + risk score may be shared with the BSA officer; never with external systems by default
- **external_calls**: external judge / LLM call only after explicit BSA-officer opt-in

