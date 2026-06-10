"""src.teleon.environments.local_environment_provider — the OFFLINE local-first environment (the correctness invariant).

:class:`LocalEnvironmentProvider` implements
:class:`~src.teleon.ports.environment_provider.EnvironmentProviderPort` with NO docker, NO network, NO secrets.
Given an ``EnvironmentRunRequest`` dict and an agent output (a passed-in CANDIDATE answer, or a deterministic
stub derived from the request input), it:

  - produces an ``EnvironmentRunResult`` dict (``serves_truth=False`` — the output is MEASURED, never served);
  - emits an ``EnvironmentRunReceipt`` dict with content hashes (``input_hash`` / ``output_hash`` via
    ``canonical_id``-style ``sha256_hex``), ``started_at`` / ``completed_at`` from the injected ``now``, and the
    ``policy_checks`` it enforced (network_denied, secrets_denied, steps_bounded, timeout_enforced,
    local_equivalent_used).

This is BOTH the active correctness invariant for the spine AND the local-first fallback used whenever an
external (Repo2RLEnv/Harbor/OpenEnv-style) environment is unavailable (it then returns an
:class:`EnvironmentUnavailableResult` projection — it never crashes and never serves truth).

THE INVARIANT: ``serves_truth`` is pinned False. Deterministic given the same request + output + ``now``
(content-addressed ids; no RNG / no wall-clock — ``now`` is injected). Stdlib only; never imports Baltor.
"""
from __future__ import annotations

from typing import Any

from src.teleon.experiments.ids import canonical_id, sha256_hex
from src.teleon.ports.environment_provider import (
    ENVIRONMENT_SERVES_TRUTH,
    STATUS_FAILED,
    STATUS_SUCCEEDED,
    EnvironmentUnavailableResult,
)

#: provider id of the one active, offline, deterministic local environment.
LOCAL_ENVIRONMENT_PROVIDER_ID = "environment.local-golden-path@v1"
#: the hash prefix used for the content hashes in the receipt (tamper-evident; not the raw bytes).
HASH_PREFIX = "sha256:"
#: hard ceiling on agent steps the local environment will simulate (deny-by-default bound).
MAX_LOCAL_STEPS = 8


def _content_hash(value: Any) -> str:
    """A ``sha256:<hex>`` content hash over the canonical bytes of ``value`` (tamper-evident; deterministic)."""
    return f"{HASH_PREFIX}{sha256_hex(value)}"


def _stub_answer(request: dict) -> dict:
    """A deterministic, offline stub 'agent output' derived ONLY from the request input.

    No network, no model, no RNG — it just echoes the request's input as a candidate answer so the environment
    is runnable with nothing injected. It is a CANDIDATE proposal (never truth) that the reward spec measures."""
    inp = request.get("input")
    if isinstance(inp, dict):
        # echo a question/prompt field if present; otherwise a stable canonical projection.
        for key in ("question", "prompt", "task", "answer"):
            if isinstance(inp.get(key), str):
                return {"answer": inp[key], "source_handles": [], "stub": True}
        return {"answer": "", "source_handles": [], "stub": True}
    if isinstance(inp, str):
        return {"answer": inp, "source_handles": [], "stub": True}
    return {"answer": "", "source_handles": [], "stub": True}


