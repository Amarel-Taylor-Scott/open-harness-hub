"""src.teleon.runtime.execution_providers.gcp_cloud_run_function_candidate — CANDIDATE cloud-function
execution backend (GCP Cloud Run function). No live cloud call without credentials + owner approval; when
unconfigured it returns ProviderUnavailableResult so the selector falls back to the local emulator. The
real GCP SDK is imported ONLY inside this adapter (never in domain/selector code). Catalog-only until proven.

Canonical TELEON home (runtime layer); imports the port from Teleon (never Baltor). Baltor re-exports this via
a shim at _repos/baltor/backend/src/baltor/workers/execution_providers/gcp_cloud_run_function_candidate.py.
"""
from __future__ import annotations

import os

from src.teleon.runtime.execution_provider import py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult

py_const_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate__PROVIDER_ID = "gcp_cloud_run_function@candidate"
# the env that would configure it (no secret-shaped literals; presence-only check)
py_var_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate___CRED_ENV = ("GCP_PROJECT", "GCP_FUNCTION_URL")


class py_class_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate__GcpCloudRunFunctionCandidate:
    provider_id = py_const_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate__PROVIDER_ID

    def configured(self) -> bool:
        return all(os.environ.get(k) for k in py_var_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate___CRED_ENV)

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "kind": "cloud_function", "status": "candidate",
                "owns_truth": False, "requires_env": list(py_var_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate___CRED_ENV)}

    def health(self) -> dict:
        return {"provider_id": self.provider_id, "available": self.configured(),
                "reason": "configured" if self.configured() else "no credentials (candidate)"}

    def invoke(self, py_arg_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate__py_class_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate__GcpCloudRunFunctionCandidate_invoke__task: dict):
        if not self.configured():
            return py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult(provider_id=self.provider_id,
                                             reason="GCP cloud function not configured (candidate); use the local emulator")
        # real invocation requires owner approval (network + creds) — never auto-run here.
        return py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult(provider_id=self.provider_id,
                                         reason="live cloud invocation requires explicit owner approval (network/creds)")


__all__ = ["py_class_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate__GcpCloudRunFunctionCandidate", "py_const_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate__PROVIDER_ID"]
