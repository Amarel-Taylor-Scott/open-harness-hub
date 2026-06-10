# api

**Purpose.** HTTP routes + projections.

**What belongs here.** Code for the `api` layer of the Baltor spine (see `architecture/project_spine.json`).

**What does NOT belong here.** Anything that violates the import direction below, or a different layer's concern.

**Allowed project imports.** ['src/baltor/runtime', 'src/baltor/adapters', 'src/baltor/processors']

**Forbidden imports.** none

**Enforced by.** `scripts/check_architecture_dashboard_projection_only` (+ the C33 architecture proofs).

> Legacy note: the current working implementation may still live under `scripts/` (see `architecture/migration_plan.json`); new reusable code lands here.
