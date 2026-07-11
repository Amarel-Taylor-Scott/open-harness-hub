# Repository organization — status

**Everything is physically organized under `_repos/`.** The repo root holds only `_repos/` + essential meta
(`README.md`, `LICENSE`, `AGENTS.md`, `CLAUDE.md`, `conftest.py`, `.git`, `.gitignore`, `.env`, `.aidoneright-root`)
+ tooling dirs tools must read from root (`.venv`, `.claude`, `.codex`, `.github`). No compat symlinks remain at the
root — the earlier symlink bridges were removed and the real dirs moved into `_repos/` in full.

## Layout

| `_repos/<owner>/` | Holds |
|---|---|
| `shared-backend-components` | `scripts/` (the suite runner + all tooling), `architecture/` `schemas/` `vocabularies/` `catalog/` `data/` `db/` `deploy/` `docs/` `dist/` `experiments/` `local_emulators/` `media/` `pipelines/` `services/` `rubrics/` `fly/` `infra/` `demo-data/` `hf-space/`. **No product `backend/`** — each backend's code lives in its own product folder at `_repos/<x>/backend/src/<x>/` (see the products row below); the location-stable `src/<x>/` name used by ids + the code graph maps to that physical path. |
| `teleon` `baltor` `openhubforai` `aidevobserver` `aidoneright` | each product: `backend/src/<x>/`, `frontend/`, `context/` (its docs), `EDGES.md`, `interface.json`, `CLAUDE.md`, `README.md` (+ `e2e/` in `baltor`) |
| `dev-rules-context` | the devkit: `standards/` `prompts/` `hooks/` `mcp/` `commands/` `skills/` `code-templates/` `templates/` `workflows/` `editor/` `tests/` |
| `_shared` | cross-cutting: `strategy/` `codex/` `concepts/` `research/` `notes/` `meta/` `taxonomy/` `_reference/` (embedded ref repos) `archive/` (lineage) |
| `_generated` | build/vendored output kept out of the working tree: `node_modules` `.agent` `generated` `site` `artifacts` `generated_primitive_packs` `manual_source_materials` `scratchpad` |

## Consequences (the content-review is fixing these)

- **Doc path citations** that named old root paths (`scripts/x.py`, `src/teleon/…`, `docs/…`, `architecture/…`)
  no longer resolve at root — they moved under `_repos/`. A repoint pass is underway.
- **Doc-bridge symlinks** (component `context/` surfaced into `docs/architecture` etc.) were re-verified: 41 that
  dangled after the moves are now repointed; 0 broken remain.
- **Background factory loops** (`flywheel_orchestrator --forever`, foundry daemon, verification loop) were stopped;
  they had been recreating `data/` at root.

## For the eventual GitHub split (optional)

`git subtree split -P _repos/<repo> -b split/<repo>` still produces a standalone repo per surface (files at that
repo's root). `scripts/split_repos_for_github.sh` runs it for all. Not required for the local organization above.
