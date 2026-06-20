"""src/baltor/experiments/parallel_paths — RE-EXPORT SHIM (lossless extraction → Teleon).

The Parallel-Path Engine's core now lives in its canonical Teleon home ``src.teleon.experiments.parallel_paths``
(experiments layer; architecture/portfolio_dependency_law.json migration_status, step 2). This shim re-exports its
public surface so callers — purpose_task, the check_parallel_path_* proofs, and still-in-Baltor siblings — keep
working with NO duplicate runtime. Baltor → Teleon is the allowed direction; Teleon never imports Baltor.
"""
from __future__ import annotations

from src.teleon.experiments.parallel_paths import (
    CHALLENGER_MODES,
    SCHEMA_VERSION,
    SERVABLE_MODES,
    Runner,
    RunnerResult,
    canonical_id,   # re-exported from .ids; callers access parallel_paths.canonical_id
    run_parallel,
    served_output,
    sha256_hex,     # re-exported from .ids; proofs access parallel_paths.sha256_hex
)

__all__ = ["run_parallel", "served_output", "SERVABLE_MODES", "CHALLENGER_MODES", "SCHEMA_VERSION",
           "Runner", "RunnerResult", "sha256_hex", "canonical_id"]
