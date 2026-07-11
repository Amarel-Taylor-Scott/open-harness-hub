# AGENTS.md — AI Done Right

> Orientation for AI assistants (Claude Code, Cursor, Copilot,
> Windsurf, Aider, Zed, Warp, RooCode, …) opening this repository.

## What this repo is

A specification + content catalog + static site that standardizes how
the modular pieces of an AI-assisted system are described. The hub is
host-agnostic (GitHub Pages, Hugging Face Spaces, Vercel, Netlify,
Cloudflare Pages) and industry-agnostic.

Read [`README.md`](README.md) first, then [`_repos/_shared/taxonomy/SPEC.md`](_repos/_shared/taxonomy/SPEC.md).
For Baltor-specific work, also keep
[`_repos/shared-backend-components/docs/codex/baltor-always-in-memory-context.md`](_repos/shared-backend-components/docs/codex/baltor-always-in-memory-context.md)
loaded as the compact product and architecture anchor.

## Layout — everything lives under `_repos/`

The tree was reorganized: the repo **root** now holds only `_repos/`, the essential meta files
(`README.md`, `LICENSE`, `AGENTS.md`, `CLAUDE.md`, `conftest.py`, `.gitignore`, `.env`, `.aidoneright-root`),
and tooling-hidden dirs tools read from root (`.venv`, `.claude`, `.codex`, `.github`). Every former
top-level dir moved into `_repos/<owner>/`. Authoritative maps: **[`_repos/INDEX.md`](_repos/INDEX.md)**
(surface → landmark files), **[`_repos/MIGRATION-STATUS.md`](_repos/MIGRATION-STATUS.md)** (what moved where),
and **[`_repos/_moved_dirs.json`](_repos/_moved_dirs.json)** (old-name → new `_repos/…` path).

| `_repos/<owner>/` | Holds |
|---|---|
| **`shared-backend-components`** | the substrate + all tooling: `scripts/` (suite runner + every `check_*.py`/`build_*.py`), `architecture/*.json`, `schemas/*.schema.json`, `vocabularies/*.yaml`, `catalog/`, `db/`, `docs/`, `hf-space/`, `rubrics/`, `data/`, `deploy/`, `dist/`, … |
| **`teleon` · `baltor` · `openhubforai` · `aidevobserver` · `aidoneright`** | each product/surface: `backend/src/<x>/`, `frontend/`, `context/`, `EDGES.md`, `interface.json`, `CLAUDE.md`, `README.md` (+ `e2e/` in `baltor`) |
| **`dev-rules-context`** | the devkit: `standards/` `prompts/` `hooks/` `mcp/` `commands/` `skills/` `code-templates/` `templates/` `workflows/` `tests/` |
| **`_shared`** | cross-cutting: `strategy/` `codex/` `concepts/` `research/` `taxonomy/` `_reference/` (local ref repos, NOT republished) `archive/` (lineage) |

**Path convention in the docs below:** a bare `scripts/x.py`, `docs/…`, `architecture/…`, `catalog/…` names the
file under `_repos/shared-backend-components/…`; product code written `src/<x>/…` lives physically at
`_repos/<x>/backend/src/<x>/…` (the `src/<x>/…` form is the canonical, location-stable name used by ids/graph).

## Conventions

- **YAML** for seed/export component definitions. JSON Schema 2020-12 for validation.
- **Python 3.11+** for scripts (though most run on 3.9+ via
  `from __future__ import annotations`).
- **Slug format**: lowercase-with-dashes, ≤ 64 chars.
- **Component IDs**: `{type}/{slug}`. Immutable once published.
- **No version in names or IDs.** Version lives only in the `version` metadata
  field (semver). Never put `-v1`/`-v2`/`v1` in a slug or name. Existing `-v1`
  ids are a careful-migration target (renaming a published id breaks refs, so
  migrate with a CDC/alias, never silently).
- **License**: MIT for code-shaped components; CC-BY-4.0 for data-shaped.
- **Industry tags** are OPEN. Sub-industries are dot-separated
  (`healthcare.radiology`, `finance.aml`).

## Workflow for adding a component

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
4. Re-run `python scripts/validate.py` — every existing component definition must
   still pass.

## Hard rules (load-bearing)

- **A pipeline never wires raw rule packs to a model.** A rule pack
  reaches a model through a harness; this keeps the trust boundary
  explicit.
- **Volatile facts go in tools or knowledge packs, not personas.**
- **Every harness declares `model_targets`, even when the value is
  `none`.**
- **Privacy boundaries travel with the component, not the deployment.**
- **Reproducibility is a first-class field.** Every benchmark
  declares `(commit_sha, dataset_version, run_date)`.
- **No magic values — single source of truth.** Never hand-type a
  value that must be updated in more than one place. Repo-state counts
  and versions are computed, not typed into prose; shared values
  (embedding dimension, model IDs, thresholds, paths, type/row-family
  lists) get one definition and are imported/read everywhere else;
  strings are built from the owning constant, never copied as parallel
  literals. See [`docs/codex/no-magic-values.md`](_repos/shared-backend-components/docs/codex/no-magic-values.md).

## Do not

- Do not republish anything under `_reference/`. Those are upstream
  reference repos cloned for offline study only.
- Do not commit real PII in sample data. Composite/synthetic only.
- Do not introduce industry-specific concepts as top-level taxonomy
  entries. Model them as leaf instances of generic types
  (see SPEC §4).
- Do not delete `_inbox/` drafts without curator review.
