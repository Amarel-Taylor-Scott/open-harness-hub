# Playground & sample runs

Pipelines should be **viewable** and **runnable** with sample data so
visitors can build intuition before installing anything. The catalog
supports three levels of interactivity:

## 1. Static catalog page (always available)

The MkDocs site renders each manifest as a browsable page with:

- description
- primitives it consumes / emits
- step-by-step diagram
- embedded sample-run output

No execution; safe on GitHub Pages.

## 2. Pre-rendered sample run (always available)

Each pipeline ships with one or more `samples/<scenario>.json` files
next to its manifest. The file is a frozen input, the deterministic
outputs of each step, and the final output. These are committed to
git and rendered inline on the static catalog page.

```json
{
  "pipeline":   "pipeline/research-entity",
  "scenario":   "company-acme",
  "inputs":    { "entity_name": "Acme Corp", "entity_kind": "company" },
  "steps": [
    { "step_id": "redact_query", "harness": "harness/redact-pii-text",
      "input":  { "text": "Acme Corp" },
      "output": { "redacted_text": "Acme Corp", "audit": [] },
      "ms": 4 }
  ],
  "output":    { "profile_markdown": "...", "citations": [] },
  "model":     "ollama/llama3.1:8b",
  "frozen_at": "2026-05-19T12:00:00Z",
  "license":   "MIT"
}
```

A pipeline with no sample-run committed cannot be marked `stable`.

## 3. Live playground (where the host allows execution)

A Gradio app under `hf-space/` loads a pipeline manifest, accepts user
input, runs the pipeline against a configured model adapter, and shows
the layer-by-layer trace. The same app works locally
(`python hf-space/app.py`) and deploys to Hugging Face Spaces or any
Docker host.

Run locally:

```bash
pip install -r hf-space/requirements.txt
python hf-space/app.py
# open http://127.0.0.1:7860
```

The playground reads the catalog directly - no preprocessing, no
generation step. Edit a manifest, save, refresh.
