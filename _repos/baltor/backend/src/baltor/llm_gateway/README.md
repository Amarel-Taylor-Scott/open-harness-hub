# llm_gateway

**Purpose.** The only legal way to call models.

**What belongs here.** Code for the `llm_gateway` layer of the Baltor spine (see `architecture/project_spine.json`).

**What does NOT belong here.** Anything that violates the import direction below, or a different layer's concern.

**Allowed project imports.** ['src/baltor/contracts', 'src/baltor/ports', 'scripts/security']

**Forbidden imports.** ['web', 'scripts/baltor_admin_demo_server']

**Enforced by.** `scripts/check_no_direct_provider_bypass + check_llm_router_policy` (+ the C33 architecture proofs).

> Legacy note: the current working implementation may still live under `scripts/` (see `architecture/migration_plan.json`); new reusable code lands here.
