"""src.baltor.workers.execution_providers.gcp_cloud_run_function_candidate — RE-EXPORT SHIM (lossless extraction → Teleon).

The GCP Cloud Run function CANDIDATE adapter now lives in its canonical Teleon home
``src.teleon.runtime.execution_providers.gcp_cloud_run_function_candidate`` (runtime layer; _repos/shared-backend-components/architecture/
portfolio_dependency_law.json migration_status). This shim re-exports it so callers + proofs keep working with NO
duplicate runtime. Baltor → Teleon is the allowed direction; Teleon never imports Baltor.
"""
from __future__ import annotations

from src.teleon.runtime.execution_providers.gcp_cloud_run_function_candidate import (
    py_const_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate__PROVIDER_ID,
    py_class_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate__GcpCloudRunFunctionCandidate,
)

__all__ = ["py_class_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate__GcpCloudRunFunctionCandidate", "py_const_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate__PROVIDER_ID"]
