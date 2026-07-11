"""src.teleon.lift — TELEON LIFT: discover/model/observe existing cloud functions + Kubernetes workloads and
LIFT them into PurposeTask drafts WITHOUT taking over production.

Teleon Lift never says "we imported your Lambda into Teleon." It says: we discovered an existing
ImplementationCandidate, inferred a PurposeTaskDraft, preserved your current runtime as the rollback baseline,
and you can now evaluate alternatives safely. The pipeline:

    native workload → ImportedWorkload → RuntimeProfile + Trigger/Dependency graphs → PurposeTaskDraft
    (confidence + ALWAYS requires_human_review) → CapabilityTaskDraft → baseline ImplementationCandidate
    (= rollback target) → AdoptionPlan (6-mode ladder, read-only first)

Load-bearing invariants (proven by _repos/shared-backend-components/scripts/check_teleon_lift.py):
  * the legacy workload becomes an ImplementationCandidate (status imported_baseline) that IS the rollback
    target — never a live/managed PurposeTask;
  * inferred purpose is a DRAFT — requires_human_review is ALWAYS true; Teleon never self-confirms purpose;
  * the adoption ladder starts at `discover` (read-only); managed takeover (level >= 4) needs human-confirmed
    purpose;
  * env-var VALUES are never imported (key names only); cloud connectors are offline SEAMS (canned fixtures
    today; the real provider APIs are labelled stubs).

ARCHITECTURAL LAW: this package is Teleon — it must never import `src.baltor.*` (enforced by
check_portfolio_dependency_law). It reuses _repos/shared-backend-components/architecture/capability_runtime_classes.json (the runtime-class
vocabulary) so a lifted workload's runtime_class_guess is already CTS-1-bindable.
"""
from .pipeline import lift_workload, lift_inventory, LiftResult
from . import model, normalize, semantic_lifter, adoption, connectors

__all__ = ["lift_workload", "lift_inventory", "LiftResult", "model", "normalize", "semantic_lifter",
           "adoption", "connectors"]
