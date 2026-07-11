# contracts

**Purpose.** Versioned payloads/schemas/shared types.

**What belongs here.** Code for the `contracts` layer of the Baltor spine (see `architecture/project_spine.json`).

**What does NOT belong here.** Anything that violates the import direction below, or a different layer's concern.

**Allowed project imports.** stdlib only

**Forbidden imports.** ['src/baltor/processors', 'src/baltor/api', 'scripts', 'web']

**Enforced by.** `scripts/check_contract_registry_manifest` (+ the C33 architecture proofs).

> Legacy note: the current working implementation may still live under `scripts/` (see `architecture/migration_plan.json`); new reusable code lands here.
