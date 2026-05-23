# AGENTS.md — Open Harness Hub

> Orientation for AI assistants (Claude Code, Cursor, Copilot,
> Windsurf, Aider, Zed, Warp, RooCode, …) opening this repository.

## What this repo is

A specification + content catalog + static site that standardizes how
the modular pieces of an AI-assisted system are described. The hub is
host-agnostic (GitHub Pages, Hugging Face Spaces, Vercel, Netlify,
Cloudflare Pages) and industry-agnostic.

Read [`README.md`](README.md) first, then [`taxonomy/SPEC.md`](taxonomy/SPEC.md).

## Layout

```
.
├── taxonomy/SPEC.md          # canonical specification (read first)
├── schemas/*.schema.json     # JSON Schemas for every artifact type
├── vocabularies/*.yaml       # controlled vocabularies (industries, capabilities, …)
├── catalog/                  # the actual content
│   ├── harnesses/<slug>.yaml
│   ├── pipelines/<kind>/<slug>.yaml
│   ├── rule-packs/<family>/<slug>.yaml
│   ├── knowledge-packs/<slug>.yaml
│   ├── tools/<slug>.yaml
│   ├── personas/<slug>.yaml
│   ├── adapters/<slug>.yaml
│   ├── rubrics/<slug>.yaml
│   └── _inbox/               # draft manifests pending curator review
├── db/
│   ├── postgres/schema.sql   # canonical relational schema
│   ├── mongodb/collections.md
│   ├── redis/keys.md
│   └── vector/spec.md
├── scripts/
│   ├── validate.py           # JSON Schema + ref + vocab validation
│   ├── build_catalog_pages.py# render manifests into docs/catalog/*.md
│   ├── run_pipeline.py       # minimal pipeline runner with --simulate
│   ├── new.py                # scaffold a new manifest
│   └── mine_kaggle_harnesses.py
├── hf-space/
│   ├── app.py                # Gradio playground
│   ├── Dockerfile
│   └── README.md             # HF Space frontmatter
├── docs/                     # MkDocs source (rendered to site/)
├── .github/workflows/
│   ├── pages.yml             # GitHub Pages deploy
│   └── validate.yml          # PR validation
├── mkdocs.yml
├── vercel.json
├── netlify.toml
├── _headers / _redirects
└── _reference/               # local reference repos; NOT republished
```

## Conventions

- **YAML** for manifests. JSON Schema 2020-12 for validation.
- **Python 3.11+** for scripts (though most run on 3.9+ via
  `from __future__ import annotations`).
- **Slug format**: lowercase-with-dashes, ≤ 64 chars.
- **Artifact IDs**: `{type}/{slug}`. Immutable once published.
- **License**: MIT for code-shaped artifacts; CC-BY-4.0 for data-shaped.
- **Industry tags** are OPEN. Sub-industries are dot-separated
  (`healthcare.radiology`, `finance.aml`).

## Workflow for adding an artifact

```bash
python scripts/new.py harness my-new-thing
$EDITOR catalog/harnesses/my-new-thing.yaml
python scripts/validate.py
python scripts/build_catalog_pages.py
```

## Workflow for changing the taxonomy

1. Open a PR that edits `taxonomy/SPEC.md`.
2. Update the corresponding `schemas/*.schema.json`.
3. Add or update entries in `vocabularies/`.
4. Re-run `python scripts/validate.py` — every existing manifest must
   still pass.

## Hard rules (load-bearing)

- **A pipeline never wires raw rule packs to a model.** A rule pack
  reaches a model through a harness; this keeps the trust boundary
  explicit.
- **Volatile facts go in tools or knowledge packs, not personas.**
- **Every harness declares `model_targets`, even when the value is
  `none`.**
- **Privacy boundaries travel with the artifact, not the deployment.**
- **Reproducibility is a first-class field.** Every benchmark
  declares `(commit_sha, dataset_version, run_date)`.

## Do not

- Do not republish anything under `_reference/`. Those are upstream
  reference repos cloned for offline study only.
- Do not commit real PII in sample data. Composite/synthetic only.
- Do not introduce industry-specific concepts as top-level taxonomy
  entries. Model them as leaf instances of generic types
  (see SPEC §4).
- Do not delete `_inbox/` drafts without curator review.
