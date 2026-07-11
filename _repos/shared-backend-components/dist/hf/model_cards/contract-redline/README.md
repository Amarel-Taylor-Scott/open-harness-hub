---
license: MIT
tags:
- beta
- contract
- evaluation
- extraction
- harness
- legal
- legal.compliance
- legal.contract
- open-harness-hub
- playbook
- reasoning
- redline
- text
- verification
library_name: open-harness-hub
pipeline_tag: token-classification
language:
- en
region:
- legal
- legal.contract
- legal.compliance
---

# Contract Clause Redlining harness

<!-- Generated from OpenHubForAI manifest `harness/contract-redline` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Playbook-cite-first harness for commercial contract review. Surfaces
red-flag clauses + proposes concrete redline language + cites the
playbook clause family for every finding.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `privacy` layer
- `grep` layer
- `rag` layer
- `tools` layer

**Industries**: legal, legal.contract, legal.compliance
**Capabilities**: evaluation, extraction, verification, reasoning
**Modalities**: text
**Trust boundary**: local

## How the harness runs

### contract → red flags → playbook citations → redline proposals

1. structured-to-prose
2. PII redact
3. contract-red-flags GREP
4. RAG against contract-law-clauses playbook
5. judge against contract-review-quality rubric
6. emit suggested redline language per finding
7. audit trace

## Privacy boundaries

- **raw_input**: stays local; subject to attorney-client privilege
- **derived_output**: may sync to hub only with explicit privilege waiver
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `local_ollama` | `ollama` | local |
| `anthropic_opus` | `anthropic` | external |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{contract-redline_open_harness_hub,
  title  = {Contract Clause Redlining harness},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/harness/contract-redline},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/contract-redline`.
