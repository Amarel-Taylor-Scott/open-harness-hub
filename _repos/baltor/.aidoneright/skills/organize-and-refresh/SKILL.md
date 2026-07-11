---
name: organize-and-refresh
description: Use whenever the multi-repo structure, cross-repo edges, interface contracts, context, or MD/graph files may have drifted — after adding a surface/project, changing the surface-registry, moving docs, or before a release. Regenerates every derived artifact from its single source and reports staleness. The deterministic way to keep the org organized as it grows.
---

# Organize & Refresh

The whole org layout is **derived from one source**: `_repos/dev-rules-context/contracts/surface-registry.json`
(+ each repo's `interface.json` + the code layout). Never hand-edit a derived file — change the source and
refresh. This skill keeps context, graph, interfaces, and MD in sync.

## The one command

```bash
python3 _repos/shared-backend-components/scripts/refresh_all.py --check    # CI gate: fails if any derived artifact is stale
python3 _repos/shared-backend-components/scripts/refresh_all.py --write    # regenerate everything from the single sources
```

`refresh_all` orchestrates the deterministic maintainers in order: interface manifests → per-repo `EDGES.md`
+ the dependency `GRAPH.md` → the cross-repo dependency-law proof → the migration plan + project manifests,
then a staleness scan of the context MD tree.

## When to run

- **After a registry change** (new surface, new project, changed `may_depend_on`/`exposes`) → `--write`, then
  commit the regenerated edges/interfaces/plan with the source change (same commit).
- **After moving/adding context docs** → `--write` to refresh indexes + digests; review any staleness flags.
- **In CI / before release** → `--check` (it must pass green; a stale derived file is a hard failure).

## Rules (inherited standards)

- **Single source of truth** — every edge, interface, count, and plan is computed from the registry; if you
  find yourself hand-editing a `*.EDGES.md`, `interface.json`, `graph.json`, or `MIGRATION-PLAN.md`, stop and
  fix the registry instead (NO-MAGIC-VALUES).
- **The registry is owner/architecture territory** — a new surface or a changed dependency edge is a
  product-structure change; carry a warrant (CHANGE-VERIFICATION), don't add surfaces unilaterally.
- **Move-never-delete** — if the refresh surfaces stale/dead docs, archive them under `archive/legacy/`
  (never delete), then re-run.

## Related tools

- `_repos/edge-graph-generator/generate_repo_edges.py` — per-repo edge digests + the graph.
- `_repos/edge-graph-generator/interface_manifests.py` — versioned interface contracts + relationship check.
- `_repos/edge-graph-generator/check_cross_repo_dependency_law.py` — the boundary proof.
- `_repos/shared-backend-components/scripts/build_migration_plan.py` — the git-subtree split plan + per-project manifests.
- `_repos/shared-backend-components/scripts/find_migration_cleanup_candidates.py` — orphan/duplicate/stale report (move-never-delete).
