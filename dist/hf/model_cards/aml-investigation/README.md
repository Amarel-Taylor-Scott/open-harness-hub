---
license: MIT
tags:
- classification
- experimental
- finance
- finance.aml
- open-harness-hub
- reasoning
- safety_gating
- structured
- text
- tool_use
- verification
library_name: open-harness-hub
pipeline_tag: text-classification
language:
- en
region:
- finance
- finance.aml
---

# AML Investigation

<!-- Generated from Open Harness Hub manifest `harness/aml-investigation` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Harness for AML suspicious-transaction review. Composes the
AML-analyst persona, sanctions-screening heuristic, FATF-typology
classifier, financial-PII privacy gate, FATF-typology RAG,
sanctions-check tool, transaction-graph-query tool, and a
citation-first response policy. Output is a SAR-style narrative
draft and a structured risk score; never a SAR filing.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `grep` layer
- `classifier` layer
- `heuristic` layer
- `rag` layer
- `tools` layer
- `privacy` layer

**Industries**: finance, finance.aml
**Capabilities**: reasoning, classification, verification, tool_use, safety_gating
**Modalities**: text, structured
**Trust boundary**: local

## How the harness runs

### Review a transaction bundle and produce a SAR-style narrative draft

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

## Privacy boundaries

- **raw_input**: stays inside the institution's perimeter
- **derived_output**: narrative + risk score may be shared with the BSA officer; never with external systems by default
- **external_calls**: external judge / LLM call only after explicit BSA-officer opt-in

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `local_ollama` | `ollama` | local |
| `self_hosted` | `openai_compatible` | local |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{aml-investigation_open_harness_hub,
  title  = {AML Investigation},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/aml-investigation},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub artifact: `harness/aml-investigation`.
