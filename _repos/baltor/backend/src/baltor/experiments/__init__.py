"""_repos/baltor/backend/src/baltor/experiments — the PARALLEL-PATH EXPERIMENT ENGINE.

Run a baseline path AND each candidate path on the SAME input_snapshot for one capability_slot, compare
them apples-to-apples, and promote a candidate to baseline ONLY through a passing PathPromotionDecision —
never serve a candidate's output as truth. This is the runtime that the Stage-1 contracts under
``schemas/experiments/`` describe; every object it emits validates against those versioned schemas.

The engine is PURE + DETERMINISTIC: all inputs are injected (a caller-supplied ``runner`` performs the
actual path execution; ``now`` is passed in; ids are content hashes via :mod:`hashlib`). No wall-clock,
no RNG, no network, no Date.

Modules:
  - :mod:`parallel_paths`   — ``run_parallel(...) -> ParallelPathRun`` (same input to every path; candidate
                              output is recorded, NEVER served).
  - :mod:`path_comparator`  — ``compare(run, ...) -> PathComparisonReport`` (per-candidate gate verdicts).
  - :mod:`path_promotion`   — ``decide(report, criteria, ...) -> PathPromotionDecision`` (promote iff ALL
                              gates pass; always sets rollback_target = baseline.path_id).
  - :mod:`path_costing`     — ``estimate(...) -> PathCostReport`` (relative cost from the pricebook CONFIG).
  - :mod:`path_rollback`    — ``build_rollback_plan(decision, ...) -> PathRollbackPlan`` (undo a promotion by
                              a pointer move only — never deletes a path or a prior run).
"""
from __future__ import annotations

#: the canonical capability_slot the reconciliation beachhead uses (CFPB Reg-E vs FAQ); see
#: _repos/shared-backend-components/scripts/check_contextops_cfpb_reference.py + _repos/shared-backend-components/scripts/demo_offline_full_baltor.py.
RECONCILIATION_CAPABILITY_SLOT = "reconciliation.answer"

__all__ = [
    "RECONCILIATION_CAPABILITY_SLOT",
    "parallel_paths",
    "path_comparator",
    "path_promotion",
    "path_costing",
    "path_rollback",
]
