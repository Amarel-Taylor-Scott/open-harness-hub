# Taedri repo split — executed 2026-07-12

**Status: DONE.** `aidonerightcorp/taedri` (private) is the **direct development home** for the Taedri product
(hosted capability retrieval: remote MCP + agent API + web app + billing seam, serving taedri.dev on Fly app
`taedri`). It is fully standalone: clone it into a fresh folder, open in VS Code, and develop — no monorepo
checkout required. In-repo orientation: its root `CLAUDE.md` (agent context) and `DEVELOPMENT.md` (5-minute
setup). Warrant: owner 2026-07-12 — "get ready to split this project off into its own repo (separate from the
other projects)" / "create a new VS Code project folder, sync up with the repo, and start programming from
there".

## The boundary

| Side | Owns |
|---|---|
| `aidonerightcorp/taedri` | Gateway/server code as deployed, designed web screens, deploy shape (Dockerfile, fly.toml, 4 workflows), runbooks, the **served** corpus snapshot (search index + card files, gzipped in git) |
| monorepo (`_repos/shared-backend-components`) | The **factory** that generates and improves the corpus (foundry loops, kernel packs, benchmarks, promotion gates) and the bundle builder that originally assembled the repo |

**Layout is FLAT since 2026-07-12 (owner request: "everything contained in taedri.dev"):** the taedri repo
root IS the code root — `scripts/`, `catalog/`, `data/`, `web/`, `schemas/`, `vocabularies/`,
`architecture/` at top level (commit `be8ac33`, 2,731 history-preserving renames). A small `_repos/`
support folder remains for the two libraries the gateway imports (`openhubforai` auth kit, `teleon` ids)
plus `_moved_dirs.json` (entries rewritten to flat paths); `.aidoneright-root` anchors `repo_root()` at the
repo root. **Path mapping for PRs from the monorepo:** monorepo `_repos/shared-backend-components/<path>`
→ taedri `<path>` (strip the prefix). Verified before ship: both self-tests PASS from the flat root, and a
local docker build + container smoke served /health + the 557,439 count.

## The freeze (enforced in code, not prose)

`scripts/build_capability_saas_bundle.py --push-github` **force-replaces the entire remote history**. Since the
split, `push_github` refuses when the remote `main` already exists (`bundle_push_freeze_reason`, self-tested on
both branches); the deliberate-overwrite escape hatch is `TAEDRI_BUNDLE_OVERWRITE=1`. Never use the escape hatch
to "sync" — direct edits now live in that repo and an overwrite deletes them.

## Refreshing the served corpus after the split (PR, never overwrite)

1. In the monorepo: regenerate the corpus artifacts (index + card files) with the usual factory lanes;
   `python3 scripts/build_capability_saas_bundle.py --build` refreshes `dist/capability-saas-deploy/` locally
   (gitignored here — GitHub is the tracked home).
2. In a taedri-repo **branch**: copy the changed corpus files in (same paths), commit, open a PR.
3. Review + merge → `fly-deploy` ships it. If a `/data/serving_index.json` exists from an admin reindex, re-run
   the reindex (or remove it) so the volume copy does not shadow the new image corpus.

## Deploy shape facts (learned from receipts, do not relearn)

- Fly caps **shared-CPU memory at 2048 MiB × cpus**: `8gb` requires `cpus = 4`. `cpus = 2` + `8gb` fails every
  machine update (`invalid config.guest.memory_mb`, run 29172275598, 2026-07-11) while health checks stay green
  on the OLD release — a deploy can "succeed" as a build and silently never install.
- 8gb is a **measured** requirement: serving + full-corpus admin reindex starved a 4gb box (critical health,
  27s responses, 2026-07-11). `auto_stop_machines` keeps the larger VM billed only while awake.
- The public primitive counter is computed (`/v1/stats/domains` ← index `manifest.json n_docs`); screen mocks
  contain specimen literals that the wire script overrides client-side — a raw-HTML grep shows the specimen,
  not what users see.
