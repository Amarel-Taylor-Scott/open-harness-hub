---
license: MIT
tags:
- climate
- compliance
- esg
- esg.csrd
- evaluation
- experimental
- gri
- harness
- issb
- open-harness-hub
- reasoning
- retrieval
- sasb
- structured
- sustainability
- tcfd
- text
- verification
library_name: open-harness-hub
pipeline_tag: text-generation
language:
- en
region:
- esg
- esg.csrd
- sustainability
- climate
- compliance
---

# ESG pillar (E / S / G) deep-dive review harness

<!-- Generated from Open Harness Hub manifest `harness/esg-pillar-review` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Wraps the ESG pillar deep-dive review flow as a reusable harness.
Reviews ONE pillar (E, S, or G) at SASB + ISSB + TCFD + GRI depth,
cross-checks against greenwashing rule pack, and emits framework-
coded findings with disclosure-code citations.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `grep` layer
- `rag` layer
- `tools` layer

**Industries**: esg, esg.csrd, sustainability, climate, compliance
**Capabilities**: evaluation, verification, retrieval, reasoning
**Modalities**: text, structured
**Trust boundary**: local

## How the harness runs

### disclosure + pillar (E|S|G) → industry SASB topics → framework alignment → greenwashing scan → grade

1. classify company into SICS industry
2. fetch SASB industry-specific material topics for pillar
3. fire greenwashing GREP pack
4. RAG against SASB+GRI+TCFD+ISSB pack per material topic
5. judge per esg-pillar-depth-v1 rubric
6. propose specific drafting fixes per gap
7. emit audit trace

## Privacy boundaries

- **raw_input**: stays local; disclosure text is usually public
- **derived_output**: may sync to hub
- **external_calls**: only on explicit user opt-in

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
@misc{esg-pillar-review_open_harness_hub,
  title  = {ESG pillar (E / S / G) deep-dive review harness},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/esg-pillar-review},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/esg-pillar-review`.