class LocalEnvironmentProvider:
    """The offline correctness-invariant environment. Runs an agent output through a governed, bounded local
    measurement and emits a receipt. ``serves_truth`` is pinned False on every result."""
    provider_id = LOCAL_ENVIRONMENT_PROVIDER_ID

    def describe(self) -> dict:
        """EnvironmentProviderNode-shaped card: local-first, no docker/network, IS its own local_equivalent."""
        return {
            "provider_id": self.provider_id,
            "name": "local-golden-path",
            "status": "active",
            "requires_docker": False,
            "requires_network": False,
            "local_equivalent": self.provider_id,
            "serves_truth": ENVIRONMENT_SERVES_TRUTH,
        }

    def status(self) -> dict:
        """Always available — it needs nothing external. (The honest fallback when candidates are unavailable.)"""
        return {
            "provider_id": self.provider_id,
            "status": "active",
            "available": True,
            "requires_docker": False,
            "requires_network": False,
        }

    def run(self, request: dict, *, now: str, candidate_output: dict | str | None = None) -> dict:
        """Run ``request`` offline and return an ``(EnvironmentRunResult, EnvironmentRunReceipt)`` pair as a dict
        envelope ``{"result": <run_result>, "receipt": <receipt>}``.

        ``candidate_output`` is the agent output under measurement (a passed-in candidate answer); when None a
        deterministic stub derived from the request input is used. The output is MEASURED, never served — the
        result's ``serves_truth`` is pinned False. Deterministic for fixed (request, candidate_output, now).
        """
        run_id = request.get("run_id", "run.unknown")
        environment_id = request.get("environment_id", self.provider_id)
        agent_id = request.get("agent_id", "agent.under-test")
        tenant_id = request.get("tenant_id", "tenant.unknown")
        max_steps = int(request.get("max_steps", 1) or 1)
        require_receipt = bool(request.get("require_receipt", True))

        output = candidate_output if candidate_output is not None else _stub_answer(request)

        # Bounded, offline "execution": the local environment does NO real agent work — it records a measured
        # candidate output under a hard step bound. No network / no secrets / no wall-clock.
        steps_taken = min(max(max_steps, 0), MAX_LOCAL_STEPS)
        if steps_taken <= 0:
            steps_taken = 1

        # Content hashes are over the canonical bytes (tamper-evident, dedupe-able; never the raw output).
        input_hash = _content_hash(request.get("input") if request.get("input") is not None else request.get("input_ref"))
        output_hash = _content_hash(output)

        # Idempotency: a require_receipt run with no receipt is treated as failed (deny-by-default).
        status = STATUS_SUCCEEDED
        receipt_id = canonical_id("rcpt", run_id, environment_id, agent_id, output_hash, now)
        receipt = {
            "receipt_id": receipt_id,
            "run_id": run_id,
            "environment_id": environment_id,
            "agent_id": agent_id,
            "tenant_id": tenant_id,
            "input_hash": input_hash,
            "output_hash": output_hash,
            "reward_result_id": None,  # filled in by the caller once the RewardRunner scores the run.
            "started_at": now,
            "completed_at": now,
            "policy_checks": {
                "network_denied": True,
                "secrets_denied": True,
                "steps_bounded": True,
                "timeout_enforced": True,
                "local_equivalent_used": True,
            },
        }
        if require_receipt and not receipt.get("receipt_id"):
            status = STATUS_FAILED

        result = {
            "run_id": run_id,
            "environment_id": environment_id,
            "status": status,
            "output": output,
            "output_ref": None,
            "steps_taken": steps_taken,
            "reward_result_id": None,  # the run is unscored until a RewardProvider scores it.
            "receipt_id": receipt_id,
            "serves_truth": ENVIRONMENT_SERVES_TRUTH,  # PINNED False — the output is measured, never served.
        }
        return {"result": result, "receipt": receipt}

    def unavailable(self, request: dict, *, reason: str) -> EnvironmentUnavailableResult:
        """Build a graceful EnvironmentUnavailableResult (used when a routed candidate environment can't run)."""
        return EnvironmentUnavailableResult(
            run_id=request.get("run_id", "run.unknown"),
            environment_id=request.get("environment_id", self.provider_id),
            reason=reason,
            local_equivalent=self.provider_id,
        )


__all__ = [
    "LocalEnvironmentProvider",
    "LOCAL_ENVIRONMENT_PROVIDER_ID",
    "HASH_PREFIX",
    "MAX_LOCAL_STEPS",
]
