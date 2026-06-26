---
title: OpenHubForAI Playground
emoji: 🧩
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 4.40.0
app_file: app.py
pinned: false
license: mit
short_description: Browse and run harnesses + pipelines from the OpenHubForAI catalog.
---

# OpenHubForAI — Playground

Pick any pipeline from the [OpenHubForAI](https://github.com/TaylorAmarelTech/open-harness-hub)
catalog, plug in sample data, and watch the DAG execute step-by-step.
This Space reads pipelines directly from the catalog at runtime.

## Catalog state

Snapshot at last Space build (auto-updated by CI):

- **adapter**: 33
- **benchmark**: 111
- **dataset**: 205
- **harness**: 195
- **knowledge-pack**: 427
- **logic-pack**: 2
- **pattern**: 59
- **persona**: 233
- **pipeline**: 417
- **processor**: 176
- **rubric**: 245
- **rule-pack**: 402
- **tool**: 173

**Total components**: 2678.

## Run locally

```bash
pip install -r requirements.txt
python app.py
# open http://127.0.0.1:7860
```

## Switching the model

The app honors:

- `OH_MODEL` (default `simulated`; set to `ollama/llama3.1:8b` or any
  OpenAI-compatible endpoint).
- `OPENAI_API_KEY` for OpenAI-compatible adapters.
- `ANTHROPIC_API_KEY` for the Anthropic judge.

Without a model configured, the app runs in **simulate mode**: every
harness/tool step returns a stub so you still see the shape of the
trace.

## Adding a new pipeline

Open a PR against the main repo with a new manifest under
`catalog/pipelines/...`. After it merges, CI rebuilds this Space and
the pipeline appears in the dropdown automatically.
