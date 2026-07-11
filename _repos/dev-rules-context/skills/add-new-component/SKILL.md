---
name: add-new-component
description: Use when adding a new product SURFACE, a new PROJECT under an existing surface, or a new repo to the org — so a new hire never hand-edits 12 derived files. Appends ONE entry to the single-source registry, scaffolds the repo folder ADD-ONLY, then refreshes every derived artifact. The registry is the source; edges/graph/interfaces/plan are computed from it.
---

# Add a New Component

Adding a surface/project/repo is **three deterministic moves**, none of them hand-editing a derived
file. `_repos/shared-backend-components/scripts/scaffold_component.py` does all three in one command, reading the single source of truth
(`_repos/dev-rules-context/contracts/surface-registry.json` + each repo's `interface.json` + the code
layout) and reusing the org's existing tools — it never re-implements the dependency law or writes a
derived file itself.

## The one command

```bash
# always prove the logic offline first (synthetic registry in a temp dir; no real writes):
python3 _repos/shared-backend-components/scripts/scaffold_component.py --self-test

# dry run — prints the plan (append + scaffold) without touching disk:
python3 _repos/shared-backend-components/scripts/scaffold_component.py --name <name> --kind <kind> --may-depend-on <a> <b> --exposes <cap> <cap>

# perform it (append to registry + ADD-ONLY scaffold + refresh_all):
python3 _repos/shared-backend-components/scripts/scaffold_component.py --name <name> --kind <kind> --may-depend-on <a> <b> --exposes <cap> --write
```

Add a **PROJECT** under an existing surface instead of a new surface:

```bash
python3 _repos/shared-backend-components/scripts/scaffold_component.py --under-surface <surface> --name <project> --kind <backend|frontend|microservice> \
  --code-path <src/path/in/monorepo> --consumes-projects <sibling> --write
```

## What it does (in order)

1. **APPEND** one entry to the single source of truth — `surfaces.<name>` (or
   `surfaces.<s>.projects.<p>`). Never a second copy of a name/edge anywhere.
2. **SCAFFOLD** `_repos/<name>/` ADD-ONLY from the shared component template
   (`context/blackbox.md` + `context/edges.md`) plus a `README.md` and a starter `interface.json`
   computed from the just-appended entry. Never clobbers an existing entry or file.
3. **REFRESH** — runs `_repos/shared-backend-components/scripts/refresh_all.py --write` so edges, the dependency graph, interface
   manifests, and the migration plan are all regenerated from the new source of truth.

## Rules (inherited standards)

- **Single source of truth** — the registry is the ONLY place a surface/project/edge is declared;
  everything else is derived. Never hand-edit `*.EDGES.md`, `interface.json`, `graph.json`, or
  `MIGRATION-PLAN.md` (NO-MAGIC-VALUES; no hardcoded surface/repo names in logic).
- **Warrant before a registry change** — a new surface or a changed `may_depend_on` edge is a
  product-structure change: carry clear owner intent (CHANGE-VERIFICATION), never a unilateral call.
- **Dependency law holds** — the new edge must respect Baltor → Teleon → OpenHubForAI (never the
  reverse); the tool validates it against `check_cross_repo_dependency_law` before writing, and
  refuses an illegal edge.
- **ADD-ONLY** — the scaffold only creates new files; move-never-delete for anything it supersedes.
- **Commit together** — commit the registry append + the regenerated derived files in the SAME commit.

## Verify

After `--write`, prove the org is back in sync (a stale derived file is a hard failure):

```bash
python3 _repos/shared-backend-components/scripts/check_org_freshness.py && python3 _repos/shared-backend-components/scripts/refresh_all.py --check
```

## Related tools

- `_repos/shared-backend-components/scripts/refresh_all.py` — the derived-artifact orchestrator scaffold_component calls after appending.
- `_repos/edge-graph-generator/interface_manifests.py` — the manifest shape it reuses.
- `_repos/edge-graph-generator/check_cross_repo_dependency_law.py` — the boundary proof it validates against.
- `skills/check-organization` — the pre-release drift gate.
