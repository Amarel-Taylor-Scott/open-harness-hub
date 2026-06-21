"""src.teleon.runtime.execution_providers.cloud_function — BYO serverless function execution (Lambda/GCP/Azure).

The serverless-function FAMILY behind one provider, selected by ``flavor`` (aws_lambda | gcp_cloud_run_function |
gcp_cloud_function | azure_function). A customer supplies their cloud credentials (SecretRefs); Teleon dispatches the
unit to THEIR function (their compute/bill/data-residency). Implements ExecutionProviderPort via ByoComputeProvider:
eligible only with creds, offline equivalent = execution.local_function_emulator@v1, never owns truth. The live invoke
(call the customer's function via the cloud SDK/HTTP) is documented; without reachable creds it returns a
non-consumable unavailable result and the dispatcher falls back to the local function emulator. Adding a new serverless
provider = a new flavor here (config), not a new class. Teleon-layer; stdlib only.
"""
from __future__ import annotations

from typing import Any

from src.teleon.runtime.execution_providers._byo_base import ByoComputeProvider

_FLAVORS = {
    "aws_lambda": ("aws_access_key_id", "aws_secret_access_key"),
    "gcp_cloud_run_function": ("gcp_service_account_json",),
    "gcp_cloud_function": ("gcp_service_account_json",),
    "azure_function": ("azure_function_key",),
}


class CloudFunctionProvider(ByoComputeProvider):
    compute_ownership = "customer_account"
    offline_equivalent = "execution.local_function_emulator@v1"

    def __init__(self, *, flavor: str = "aws_lambda", **kw) -> None:
        if flavor not in _FLAVORS:
            raise ValueError(f"unknown serverless flavor {flavor!r}; have: {sorted(_FLAVORS)}")
        super().__init__(**kw)
        self.flavor = flavor
        self.backend = flavor
        self.provider_id = f"execution.{flavor}@candidate"
        self.required_secrets = _FLAVORS[flavor]

    def _live(self, task: dict) -> Any:
        # LIVE (documented): invoke the customer's function via the cloud SDK/HTTP with their creds, record into the
        # DurableFleetLedger. Needs reachable cloud creds + an SDK; not wired in this build -> non-consumable fallback.
        from src.teleon.runtime.execution_provider import ProviderUnavailableResult
        return ProviderUnavailableResult(self.provider_id, f"live {self.flavor} invoke needs the cloud SDK + reachable creds (not wired)")


__all__ = ["CloudFunctionProvider"]
