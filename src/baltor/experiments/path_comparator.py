"""src/baltor/experiments/path_comparator — RE-EXPORT SHIM (lossless extraction → Teleon).

The path comparator now lives in its canonical Teleon home ``src.teleon.experiments.path_comparator`` (experiments
layer; architecture/portfolio_dependency_law.json migration_status, step 2). This shim re-exports its full accessed
surface (the public API + the `canonical_id` it re-exports from .ids) so purpose_task + the check_parallel_path_*
proofs + still-in-Baltor siblings keep working with NO duplicate runtime. Baltor → Teleon is the allowed direction;
Teleon never imports Baltor.
"""
from __future__ import annotations

from src.teleon.experiments.path_comparator import (
    ACTION_INVESTIGATE,
    ACTION_KEEP,
    ACTION_PROMOTE,
    SCHEMA_VERSION,
    canonical_id,
    compare,
)

__all__ = ["compare", "SCHEMA_VERSION", "ACTION_PROMOTE", "ACTION_KEEP", "ACTION_INVESTIGATE", "canonical_id"]
