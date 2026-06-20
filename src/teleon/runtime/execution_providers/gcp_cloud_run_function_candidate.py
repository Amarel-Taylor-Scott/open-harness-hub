"""src.teleon.runtime.execution_providers.gcp_cloud_run_function_candidate — CANDIDATE cloud-function
execution backend (GCP Cloud Run function). No live cloud call without credentials + owner approval; when
unconfigured it returns ProviderUnavailableResult so the selector falls back to the local emulator. The
real GCP SDK is imported ONLY inside this adapter (never in domain/selector code). Catalog-only until proven.

Canonical TELEON home (runtime layer); imports the port from Teleon (never Baltor). Baltor re-exports this via
a shim at src/baltor/workers/execution_providers/gcp_cloud_run_function_candidate.py.
"""
from __future__ import annotations

import os

from src.teleon.runtime.execution_provider import ProviderUnavailableResult

PROVIDER_ID = "gcp_cloud_run_function@candidate"
# the env that would configure it (no secret-shaped literals; presence-only check)
_CRED_ENV = ("GCP_PROJECT", "GCP_FUNCTION_URL")


class GcpCloudRunFunctionCandidate:
    provider_id = PROVIDER_ID

    def configured(self) -> bool:
        return all(os.environ.get(k) for k in _CRED_ENV)

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "kind": "cloud_function", "status": "candidate",
                "owns_truth": False, "requires_env": list(_CRED_ENV)}

    def health(self) -> dict:
        return {"provider_id": self.provider_id, "available": self.configured(),
                "reason": "configured" if self.configured() else "no credentials (candidate)"}

    def invoke(self, task: dict):
        if not self.configured():
            return ProviderUnavailableResult(provider_id=self.provider_id,
                                             reason="GCP cloud function not configured (candidate); use the local emulator")
        # real invocation requires owner approval (network + creds) — never auto-run here.
        return ProviderUnavailableResult(provider_id=self.provider_id,
                                         reason="live cloud invocation requires explicit owner approval (network/creds)")


__all__ = ["GcpCloudRunFunctionCandidate", "PROVIDER_ID"]
