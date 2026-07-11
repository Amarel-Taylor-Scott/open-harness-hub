"""src/baltor/experiments/path_promotion — RE-EXPORT SHIM (lossless extraction → Teleon).

The promotion-authority module now lives in its canonical Teleon home ``src.teleon.experiments.path_promotion``
(experiments layer; _repos/shared-backend-components/architecture/portfolio_dependency_law.json migration_status, step 2). This shim re-exports its
full accessed surface (decide / is_promote_authorized / authorized_promoted_path_id + GATES + the decision constants
+ the canonical_id it re-exports from .ids) so purpose_task + the check_parallel_path_* / check_openbenchmarkhub_core
proofs + still-in-Baltor siblings keep working with NO duplicate runtime. Baltor → Teleon is the allowed direction;
Teleon never imports Baltor.
"""
from __future__ import annotations

from src.teleon.experiments.path_promotion import (
    DECISION_KEEP,
    DECISION_PROMOTE,
    GATES,
    SCHEMA_VERSION,
    authorized_promoted_path_id,
    canonical_id,
    decide,
    is_promote_authorized,
)

__all__ = ["decide", "is_promote_authorized", "authorized_promoted_path_id", "GATES", "SCHEMA_VERSION",
           "DECISION_PROMOTE", "DECISION_KEEP", "canonical_id"]
