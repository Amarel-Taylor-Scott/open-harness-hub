#!/usr/bin/env python3
"""Emit a Hugging Face Space README.md for the Gradio playground.

The hub already ships hf-space/README.md with the canonical
frontmatter. This emitter regenerates it from a single source of truth
so all metadata stays in sync with the catalog.

Output: dist/hf/space/README.md  (mirrors hf-space/README.md)
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.emit._lib import DIST, load_catalog  # noqa: E402


SPACE_FRONT = {
    "title":       "Open Harness Hub Playground",
    "emoji":       "🧩",
    "colorFrom":   "blue",
    "colorTo":     "gray",
    "sdk":         "gradio",
    "sdk_version": "4.40.0",
    "app_file":    "app.py",
    "pinned":      False,
    "license":     "mit",
    "short_description": "Browse and run harnesses + pipelines from the Open Harness Hub catalog.",
}


def render() -> str:
    catalog = load_catalog()
    counts: dict[str, int] = {}
    for _, m in catalog.items():
        path = m[0]      # not used here
        manifest = m[1]
        counts[manifest["type"]] = counts.get(manifest["type"], 0) + 1
    total = sum(counts.values())

    front = SPACE_FRONT.copy()
    front_yaml = yaml.safe_dump(front, sort_keys=False, allow_unicode=True).strip()

    counts_lines = "\n".join(
        f"- **{t}**: {n}" for t, n in sorted(counts.items())
    )

    return f"""---
{front_yaml}
---

# Open Harness Hub — Playground

Pick any pipeline from the [Open Harness Hub](https://github.com/TaylorAmarelTech/open-harness-hub)
catalog, plug in sample data, and watch the DAG execute step-by-step.
This Space reads pipelines directly from the catalog at runtime.

## Catalog state

Snapshot at last Space build (auto-updated by CI):

{counts_lines}

**Total artifacts**: {total}.

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
"""


def main() -> int:
    out_dir = DIST / "hf" / "space"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    (out_dir / "README.md").write_text(render())
    print("wrote dist/hf/space/README.md")
    print("  copy with: cp dist/hf/space/README.md hf-space/README.md")
    print("  then push hf-space/ to your HF Space repo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
