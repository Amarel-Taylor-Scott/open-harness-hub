---
license: MIT
tags:
- evaluation
- experimental
- government
- government.regulatory
- harness
- interpretation
- law
- legal
- legal.compliance
- open-harness-hub
- reasoning
- retrieval
- statute
- text
- verification
library_name: open-harness-hub
pipeline_tag: text-generation
language:
- en
region:
- legal
- legal.compliance
- government
- government.regulatory
---

# Statute / regulation clarity review harness

<!-- Generated from OpenHubForAI manifest `harness/statute-clarity-review` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Wraps the statute-clarity review flow as a reusable harness with
persona + GREP + RAG + tools layers. Targets local-Ollama or
Anthropic/OpenAI for the judge model arm. Emits citation-first
findings tagged with canon name, severity, suggested redline, and
cited authority.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `grep` layer
- `rag` layer
- `tools` layer

**Industries**: legal, legal.compliance, government, government.regulatory
**Capabilities**: evaluation, verification, retrieval, reasoning
**Modalities**: text
**Trust boundary**: local

## How the harness runs

### statute text → ambiguity flags → canon analysis → grade + redlines

1. normalize statute text + extract section structure
2. fire ambiguity GREP pack
3. RAG against canons-of-construction pack
4. judge per statute-clarity-v1 rubric
5. propose smallest-fix redlines per finding
6. emit audit trace

## Privacy boundaries

- **raw_input**: stays local to the running pipeline
- **derived_output**: may sync to hub if statute text is public-law
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `local_ollama` | `ollama` | local |
| `anthropic_judge` | `anthropic` | external |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{statute-clarity-review_open_harness_hub,
  title  = {Statute / regulation clarity review harness},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/harness/statute-clarity-review},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/statute-clarity-review`.
