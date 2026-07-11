"""src.teleon.runtime.execution_providers.provider_unavailable — the canonical non-consumable result for
an unconfigured/unreachable backend (cloud creds missing, Docker/K8s absent). A provider that ALWAYS
returns ProviderUnavailableResult — so a missing cloud backend degrades to a structured, safe fallback
signal, never a crash and never truth.

Canonical TELEON home (runtime layer); imports the port from Teleon (never Baltor). Baltor re-exports this via
a shim at _repos/baltor/backend/src/baltor/workers/execution_providers/provider_unavailable.py.
"""
from __future__ import annotations

from src.teleon.runtime.execution_provider import py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult

py_const_src_teleon_runtime_execution_providers_provider_unavailable__PROVIDER_ID = "execution.provider_unavailable@v1"


class py_class_src_teleon_runtime_execution_providers_provider_unavailable__ProviderUnavailable:
    provider_id = py_const_src_teleon_runtime_execution_providers_provider_unavailable__PROVIDER_ID

    def __init__(self, reason: str = "backend unavailable") -> None:
        self.reason = reason

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "kind": "unavailable_sentinel", "owns_truth": False}

    def health(self) -> dict:
        return {"provider_id": self.provider_id, "available": False, "reason": self.reason}

    def invoke(self, py_arg_src_teleon_runtime_execution_providers_provider_unavailable__py_class_src_teleon_runtime_execution_providers_provider_unavailable__ProviderUnavailable_invoke__task: dict):
        return py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult(provider_id=self.provider_id, reason=self.reason, consumable=False)


__all__ = ["py_class_src_teleon_runtime_execution_providers_provider_unavailable__ProviderUnavailable", "py_const_src_teleon_runtime_execution_providers_provider_unavailable__PROVIDER_ID"]
