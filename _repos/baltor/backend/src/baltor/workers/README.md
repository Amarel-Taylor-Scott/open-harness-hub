# workers

**Purpose.** Claim loops binding queues to the harness.

**What belongs here.** Code for the `workers` layer of the Baltor spine (see `architecture/project_spine.json`).

**What does NOT belong here.** Anything that violates the import direction below, or a different layer's concern.

**Allowed project imports.** ['src/baltor/runtime', 'src/baltor/adapters', 'src/baltor/processors', 'scripts/runtime', 'scripts/durable_store']

**Forbidden imports.** ['web']

**Enforced by.** `scripts/check_worker_command_envelope` (+ the C33 architecture proofs).

> Legacy note: the current working implementation may still live under `scripts/` (see `architecture/migration_plan.json`); new reusable code lands here.
