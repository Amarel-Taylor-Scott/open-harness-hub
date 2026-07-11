# `src/teleon/` — the Teleon runtime layer

**Teleon** (teleon.dev) is the purpose-driven, eval-gated, self-adaptive compute runtime — a **separate
product** from Baltor, owned by the holding company. This package is the destination boundary for the generic
runtime concepts being extracted out of `_repos/baltor/backend/src/baltor/`.

> **Architectural law** (`architecture/portfolio_dependency_law.json`, enforced by
> `scripts/check_portfolio_dependency_law.py`):
> - **Teleon MUST NOT import Baltor** (`src.baltor.*`). Teleon is reusable infrastructure; Baltor is a tenant.
> - **Teleon MAY consume OpenHubForAI** (`src.openhubforai.*`) artifacts (harnesses, templates, skills, the spec).
> - Baltor depends on Teleon; OpenHubForAI depends on neither.

## What Teleon owns
PurposeTask registry · runtime selector · implementation candidates · evidence ledger · promotion gate ·
policy engine · boundary approvals · task orientation · runtime adapters · assurance dashboard. It is the
reference implementation of the **open CapabilityTask spec** (the spec itself is stewarded by OpenHubForAI
for neutrality — "Teleon implements the Open CapabilityTask Spec").

## Migration in progress (lossless, incremental — never big-bang)
Generic runtime code still lives under `_repos/baltor/backend/src/baltor/` and moves here one layer at a time, updating imports +
proofs and keeping the flywheel green at each step. Planned order (see the law file's `migration_status`):
1. execution layer (`_repos/baltor/backend/src/baltor/workers/execution_*`) → `src/teleon/runtime`
2. Parallel-Path Engine (`_repos/baltor/backend/src/baltor/experiments`) → `src/teleon/experiments`
3. `_repos/baltor/backend/src/baltor/purpose_tasks` → `src/teleon/purpose_tasks`
4. add `_repos/baltor/backend/src/baltor/teleon_client` so Baltor calls Teleon as tenant `baltor-internal`

Canonical design: `docs/strategy/teleon-baltor-openhubforai-portfolio.md`. Build kit for Teleon's control &
trust plane (separate greenfield TS build): `prompts/teleon-build-kit.md`.
