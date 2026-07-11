"""src.teleon.runtime.execution_providers.factory — backend id -> an ExecutionProviderPort instance.

The seam from a configured medium (medium_config 'compute') to a concrete provider. Every backend in the policy
matrix maps here: Cloudflare Workers (BYO key), Kubernetes (BYO cluster), the serverless family (Lambda/GCP/Azure,
BYO creds), and the local emulators (the offline equivalents). Credentials are tenant SecretRefs resolved via an
injected resolver (never logged). serves_truth=false; Teleon-layer; stdlib only.
"""
from __future__ import annotations

from typing import Any, Callable

from src.teleon.runtime.execution_providers.cloud_function import py_class_src_teleon_runtime_execution_providers_cloud_function__CloudFunctionProvider, py_var_src_teleon_runtime_execution_providers_cloud_function___FLAVORS
from src.teleon.runtime.execution_providers.cloudflare_workers import py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider
from src.teleon.runtime.execution_providers.kubernetes import py_class_src_teleon_runtime_execution_providers_kubernetes__KubernetesProvider

py_var_src_teleon_runtime_execution_providers_factory___SERVERLESS = set(py_var_src_teleon_runtime_execution_providers_cloud_function___FLAVORS)
py_var_src_teleon_runtime_execution_providers_factory___K8S = {"k8s_deployment_worker", "k8s_job"}
py_var_src_teleon_runtime_execution_providers_factory___LOCAL = {"local_function_emulator", "local_subprocess", "local_job_emulator"}


def py_function_src_teleon_runtime_execution_providers_factory__supported_backends() -> list[str]:
    return sorted({"cloudflare_workers", *py_var_src_teleon_runtime_execution_providers_factory___K8S, *py_var_src_teleon_runtime_execution_providers_factory___SERVERLESS, *py_var_src_teleon_runtime_execution_providers_factory___LOCAL})


def py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider(py_arg_src_teleon_runtime_execution_providers_factory__py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider__backend: str, *, secret_refs: dict | None = None,
                           resolve_secret: Callable[[str], str | None] | None = None, network_ok: bool = False,
                           account_id: str | None = None, endpoint: str | None = None) -> Any:
    """Instantiate the provider for ``backend``. ``secret_refs`` maps logical secret name -> SecretRef; ``resolve_secret``
    turns a SecretRef into the value (injected; never logged). Raises on an unknown backend (never a silent default)."""
    secret_refs = secret_refs or {}
    if py_arg_src_teleon_runtime_execution_providers_factory__py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider__backend == "cloudflare_workers":
        return py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider(account_id=account_id, token_secret_ref=secret_refs.get("cloudflare_api_token"),
                                         resolve_secret=resolve_secret, network_ok=network_ok)
    if py_arg_src_teleon_runtime_execution_providers_factory__py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider__backend in py_var_src_teleon_runtime_execution_providers_factory___K8S:
        return py_class_src_teleon_runtime_execution_providers_kubernetes__KubernetesProvider(secret_refs=secret_refs, resolve_secret=resolve_secret, endpoint=endpoint, network_ok=network_ok)
    if py_arg_src_teleon_runtime_execution_providers_factory__py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider__backend in py_var_src_teleon_runtime_execution_providers_factory___SERVERLESS:
        return py_class_src_teleon_runtime_execution_providers_cloud_function__CloudFunctionProvider(flavor=py_arg_src_teleon_runtime_execution_providers_factory__py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider__backend, secret_refs=secret_refs, resolve_secret=resolve_secret, network_ok=network_ok)
    if py_arg_src_teleon_runtime_execution_providers_factory__py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider__backend in py_var_src_teleon_runtime_execution_providers_factory___LOCAL:
        from src.teleon.workers.function_emulator import LocalFunctionEmulator
        return LocalFunctionEmulator()
    raise ValueError(f"unknown execution backend {py_arg_src_teleon_runtime_execution_providers_factory__py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider__backend!r}; supported: {py_function_src_teleon_runtime_execution_providers_factory__supported_backends()}")


__all__ = ["py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider", "py_function_src_teleon_runtime_execution_providers_factory__supported_backends"]
