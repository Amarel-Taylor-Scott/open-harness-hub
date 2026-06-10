# runtime

**Purpose.** Generic execution/validation/harness/pipeline.

**What belongs here.** Code for the `runtime` layer of the Baltor spine (see `architecture/project_spine.json`).

**What does NOT belong here.** Anything that violates the import direction below, or a different layer's concern.

**Allowed project imports.** ['src/baltor/contracts', 'src/baltor/ports']

**Forbidden imports.** ['src/baltor/processors', 'src/baltor/demos', 'web', 'scripts/baltor_admin_demo_server']

**Enforced by.** `scripts/check_import_boundaries_manifest + check_no_duplicate_runtime` (+ the C33 architecture proofs).

> Legacy note: the current working implementation may still live under `scripts/` (see `architecture/migration_plan.json`); new reusable code lands here.
