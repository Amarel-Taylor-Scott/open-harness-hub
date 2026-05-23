---
title: Open Harness Hub Playground
emoji: 🧩
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 4.40.0
app_file: app.py
pinned: false
license: mit
short_description: Browse and run harnesses + pipelines from the Open Harness Hub
  catalog.
---

# Open Harness Hub — Playground

Pick any pipeline from the [Open Harness Hub](https://github.com/TaylorAmarelTech/open-harness-hub)
catalog, plug in sample data, and watch the DAG execute step-by-step.
This Space reads pipelines directly from the catalog at runtime.

## Catalog state

Snapshot at last Space build (auto-updated by CI):

- **adapter**: 9
- **benchmark**: 1
- **dataset**: 3
- **harness**: 5
- **knowledge-pack**: 19
- **pattern**: 22
- **persona**: 13
- **pipeline**: 36
- **processor**: 39
- **rubric**: 11
- **rule-pack**: 20
- **tool**: 6

**Total artifacts**: 184.

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
