"""src.baltor.workers.execution_providers.gcp_cloud_run_function_candidate — RE-EXPORT SHIM (lossless extraction → Teleon).

The GCP Cloud Run function CANDIDATE adapter now lives in its canonical Teleon home
``src.teleon.runtime.execution_providers.gcp_cloud_run_function_candidate`` (runtime layer; architecture/
portfolio_dependency_law.json migration_status). This shim re-exports it so callers + proofs keep working with NO
duplicate runtime. Baltor → Teleon is the allowed direction; Teleon never imports Baltor.
"""
from __future__ import annotations

from src.teleon.runtime.execution_providers.gcp_cloud_run_function_candidate import (
    PROVIDER_ID,
    GcpCloudRunFunctionCandidate,
)

__all__ = ["GcpCloudRunFunctionCandidate", "PROVIDER_ID"]
