"""src.openhubforai — the OPEN HARNESS HUB ecosystem layer (neutral, open).

OpenHubForAI is the open ecosystem around purpose-driven compute: eval harnesses, task templates,
conformance tests, skills, runtime-adapter examples, example CapabilityTasks, and the OPEN CapabilityTask spec.
It is the neutral home of the standard so the standard never reads as one vendor's proprietary format.

ARCHITECTURAL LAW (_repos/shared-backend-components/architecture/portfolio_dependency_law.json, enforced by
_repos/shared-backend-components/scripts/check_portfolio_dependency_law.py): OpenHubForAI depends on NEITHER Teleon (`src.teleon.*`) NOR
Baltor (`src.baltor.*`). Teleon consumes OpenHubForAI artifacts; never the reverse. Keeping this package
import-free of the other layers is what makes the spec/ecosystem credibly neutral.
"""
