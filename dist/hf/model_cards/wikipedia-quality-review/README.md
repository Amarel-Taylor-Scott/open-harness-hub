---
license: MIT
tags:
- blp
- education
- evaluation
- experimental
- extraction
- harness
- media
- media.editorial
- media.factcheck
- npov
- open-harness-hub
- or
- retrieval
- rs
- text
- v
- verification
- wikipedia
library_name: open-harness-hub
pipeline_tag: token-classification
language:
- en
region:
- media
- media.editorial
- media.factcheck
- education
---

# Wikipedia article quality review harness

<!-- Generated from OpenHubForAI manifest `harness/wikipedia-quality-review` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Wraps the Wikipedia-quality review flow as a reusable harness with
persona + GREP + RAG + tools layers. Reviews an article (or draft)
against the four core content policies + style/structure rubric and
emits structured per-claim findings with WP-policy citation.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `grep` layer
- `rag` layer
- `tools` layer

**Industries**: media, media.editorial, media.factcheck, education
**Capabilities**: evaluation, verification, retrieval, extraction
**Modalities**: text
**Trust boundary**: local

## How the harness runs

### article text → quality flags → policy RAG → grade + edit suggestions

1. fetch article wikitext (or accept inline)
2. extract claims + sources
3. fire WP-quality GREP pack
4. RAG against WP-policy pack per flag category
5. verify a sample of citations against the cited text
6. judge per wikipedia-article-quality-v1 rubric
7. propose per-finding edits (tag / rewrite / remove)
8. emit audit trace

## Privacy boundaries

- **raw_input**: stays local; article text is public
- **derived_output**: may sync to hub
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
@misc{wikipedia-quality-review_open_harness_hub,
  title  = {Wikipedia article quality review harness},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/harness/wikipedia-quality-review},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/wikipedia-quality-review`.
