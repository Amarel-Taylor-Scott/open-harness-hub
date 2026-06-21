"""src.teleon.runtime.execution_providers.factory — backend id -> an ExecutionProviderPort instance.

The seam from a configured medium (medium_config 'compute') to a concrete provider. Every backend in the policy
matrix maps here: Cloudflare Workers (BYO key), Kubernetes (BYO cluster), the serverless family (Lambda/GCP/Azure,
BYO creds), and the local emulators (the offline equivalents). Credentials are tenant SecretRefs resolved via an
injected resolver (never logged). serves_truth=false; Teleon-layer; stdlib only.
"""
from __future__ import annotations

from typing import Any, Callable

from src.teleon.runtime.execution_providers.cloud_function import CloudFunctionProvider, _FLAVORS
from src.teleon.runtime.execution_providers.cloudflare_workers import CloudflareWorkersProvider
from src.teleon.runtime.execution_providers.kubernetes import KubernetesProvider

_SERVERLESS = set(_FLAVORS)
_K8S = {"k8s_deployment_worker", "k8s_job"}
_LOCAL = {"local_function_emulator", "local_subprocess", "local_job_emulator"}


def supported_backends() -> list[str]:
    return sorted({"cloudflare_workers", *_K8S, *_SERVERLESS, *_LOCAL})


def get_execution_provider(backend: str, *, secret_refs: dict | None = None,
                           resolve_secret: Callable[[str], str | None] | None = None, network_ok: bool = False,
                           account_id: str | None = None, endpoint: str | None = None) -> Any:
    """Instantiate the provider for ``backend``. ``secret_refs`` maps logical secret name -> SecretRef; ``resolve_secret``
    turns a SecretRef into the value (injected; never logged). Raises on an unknown backend (never a silent default)."""
    secret_refs = secret_refs or {}
    if backend == "cloudflare_workers":
        return CloudflareWorkersProvider(account_id=account_id, token_secret_ref=secret_refs.get("cloudflare_api_token"),
                                         resolve_secret=resolve_secret, network_ok=network_ok)
    if backend in _K8S:
        return KubernetesProvider(secret_refs=secret_refs, resolve_secret=resolve_secret, endpoint=endpoint, network_ok=network_ok)
    if backend in _SERVERLESS:
        return CloudFunctionProvider(flavor=backend, secret_refs=secret_refs, resolve_secret=resolve_secret, network_ok=network_ok)
    if backend in _LOCAL:
        from src.teleon.workers.function_emulator import LocalFunctionEmulator
        return LocalFunctionEmulator()
    raise ValueError(f"unknown execution backend {backend!r}; supported: {supported_backends()}")


__all__ = ["get_execution_provider", "supported_backends"]
