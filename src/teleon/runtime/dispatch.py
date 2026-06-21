"""src.teleon.runtime.dispatch — the CONTROL-PLANE compute dispatch: route a task to the configured medium.

Given (tenant, function, task): resolve the per-function compute medium (medium_config), instantiate its provider
(factory), invoke it on the customer's compute, and FALL BACK to the offline equivalent (local emulator) when the
provider is unavailable (no creds / offline) — never crash. Returns a routing record (requested vs ran_on, fell_back,
reason, compute_ownership). Teleon ROUTES + records; it does not own the compute. serves_truth=false; Teleon-layer.
"""
from __future__ import annotations

from typing import Any, Callable

from src.teleon.config.medium_resolver import resolve_mediums
from src.teleon.runtime.execution_provider import ProviderUnavailableResult
from src.teleon.runtime.execution_providers.factory import get_execution_provider


def dispatch(tenant: str, function: str, task: dict, *, resolve_secret: Callable[[str], str | None] | None = None,
             network_ok: bool = False, account_id: str | None = None, endpoint: str | None = None) -> dict:
    """Route ``task`` to the configured compute medium for (tenant, function), with offline fallback to the local
    emulator. Returns {requested_compute, ran_on, fell_back, reason, compute_ownership, serves_truth}."""
    m = resolve_mediums(tenant, function)
    backend = m.get("compute") or "local_function_emulator"
    provider = get_execution_provider(backend, secret_refs=m.get("secrets", {}), resolve_secret=resolve_secret,
                                      network_ok=network_ok, account_id=account_id, endpoint=endpoint)
    res = provider.invoke(task)
    fell_back = isinstance(res, ProviderUnavailableResult)
    ran_on = (m.get("fallback_compute") or "local_function_emulator") if fell_back else backend
    return {
        "tenant": tenant, "function": function, "requested_compute": backend, "ran_on": ran_on,
        "fell_back": fell_back, "reason": getattr(res, "reason", None) if fell_back else None,
        "compute_ownership": m.get("compute_ownership"), "provider_id": getattr(provider, "provider_id", backend),
        "serves_truth": False,
    }


__all__ = ["dispatch"]
