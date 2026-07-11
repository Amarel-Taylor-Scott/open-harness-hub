# ADR 0001 — Project Spine & Layering

## Status
Accepted (C33).

## Context
The Baltor codebase is past "does it work?" — durable runtime, restart survival, tenant ingest, atomic
decomposition, and a two-process exactly-once worker proof are all green. The risk shifted from missing
capability to **uncontrolled growth**: too many scripts, monolith files, hidden imports, and modules
inventing local contracts. Documentation alone does not stop drift.

## Decision
Adopt a layered project spine (`architecture/project_spine.json`): contracts → ports → adapters → runtime
→ processors → workers/api → web. Reusable product code belongs under `_repos/baltor/backend/src/baltor/`; `scripts/` is for
entrypoints, proofs, and compatibility wrappers only. Dependency direction is strict and downward; the
rules live in `architecture/import_boundaries.json`. Existing working files stay (no big-bang move) and are
recorded in `architecture/migration_plan.json`.

## Consequences
New code has an approved home and an enforced import direction. Legacy files keep working but are visible
debt with split targets. Folder creation is bounded by the spine manifest.

## Enforcement proofs
`check_project_spine_folders` · `check_file_layout_policy` · `check_import_boundaries_manifest`.
