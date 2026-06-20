"""src.teleon.runtime.execution_providers.provider_unavailable — the canonical non-consumable result for
an unconfigured/unreachable backend (cloud creds missing, Docker/K8s absent). A provider that ALWAYS
returns ProviderUnavailableResult — so a missing cloud backend degrades to a structured, safe fallback
signal, never a crash and never truth.

Canonical TELEON home (runtime layer); imports the port from Teleon (never Baltor). Baltor re-exports this via
a shim at src/baltor/workers/execution_providers/provider_unavailable.py.
"""
from __future__ import annotations

from src.teleon.runtime.execution_provider import ProviderUnavailableResult

PROVIDER_ID = "execution.provider_unavailable@v1"


class ProviderUnavailable:
    provider_id = PROVIDER_ID

    def __init__(self, reason: str = "backend unavailable") -> None:
        self.reason = reason

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "kind": "unavailable_sentinel", "owns_truth": False}

    def health(self) -> dict:
        return {"provider_id": self.provider_id, "available": False, "reason": self.reason}

    def invoke(self, task: dict):
        return ProviderUnavailableResult(provider_id=self.provider_id, reason=self.reason, consumable=False)


__all__ = ["ProviderUnavailable", "PROVIDER_ID"]
