---
name: aml-investigation
description: Harness for AML suspicious-transaction review. Composes the AML-analyst
  persona, sanctions-screening heuristic, FATF-typology classifier, financial-PII
  privacy gate, FATF-typology RAG, sanctions-check tool, transaction-graph-query tool,
  and a citation-first response policy. Output is a SAR-style narrative draft and
  a structured risk score; never a SAR filing.
when_to_use: Use when the user needs reasoning. Use when the user needs classification.
  Use when the user needs verification. Use when the user needs tool_use. Use when
  the user needs safety_gating. Particularly relevant for finance. Particularly relevant
  for finance.aml.
---

# AML Investigation

Harness for AML suspicious-transaction review. Composes the
AML-analyst persona, sanctions-screening heuristic, FATF-typology
classifier, financial-PII privacy gate, FATF-typology RAG,
sanctions-check tool, transaction-graph-query tool, and a
citation-first response policy. Output is a SAR-style narrative
draft and a structured risk score; never a SAR filing.

## Applied layers

- `persona`
- `grep`
- `classifier`
- `heuristic`
- `rag`
- `tools`
- `privacy`

## Review a transaction bundle and produce a SAR-style narrative draft

*model_call:* `required`

**Steps**

1. redact financial PII (rule-pack/financial-pii-en)
2. sanctions screen (rule-pack/sanctions-screening) — if hit, halt routine review and escalate
3. query transaction graph 2-hops (tool/transaction-graph-query)
4. score against FATF typologies (rule-pack/aml-typologies-fatf)
5. retrieve FATF typology RAG sections
6. compose persona + retrieved context + tool results + structured graph
7. call model
8. produce structured findings: typology matches, supporting evidence, escalation path
9. draft SAR-style narrative; never a final SAR
10. verify every claim cited

**Verification**

- no financial PII in output
- sanctions hit, if present, halts routine output and routes to escalation procedure
- every typology match cites at least one FATF section and one transaction edge

## Privacy boundaries

- **raw_input**: stays inside the institution's perimeter
- **derived_output**: narrative + risk score may be shared with the BSA officer; never with external systems by default
- **external_calls**: external judge / LLM call only after explicit BSA-officer opt-in

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `self_hosted` | `openai_compatible` | local | False | False |

## Provenance

- Hub artifact: `harness/aml-investigation` v0.1.0
- License: `MIT`
- Lifecycle: `experimental`
- Full source manifest: see `references/manifest.yaml`
