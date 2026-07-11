# ports

**Purpose.** Capability interfaces (Protocols).

**What belongs here.** Code for the `ports` layer of the Baltor spine (see `architecture/project_spine.json`).

**What does NOT belong here.** Anything that violates the import direction below, or a different layer's concern.

**Allowed project imports.** ['src/baltor/contracts']

**Forbidden imports.** ['src/baltor/adapters', 'src/baltor/processors', 'scripts', 'web']

**Enforced by.** `scripts/check_import_boundaries_manifest` (+ the C33 architecture proofs).

> Legacy note: the current working implementation may still live under `scripts/` (see `architecture/migration_plan.json`); new reusable code lands here.
