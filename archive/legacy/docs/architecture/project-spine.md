# Project Spine & Folder Taxonomy (C33)

The repo is past "does it work?" — the risk is now uncontrolled growth. The spine makes structure prevent
sprawl instead of becoming sprawl: every folder is an **architectural boundary** with an owner, allowed
imports, and an enforcing proof. The machine-readable source of truth is `architecture/project_spine.json`.

## Layers (downward dependency only)
`contracts → ports → adapters → runtime → processors → workers/api → web`. Reusable product/runtime code
lives under `src/baltor/`; `scripts/` is **entrypoints, proofs, and compatibility wrappers only**.

| Layer | Home | May import | Must NOT import |
|---|---|---|---|
| contracts | `src/baltor/contracts`, `schemas` | stdlib | everything above |
| ports | `src/baltor/ports` | contracts | adapters/processors/scripts/web |
| adapters | `src/baltor/adapters` | contracts, ports | processors, web |
| runtime | `src/baltor/runtime`, `scripts/runtime` | contracts, ports | processors, demos, web, admin server, cfpb/esg |
| processors | `src/baltor/processors`, `scripts/runtime/builtin_processors.py` | contracts, ports, runtime.processor | admin server, web, global BUS/DURABLE |
| llm_gateway | `src/baltor/llm_gateway`, `scripts/llm_gateway` | contracts, ports, security | web, admin server |
| workers / api | `src/baltor/workers`, `scripts/flywheel_worker.py` / `src/baltor/api`, admin server | runtime, adapters, processors | web (workers) |
| web | `web/baltor` | API projections only | durable writes |

## Governed scope (today)
`src/baltor`, `scripts/runtime`, `scripts/artifact_graph`, `scripts/llm_gateway`, `scripts/security`,
`scripts/pipeline_runtime`. The broader Open Harness Hub code (catalog/, db/, enrichment/, context_workers/,
services/, site/, foundry/, …) predates the spine and is out of scope (see `migration_plan.json`).

## Migration rule (no big-bang)
Existing working files stay. New reusable code goes under `src/baltor/`. Old scripts become thin wrappers.
Legacy over-budget files + duplicates are allowlisted with split targets + deadlines. The architecture
proofs prevent NEW drift while the working CFPB demo + durable worker stay green.

## Enforcing proofs
`check_project_spine_folders` · `check_file_layout_policy` · `check_import_boundaries_manifest` ·
`check_runtime_ownership_manifest` · `check_contract_registry_manifest` · `check_monolith_allowlist` ·
`check_scripts_are_entrypoints` · `check_no_duplicate_runtime` · `check_architecture_dashboard_projection_only` ·
`check_architecture_adr_coverage` · `check_no_direct_provider_bypass`. ADRs: `docs/adr/0001..0003`.
