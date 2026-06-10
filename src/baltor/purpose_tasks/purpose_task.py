"""src.baltor.purpose_tasks.purpose_task — RE-EXPORT SHIM (lossless extraction -> Teleon).

PurposeTask is a Teleon concept (purpose/capability-provisioned self-adapting execution units; architecture/portfolio_dependency_law.json migration_status, step 3). The whole subsystem now lives in src.teleon.purpose_tasks; this shim re-exports its full accessed surface so the check_purpose_task_* / check_runtime_class_binding / check_adaptation_ladder / check_octs_conformance proofs keep working with NO duplicate runtime. Baltor -> Teleon is the allowed direction; Teleon never imports Baltor.
"""
from __future__ import annotations

from src.teleon.purpose_tasks.purpose_task import (
    adapt, evaluate_health, provision, rollback, run_current, run_current_guarded,
)

__all__ = ["provision", "run_current", "run_current_guarded", "evaluate_health", "adapt", "rollback"]
