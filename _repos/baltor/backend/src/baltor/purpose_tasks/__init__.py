"""src.baltor.purpose_tasks — RE-EXPORT SHIM (lossless extraction -> Teleon).

PurposeTask is a Teleon concept (purpose/capability-provisioned self-adapting execution units; _repos/shared-backend-components/architecture/portfolio_dependency_law.json migration_status, step 3). The whole subsystem now lives in src.teleon.purpose_tasks; this shim re-exports its full accessed surface so the check_purpose_task_* / check_runtime_class_binding / check_adaptation_ladder / check_octs_conformance proofs keep working with NO duplicate runtime. Baltor -> Teleon is the allowed direction; Teleon never imports Baltor.
"""
from __future__ import annotations

from .purpose_task import (
    adapt, eval_suite_for, evaluate_health, provision, run_current,
    EVAL_SUITE_FIELD, PurposeTaskSpec,
)

__all__ = ["provision", "run_current", "evaluate_health", "adapt",
           "PurposeTaskSpec", "eval_suite_for", "EVAL_SUITE_FIELD"]
