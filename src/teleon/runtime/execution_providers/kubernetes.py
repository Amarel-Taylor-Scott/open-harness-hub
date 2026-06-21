"""src.teleon.runtime.execution_providers.kubernetes — BYO Kubernetes execution (the customer's cluster).

A customer supplies their cluster API endpoint + a service-account token (SecretRefs); Teleon dispatches a Job to
THEIR cluster (their compute, their data residency). Implements ExecutionProviderPort via ByoComputeProvider:
eligible only with creds, offline equivalent = execution.local_job_emulator@v1, never owns truth. The live path
(create a k8s Job via their API) is documented; without a reachable cluster it returns a non-consumable unavailable
result and the dispatcher falls back to the local job emulator. compute_ownership = customer_managed.
Teleon-layer; stdlib only.
"""
from __future__ import annotations

from typing import Any

from src.teleon.runtime.execution_providers._byo_base import ByoComputeProvider

PROVIDER_ID = "execution.k8s_deployment_worker@candidate"


class KubernetesProvider(ByoComputeProvider):
    provider_id = PROVIDER_ID
    backend = "k8s_deployment_worker"
    compute_ownership = "customer_managed"
    offline_equivalent = "execution.local_job_emulator@v1"
    required_secrets = ("kube_api_endpoint", "kube_token")

    def _live(self, task: dict) -> Any:
        # LIVE (documented): POST a Job to {kube_api_endpoint}/apis/batch/v1/namespaces/<ns>/jobs with the SA token,
        # poll to completion, record into the DurableFleetLedger (our truth). Needs a reachable cluster + a kube client;
        # not wired in this build -> non-consumable so the dispatcher falls back to local_job_emulator.
        from src.teleon.runtime.execution_provider import ProviderUnavailableResult
        return ProviderUnavailableResult(self.provider_id, "live k8s Job dispatch needs a reachable cluster + kube client (not wired)")


__all__ = ["KubernetesProvider", "PROVIDER_ID"]
