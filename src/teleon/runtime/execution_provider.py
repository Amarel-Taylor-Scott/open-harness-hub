"""src.teleon.runtime.execution_provider — the EXECUTION BACKEND port (canonical TELEON home).

HOW a CapabilityTask runs is an interchangeable execution backend behind this port: local subprocess, local
function emulator, Kubernetes worker/Job, cloud function (AWS Lambda / GCP Cloud Run function / Azure Function),
Cloud Run Job, browser/GPU pool, sandbox. Kubernetes and cloud functions can run SIDE BY SIDE and be switched by
policy/telemetry/pricing — never hardwired. The DB FleetLedger is the source of truth; an execution provider only
RUNS a task (claims atomically, writes artifacts/events, preserves idempotency + retry/DLQ) — it never owns truth
and never emits a CanonicalFact/ContextResponse unless it is an explicit gate-approved consumption/export provider.

Runtime selection is a Teleon concern (architecture/portfolio_dependency_law.json migration_status, extraction
step 1). Baltor consumes this through a re-export shim at src/baltor/ports/execution_provider.py — Baltor → Teleon
is the allowed dependency direction; Teleon never imports Baltor. This module depends only on the stdlib.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class ProviderUnavailableResult:
    """Returned (NOT raised) when a backend is unconfigured/unreachable — e.g. a cloud function with no
    credentials. Non-consumable: the caller falls back to another backend; the loop never crashes."""
    provider_id: str
    reason: str
    consumable: bool = False


@dataclass(frozen=True)
class ExecutionResult:
    provider_id: str
    execution_id: str
    task_id: str
    status: str            # succeeded | failed | unavailable
    result_ids: tuple = ()
    is_truth: bool = False  # an execution backend never produces truth
    detail: dict = field(default_factory=dict)


@runtime_checkable
class ExecutionProviderPort(Protocol):
    """One execution backend. Real cloud providers are CANDIDATE until credentials + proofs exist; the
    local function emulator is the offline correctness invariant."""
    provider_id: str

    def describe(self) -> dict: ...
    def health(self) -> dict: ...
    def eligible(self, task: dict, policy: dict) -> dict: ...
    def estimate(self, task: dict, policy: dict) -> dict: ...
    def invoke(self, task: dict) -> Any: ...   # ExecutionResult or ProviderUnavailableResult


__all__ = ["ExecutionProviderPort", "ProviderUnavailableResult", "ExecutionResult"]
