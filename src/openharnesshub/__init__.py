"""src.openharnesshub — the OPEN HARNESS HUB ecosystem layer (neutral, open).

OpenHarnessHub is the open ecosystem around purpose-driven compute: eval harnesses, task templates,
conformance tests, skills, runtime-adapter examples, example CapabilityTasks, and the OPEN CapabilityTask spec.
It is the neutral home of the standard so the standard never reads as one vendor's proprietary format.

ARCHITECTURAL LAW (architecture/portfolio_dependency_law.json, enforced by
scripts/check_portfolio_dependency_law.py): OpenHarnessHub depends on NEITHER Teleon (`src.teleon.*`) NOR
Baltor (`src.baltor.*`). Teleon consumes OpenHarnessHub artifacts; never the reverse. Keeping this package
import-free of the other layers is what makes the spec/ecosystem credibly neutral.
"""
