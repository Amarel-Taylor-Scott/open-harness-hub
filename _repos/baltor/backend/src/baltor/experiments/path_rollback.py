"""src/baltor/experiments/path_rollback — RE-EXPORT SHIM (lossless extraction → Teleon).

The rollback-plan builder now lives in its canonical Teleon home ``src.teleon.experiments.path_rollback``
(experiments layer; _repos/shared-backend-components/architecture/portfolio_dependency_law.json migration_status, step 2). This shim re-exports
its full accessed surface (``build_rollback_plan`` + ``SCHEMA_VERSION``) so the check_parallel_path_*
proofs (examples / full_stack / promotion_gate / redteam) and still-in-Baltor siblings keep working with NO
duplicate runtime. The LOSSLESS DISTILLATION CLAUSE (deletes_paths / deletes_prior_runs pinned False — rollback
is a pointer move that NEVER deletes a path or a prior run) lives in the Teleon impl. Baltor → Teleon is the
allowed direction; Teleon never imports Baltor.
"""
from __future__ import annotations

from src.teleon.experiments.path_rollback import (
    SCHEMA_VERSION,
    build_rollback_plan,
)

__all__ = ["build_rollback_plan", "SCHEMA_VERSION"]
