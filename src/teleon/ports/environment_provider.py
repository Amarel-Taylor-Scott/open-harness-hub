"""src.teleon.ports.environment_provider — the SHARED ENVIRONMENT-PROVIDER port (canonical TELEON home).

An environment provider RUNS an agent/runtime inside a governed, local-first evaluation environment and
returns an :data:`EnvironmentRunResult`-shaped dict (see ``schemas/environments/EnvironmentRunResult.v1``).
Repo2RLEnv / Harbor / OpenEnv-style environments are CANDIDATES behind this port; the deterministic OFFLINE
:class:`~src.teleon.environments.local_environment_provider.LocalEnvironmentProvider` is the correctness
invariant and the fallback used whenever an external (docker/network) environment is unavailable.

THE INVARIANT (mirrors the agent-runtime / bounded-research-agent ports): **an environment MEASURES an agent;
it never makes the agent's output truth.** Every run result carries ``serves_truth=False`` (pinned const false
by the schema) — a run produces a measurement (a RewardResult by reference) + an agent output, never served or
promotable truth. Deny-by-default: bounded steps, a wall-clock budget, network/secrets denied locally.

Teleon-owned: imports only the stdlib (and Teleon id helpers via the modules that USE this port) — never
Baltor. Deterministic when ``now`` is injected (content-addressed ids; no RNG / no wall-clock here). Stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

#: pinned False on every environment run result — THE INVARIANT, made a constant the proofs assert.
ENVIRONMENT_SERVES_TRUTH = False

#: the EnvironmentRunResult.status values (mirrors the schema enum; single source for the providers below).
STATUS_SUCCEEDED = "succeeded"
STATUS_FAILED = "failed"
STATUS_UNAVAILABLE = "unavailable"
ENVIRONMENT_RUN_STATUSES = (STATUS_SUCCEEDED, STATUS_FAILED, STATUS_UNAVAILABLE)


@runtime_checkable
class EnvironmentProviderPort(Protocol):
    """One environment backend the spine MAY route a run to.

    ``run`` takes an ``EnvironmentRunRequest``-shaped dict and the injected ``now`` and returns an
    ``EnvironmentRunResult``-shaped dict (``serves_truth=False``). A candidate environment that cannot run
    locally (needs docker/network) reports it from ``status`` and returns a result with ``status=unavailable``
    (it degrades gracefully — it does NOT crash and does NOT serve truth). Deterministic when ``now`` is injected.
    """
    provider_id: str

    def describe(self) -> dict:
        """Static capability card: ``{provider_id, name, status, requires_docker, requires_network,
        local_equivalent, serves_truth}`` — the EnvironmentProviderNode shape."""
        ...

    def run(self, request: dict, *, now: str) -> dict:
        """Run ``request`` (an EnvironmentRunRequest dict) and return an EnvironmentRunResult dict."""
        ...

    def status(self) -> dict:
        """Liveness/availability: ``{provider_id, status, available, requires_docker, requires_network}``."""
        ...


@dataclass(frozen=True)
class EnvironmentUnavailableResult:
    """The graceful-degradation result when an environment cannot run locally (missing docker/network/dep).

    Returned (NOT raised) so the spine stays green and the caller can SEE which local-first fallback to use.
    ``consumable=False`` marks it non-measurable; ``serves_truth`` is pinned False; it carries an
    EnvironmentRunResult-compatible projection via :meth:`as_run_result` (``status="unavailable"``)."""
    run_id: str
    environment_id: str
    reason: str
    local_equivalent: str | None = None
    consumable: bool = False
    serves_truth: bool = ENVIRONMENT_SERVES_TRUTH
    policy_checks: dict = field(default_factory=dict)

    def as_run_result(self) -> dict:
        """Project to an EnvironmentRunResult dict (status=unavailable; no reward; serves_truth False)."""
        return {
            "run_id": self.run_id,
            "environment_id": self.environment_id,
            "status": STATUS_UNAVAILABLE,
            "output": None,
            "output_ref": None,
            "steps_taken": 0,
            "reward_result_id": None,
            "receipt_id": None,
            "serves_truth": ENVIRONMENT_SERVES_TRUTH,
        }


__all__ = [
    "EnvironmentProviderPort",
    "EnvironmentUnavailableResult",
    "ENVIRONMENT_SERVES_TRUTH",
    "STATUS_SUCCEEDED",
    "STATUS_FAILED",
    "STATUS_UNAVAILABLE",
    "ENVIRONMENT_RUN_STATUSES",
]
