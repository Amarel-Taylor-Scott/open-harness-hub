---
name: check-organization
description: Use before a release, in CI, or whenever the multi-repo org may have drifted — to PROVE every derived artifact (edges, dependency graph, interface manifests, migration plan) still matches its single source. If it's in sync, ship. If it drifted, refresh from the source and commit the regenerated files with the source change.
---

# Check Organization (drift gate)

The whole org layout is **derived from one source** —
`_repos/dev-rules-context/contracts/surface-registry.json` (+ each repo's `interface.json` + the code
layout). This skill proves nothing has drifted, using the SAME generators that produce the artifacts, so
the gate diffs against exactly what a refresh would write. Never hand-edit a derived file; if it drifted,
fix the source and regenerate.

## The gate (two checks)

```bash
python3 _repos/shared-backend-components/scripts/check_org_freshness.py     # fail if any derived artifact is stale vs the single source
python3 _repos/shared-backend-components/scripts/refresh_all.py --check     # verify edges/graph/interfaces/migration-plan in sync (no writes)
```

Prove the gate logic itself is sound (pure, offline):

```bash
python3 _repos/shared-backend-components/scripts/check_org_freshness.py --self-test   # in-sync tree passes; injected staleness trips
```

## If it's green

The org is in sync — safe to release.

## If it drifts

Regenerate from the source, then commit the regenerated files **with** the source change (same commit):

```bash
python3 _repos/shared-backend-components/scripts/refresh_all.py --write     # regenerate every derived artifact from the registry
git add -A && git commit                    # source change + regenerated derived files, together
```

Never patch a derived file to make the gate pass — that reintroduces drift. Change the registry (or the
repo's `interface.json` / code layout), then refresh.

## Rules (inherited standards)

- **Single source of truth** — a stale derived file is a hard failure, not a warning (NO-MAGIC-VALUES;
  no hardcoded surface/repo names in logic).
- **Same-change commits** — the source edit and its regenerated outputs land together; never orphan one.
- **Move-never-delete** — if the check surfaces dead/superseded docs, archive under `archive/legacy/`,
  then re-run the gate.
- **Warrant** — the registry is owner/architecture territory; a new surface or edge carries owner intent.

## CI wiring

CI runs both checks on every push/PR (see `.github/workflows/org-freshness.yml`). Locally the same gate
is `make check-org`. A red gate blocks the release until the org is refreshed and committed.

## Related tools

- `_repos/shared-backend-components/scripts/check_org_freshness.py` — the drift gate (diffs derived files against the live generators).
- `_repos/shared-backend-components/scripts/refresh_all.py` — `--check` for CI, `--write` to regenerate from the single source.
- `skills/organize-and-refresh` — the regenerate-everything companion.
- `skills/add-new-component` / `skills/split-repo` — the two org changes that most often cause drift.
