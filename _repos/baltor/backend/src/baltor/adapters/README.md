# adapters

**Purpose.** Concrete backends (SQLite/object-store/vector/http).

**What belongs here.** Code for the `adapters` layer of the Baltor spine (see `architecture/project_spine.json`).

**What does NOT belong here.** Anything that violates the import direction below, or a different layer's concern.

**Allowed project imports.** ['src/baltor/contracts', 'src/baltor/ports']

**Forbidden imports.** ['src/baltor/processors', 'web']

**Enforced by.** `scripts/check_no_direct_provider_bypass` (+ the C33 architecture proofs).

> Legacy note: the current working implementation may still live under `scripts/` (see `architecture/migration_plan.json`); new reusable code lands here.
