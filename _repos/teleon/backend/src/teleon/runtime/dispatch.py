"""src.teleon.runtime.dispatch — the CONTROL-PLANE compute dispatch: route a task to the configured medium.

Given (tenant, function, task): resolve the per-function compute medium (medium_config), instantiate its provider
(factory), invoke it on the customer's compute, and FALL BACK to the offline equivalent (local emulator) when the
provider is unavailable (no creds / offline) — never crash. Returns a routing record (requested vs ran_on, fell_back,
reason, compute_ownership). Teleon ROUTES + records; it does not own the compute. serves_truth=false; Teleon-layer.
"""
from __future__ import annotations

from typing import Any, Callable

from src.teleon.config.medium_resolver import resolve_mediums
from src.teleon.runtime.execution_provider import py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult
from src.teleon.runtime.execution_providers.factory import py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider


def py_function_src_teleon_runtime_dispatch__dispatch(py_arg_src_teleon_runtime_dispatch__py_function_src_teleon_runtime_dispatch__dispatch__tenant: str, py_arg_src_teleon_runtime_dispatch__py_function_src_teleon_runtime_dispatch__dispatch__function: str, py_arg_src_teleon_runtime_dispatch__py_function_src_teleon_runtime_dispatch__dispatch__task: dict, *, resolve_secret: Callable[[str], str | None] | None = None,
             network_ok: bool = False, py_arg_src_teleon_runtime_dispatch__py_function_src_teleon_runtime_dispatch__dispatch__account_id: str | None = None, py_arg_src_teleon_runtime_dispatch__py_function_src_teleon_runtime_dispatch__dispatch__endpoint: str | None = None) -> dict:
    """Route ``task`` to the configured compute medium for (tenant, function), with offline fallback to the local
    emulator. Returns {requested_compute, ran_on, fell_back, reason, compute_ownership, serves_truth}."""
    py_local_src_teleon_runtime_dispatch__dispatch__m = resolve_mediums(py_arg_src_teleon_runtime_dispatch__py_function_src_teleon_runtime_dispatch__dispatch__tenant, py_arg_src_teleon_runtime_dispatch__py_function_src_teleon_runtime_dispatch__dispatch__function)
    py_local_src_teleon_runtime_dispatch__dispatch__backend = py_local_src_teleon_runtime_dispatch__dispatch__m.get("compute") or "local_function_emulator"
    py_local_src_teleon_runtime_dispatch__dispatch__provider = py_function_src_teleon_runtime_execution_providers_factory__get_execution_provider(py_local_src_teleon_runtime_dispatch__dispatch__backend, secret_refs=py_local_src_teleon_runtime_dispatch__dispatch__m.get("secrets", {}), resolve_secret=resolve_secret,
                                      network_ok=network_ok, account_id=py_arg_src_teleon_runtime_dispatch__py_function_src_teleon_runtime_dispatch__dispatch__account_id, endpoint=py_arg_src_teleon_runtime_dispatch__py_function_src_teleon_runtime_dispatch__dispatch__endpoint)
    py_local_src_teleon_runtime_dispatch__dispatch__res = py_local_src_teleon_runtime_dispatch__dispatch__provider.invoke(py_arg_src_teleon_runtime_dispatch__py_function_src_teleon_runtime_dispatch__dispatch__task)
    py_local_src_teleon_runtime_dispatch__dispatch__fell_back = isinstance(py_local_src_teleon_runtime_dispatch__dispatch__res, py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult)
    py_local_src_teleon_runtime_dispatch__dispatch__ran_on = (py_local_src_teleon_runtime_dispatch__dispatch__m.get("fallback_compute") or "local_function_emulator") if py_local_src_teleon_runtime_dispatch__dispatch__fell_back else py_local_src_teleon_runtime_dispatch__dispatch__backend
    return {
        "tenant": py_arg_src_teleon_runtime_dispatch__py_function_src_teleon_runtime_dispatch__dispatch__tenant, "function": py_arg_src_teleon_runtime_dispatch__py_function_src_teleon_runtime_dispatch__dispatch__function, "requested_compute": py_local_src_teleon_runtime_dispatch__dispatch__backend, "ran_on": py_local_src_teleon_runtime_dispatch__dispatch__ran_on,
        "fell_back": py_local_src_teleon_runtime_dispatch__dispatch__fell_back, "reason": getattr(py_local_src_teleon_runtime_dispatch__dispatch__res, "reason", None) if py_local_src_teleon_runtime_dispatch__dispatch__fell_back else None,
        "compute_ownership": py_local_src_teleon_runtime_dispatch__dispatch__m.get("compute_ownership"), "provider_id": getattr(py_local_src_teleon_runtime_dispatch__dispatch__provider, "provider_id", py_local_src_teleon_runtime_dispatch__dispatch__backend),
        "serves_truth": False,
    }


__all__ = ["py_function_src_teleon_runtime_dispatch__dispatch"]
