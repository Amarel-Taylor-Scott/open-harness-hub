---
license: MIT
tags:
- ai
- classification
- cross_industry
- experimental
- extraction
- generation
- harness
- ingestion
- manifest-author
- meta
- open-harness-hub
- reasoning
- self-revise
- software
- software.docs
- structured
- text
- verification
library_name: open-harness-hub
pipeline_tag: text-classification
language:
- en
region:
- software
- software.docs
- ai
- cross_industry
---

# Draft-manifest authoring harness (knowledge-node → manifest)

<!-- Generated from OpenHubForAI manifest `harness/draft-manifest-author` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Wraps the manifest-authoring flow as a reusable harness. Reads a
structured knowledge node (from any walker: Wikipedia / USC /
APQC PCF / NIST framework / etc.), drafts one or more catalog
manifests, runs them through the YAML emitter + validator loop,
and produces ready-for-curator-review drafts in `catalog/_inbox/`.

Includes self-revise loop: on validation failure, the harness
receives the structured error report and revises the draft up to
N_max_revisions times before failing the node.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `rag` layer
- `tools` layer

**Industries**: software, software.docs, ai, cross_industry
**Capabilities**: generation, extraction, verification, classification, reasoning
**Modalities**: text, structured
**Trust boundary**: local

## How the harness runs

### knowledge node → proposed manifest types → draft YAML → validate → revise loop → write _inbox

1. classify node into proposed manifest target types (1-3)
2. RAG against manifest-shapes-and-conventions pack for canonical examples
3. draft each proposed manifest as a Python dict
4. self-grade against draft-manifest-quality-v1 rubric
5. emit each draft via draft-manifest-yaml-emitter
6. on validation failure: revise (max 3 attempts) using the structured error report
7. on success: write to catalog/_inbox/; emit audit trace

## Privacy boundaries

- **raw_input**: stays local; source content is usually public
- **derived_output**: draft manifests stay in _inbox/ until curator promotes
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
@misc{draft-manifest-author_open_harness_hub,
  title  = {Draft-manifest authoring harness (knowledge-node → manifest)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/harness/draft-manifest-author},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/draft-manifest-author`.
