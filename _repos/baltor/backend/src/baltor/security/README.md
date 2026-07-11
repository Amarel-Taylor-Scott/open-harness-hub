# security

**Purpose.** Tenant isolation, encryption metadata, secret hygiene.

**What belongs here.** Code for the `security` layer of the Baltor spine (see `architecture/project_spine.json`).

**What does NOT belong here.** Anything that violates the import direction below, or a different layer's concern.

**Allowed project imports.** ['src/baltor/contracts']

**Forbidden imports.** ['web']

**Enforced by.** `scripts/check_tenant_isolation_policy` (+ the C33 architecture proofs).

> Legacy note: the current working implementation may still live under `scripts/` (see `architecture/migration_plan.json`); new reusable code lands here.
