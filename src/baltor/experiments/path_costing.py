"""src/baltor/experiments/path_costing — RE-EXPORT SHIM (lossless extraction → Teleon).

The pricebook-derived path cost estimator now lives in its canonical Teleon home
``src.teleon.experiments.path_costing`` (experiments layer; architecture/portfolio_dependency_law.json
migration_status, step 2). This shim re-exports its full accessed surface (estimate / load_pricebook +
SCHEMA_VERSION + COST_CURRENCY + PRICEBOOK_PATH + the canonical_id it re-exports from .ids) so callers + proofs
keep working with NO duplicate runtime. Baltor → Teleon is the allowed direction; Teleon never imports Baltor.
"""
from __future__ import annotations

from src.teleon.experiments.path_costing import (
    COST_CURRENCY,
    PRICEBOOK_PATH,
    SCHEMA_VERSION,
    canonical_id,
    estimate,
    load_pricebook,
)

__all__ = ["estimate", "load_pricebook", "SCHEMA_VERSION", "COST_CURRENCY", "PRICEBOOK_PATH", "canonical_id"]
