"""src.teleon — the TELEON purpose-driven runtime layer (separate product from Baltor).

Teleon is the purpose-driven, eval-gated, self-adaptive compute runtime SaaS (teleon.dev). It owns the
PurposeTask registry, runtime selection, implementation candidates, the evidence ledger, the promotion +
policy gates, boundary approvals, task orientation, runtime adapters, and the assurance dashboard. It is the
reference implementation of the open CapabilityTask spec (stewarded by OpenHubForAI).

ARCHITECTURAL LAW (_repos/shared-backend-components/architecture/portfolio_dependency_law.json, enforced by
_repos/shared-backend-components/scripts/check_portfolio_dependency_law.py): Teleon is reusable infrastructure. It MAY consume OpenHubForAI
artifacts; it must NEVER import Baltor (`src.baltor.*`) — Baltor is a TENANT/consumer of Teleon, not the other
way around. Generic Teleon concepts are being extracted incrementally out of `_repos/baltor/backend/src/baltor/` into this package
(see the migration_status in the law file); until then this package is the destination boundary, not yet the
home of the code.
"""
