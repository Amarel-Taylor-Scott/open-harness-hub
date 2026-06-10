"""src/baltor/experiments/ids — RE-EXPORT SHIM (lossless extraction → Teleon).

The canonical id/hash helpers for the parallel-path engine now live in their Teleon home
``src.teleon.experiments.ids`` (experiments layer; architecture/portfolio_dependency_law.json migration_status,
step 2). This shim re-exports them so callers — including the still-in-Baltor experiments siblings whose
``from .ids import …`` resolves here — keep working with NO duplicate runtime. Baltor → Teleon is the allowed
direction; Teleon never imports Baltor.
"""
from __future__ import annotations

from src.teleon.experiments.ids import ID_HASH_SUFFIX_LEN, canonical_bytes, canonical_id, sha256_hex

__all__ = ["canonical_bytes", "sha256_hex", "canonical_id", "ID_HASH_SUFFIX_LEN"]
