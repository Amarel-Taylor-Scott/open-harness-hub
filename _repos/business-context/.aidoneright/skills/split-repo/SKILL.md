---
name: split-repo
description: Use when extracting a project out of the monorepo into its own GitHub repo WITH history — a surface graduating to a standalone repo, or a project splitting off. Builds the history-preserving git-subtree plan from the registry, installs the shared devkit, and keeps every inherited gate green. The working monorepo never breaks; split repo-by-repo, in order.
---

# Split a Project into Its Own Repo

Every project's code stays in the monorepo and **works until split**. Extraction uses
`git subtree split --prefix=<code_path>` which produces a branch carrying that subtree's full history,
ready to push to a new repo. The order + exact commands are **computed from the registry** by
`_repos/shared-backend-components/scripts/build_migration_plan.py` — never hand-write them.

## Generate the plan

```bash
python3 _repos/shared-backend-components/scripts/build_migration_plan.py --self-test   # prove the plan logic offline first
python3 _repos/shared-backend-components/scripts/build_migration_plan.py --write        # write MIGRATION-PLAN.md + json + per-project manifests
```

This emits, from the single-source registry:
- **`MIGRATION-PLAN.md`** — the ordered list of repos with the exact per-project git-subtree commands.
- a **package manifest per project** (`pyproject.toml` for python, `package.json` for a frontend/client)
  declaring the shared devkit + sibling deps, so each component is self-describing.
- extraction **order**: shared devkit first → substrate/microservices → open spec → backends → frontends.

## Extract one project (history-preserving)

For each project, in plan order, run the commands the plan generated for it:

```bash
git subtree split --prefix=<code_path> -b split/<repo>   # branch = that subtree's full history
# create the empty GitHub repo <repo> on the org account, then:
git push git@github.com:<org>/<repo>.git split/<repo>:main
```

## After each extract

1. In the new repo, install the shared devkit — `pip install -e` (or workspace-link) the shared
   `dev-rules-context` package — instead of copying standards/gates.
2. Run the **inherited gates** (`run_proofs`) — must be green before you push.
3. Rewrite any `src.<x>` imports to the package name; leave a compat shim during the transition
   (Lossless Distillation — a split is a move, never a delete; keep a rollback target).

## Rules (inherited standards)

- **Registry-driven** — the repo list, code paths, dependency edges, and order all come from
  `_repos/dev-rules-context/contracts/surface-registry.json`. No hardcoded surface/repo names.
- **Monorepo never breaks** — `git subtree split` is non-destructive; the code keeps working in the
  monorepo until you choose to remove it (and removal is move-never-delete → `archive/legacy/`).
- **Gates stay green** — the split isn't done until the extracted repo passes the inherited proofs.
- **Warrant** — graduating a surface to its own repo is a product-structure change; carry owner intent.

## Find cleanup candidates (do NOT delete)

After a split, surface orphaned/duplicate/stale files (move-never-delete report):

```bash
python3 _repos/shared-backend-components/scripts/find_migration_cleanup_candidates.py --self-test
python3 _repos/shared-backend-components/scripts/find_migration_cleanup_candidates.py --write
```

## Related tools

- `_repos/shared-backend-components/scripts/build_migration_plan.py` — the plan + manifests generator (the source of the commands above).
- `_repos/shared-backend-components/scripts/refresh_all.py` — re-derive edges/graph/interfaces/plan after any registry change.
- `skills/add-new-component` — register the surface/project BEFORE you split it.
- `skills/check-organization` — prove the org is in sync before and after.
