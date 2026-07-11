# architecture/ — machine-readable governance

Manifests that make architectural drift a FAILING check, not a vague concern:

- `project_spine.json` — approved folders + layered import boundaries
- `file_layout_policy.json` — approved top-level folders, banned vague filenames, scripts policy, line budgets
- `import_boundaries.json` — per-layer allowed/forbidden imports + runtime-core forbidden substrings
- `runtime_ownership.json` — one canonical owner per runtime concept
- `contract_registry.json` — every command/event/artifact/processor/pipeline/queue/log type
- `monolith_allowlist.json` — over-budget files with split target + deadline
- `migration_plan.json` — scripts/ → _repos/baltor/backend/src/baltor/ migration, no big-bang move
- `external_capability_catalog.json` — capability slots → adapters (stub/primary/fallback), I/O contract, license, health; builds on `data/backend-tools.yaml`
- `repo_health_policy.json` — when an external repo is still safe to adopt/keep (signals → actions, quarantine triggers)
- `repo_replacement_matrix.json` — per slot: wired → primary → fallback/stub → contract tests → swap steps

Enforced by the `scripts/check_*` architecture proofs (registered in the flywheel). See `docs/adr/`.
