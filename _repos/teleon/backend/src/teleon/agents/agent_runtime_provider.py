"""src.teleon.agents.agent_runtime_provider — the SHARED AI-AGENT RUNTIME port (canonical TELEON home).

A shared agent layer RECEIVES a bounded agent request and PROVISIONS it onto the appropriate Teleon execution
backend (local emulator / Kubernetes job / sandbox worker / cloud function) by DELEGATING to
``execution_backend_selector.select_backend`` -> ``ExecutionProviderPort``. It does NOT reimplement claiming,
leasing, queues, or retries — it RIDES the existing FleetLedger + ExecutionProviderPort (never a second worker
framework). Candidate runtimes (ClawLess/OpenClaw, Hermes, ...) are CATALOG ENTRIES ONLY — never imported or
executed in this repo; the deterministic OFFLINE ``local_emulator@v1`` is the correctness invariant.

THE INVARIANT (mirrors the bounded-research-agent port): **Agents DISCOVER/ACT and PROPOSE; Baltor STORES,
VERIFIES, RECONCILES, CONSUMES.** Every agent runtime output carries ``serves_truth=False`` — an agent runtime
NEVER produces a CanonicalFact/ContextResponse. An open-ended agent NEVER auto-runs on a generic cloud function
(a hard guard in the selector) — it provisions onto a K8s job / sandbox worker unless a policy override asserts a
proof. Runtime provisioning is a Teleon concern; Baltor is a TENANT that submits requests through this port.

Teleon-owned: imports only the stdlib + Teleon runtime selection (never Baltor). Deterministic when ``now`` is
injected (content-addressed ids; no RNG/wall-clock). Stdlib only.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from src.teleon.experiments.ids import canonical_id
from src.teleon.runtime.execution_backend_selector import py_function_src_teleon_runtime_execution_backend_selector__select_backend

py_var_src_teleon_agents_agent_runtime_provider___A = _resource("architecture")
#: the single source of agent-runtime entries (CONFIG, not code).
py_const_src_teleon_agents_agent_runtime_provider__CATALOG_PATH = py_var_src_teleon_agents_agent_runtime_provider___A / "agent_runtime_catalog.json"

#: capability slot this port populates (for the external capability catalog / replacement matrix).
py_const_src_teleon_agents_agent_runtime_provider__AGENT_RUNTIME_SLOT = "agent_runtime"
#: pinned False on every agent runtime output — THE INVARIANT, made a constant the proofs assert.
py_const_src_teleon_agents_agent_runtime_provider__AGENT_SERVES_TRUTH = False
#: an open-ended agent's default worker bucket (the selector hard-guards this off generic cloud functions).
py_const_src_teleon_agents_agent_runtime_provider__DEFAULT_AGENT_BUCKET = "open_ended_agent"
#: the offline correctness-invariant runtime id (the one active runtime).
py_const_src_teleon_agents_agent_runtime_provider__LOCAL_EMULATOR_RUNTIME_ID = "local_emulator@v1"


@dataclass(frozen=True)
class py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeRequest:
    """A bounded request to run an agent. ``runtime_id`` selects a catalog runtime; ``bounds`` caps the run;
    ``worker_bucket`` drives backend selection (default ``open_ended_agent`` → hard-guarded off generic functions)."""
    task_id: str
    tenant_id: str
    runtime_id: str
    intent: str
    bounds: dict = field(default_factory=dict)
    worker_bucket: str = py_const_src_teleon_agents_agent_runtime_provider__DEFAULT_AGENT_BUCKET
    requires_browser: bool = False
    requires_gpu: bool = False
    tenant_private: bool = False
    estimated_runtime_ms: int = 1000


@dataclass(frozen=True)
class py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeResult:
    """The structured outcome of an agent run on a provisioned backend. ``serves_truth`` is pinned False: the
    output is a CANDIDATE proposal that returns to Baltor's governance rail, never a fact."""
    runtime_id: str
    request_id: str
    task_id: str
    status: str               # succeeded | failed
    backend: str              # the execution backend it was provisioned onto
    result_ids: tuple = ()
    serves_truth: bool = False
    detail: dict = field(default_factory=dict)


@dataclass(frozen=True)
class py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeUnavailableResult:
    """Returned (NOT raised) by :func:`dispatch_agent_request` when the selected runtime is a candidate with no
    runtime/credential in this repo (or unknown). Non-consumable: graceful degradation. Carries
    ``backend_would_be`` so the caller can SEE which Teleon backend it WOULD have provisioned (honest), and an
    ``env://`` ref (never a value)."""
    runtime_id: str
    reason: str
    runtime_ref: str | None = None
    backend_would_be: str | None = None
    consumable: bool = False
    serves_truth: bool = False


class py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeUnavailable(Exception):
    """A candidate agent runtime (ClawLess/OpenClaw/Hermes/...) is not imported/executed in this repo. Carries
    the missing ``runtime_ref`` (an ``env://…`` reference, never a value). The system stays green; the
    correctness invariant uses the deterministic local emulator instead."""

    def __init__(self, runtime_id: str, runtime_ref: str | None, detail: str = "") -> None:
        self.runtime_id = runtime_id
        self.runtime_ref = runtime_ref  # env://… REF, never a secret value
        py_local_src_teleon_agents_agent_runtime_provider__AgentRuntimeUnavailable__init__msg = (f"agent runtime {runtime_id!r} is a catalog candidate only (not imported/executed in this repo): "
               f"missing runtime {runtime_ref}")
        if detail:
            py_local_src_teleon_agents_agent_runtime_provider__AgentRuntimeUnavailable__init__msg += f" ({detail})"
        super().__init__(py_local_src_teleon_agents_agent_runtime_provider__AgentRuntimeUnavailable__init__msg)


@runtime_checkable
class py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeProviderPort(Protocol):
    """One agent runtime. ``run_agent`` runs a bounded agent task on a provisioned backend and returns an
    ``AgentRuntimeResult`` (``serves_truth=False``). A candidate runtime reports ``unavailable`` from ``status``
    and raises :class:`AgentRuntimeUnavailable` from ``run_agent`` (never imported/executed). Deterministic when
    ``now`` is injected."""
    provider_id: str

    def describe(self) -> dict: ...
    def status(self) -> dict: ...
    def run_agent(self, py_arg_src_teleon_agents_agent_runtime_provider__py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeProviderPort_run_agent__request: "AgentRuntimeRequest", *, backend: str, now: str) -> "AgentRuntimeResult": ...


def py_function_src_teleon_agents_agent_runtime_provider__load_catalog(*, py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__load_catalog__catalog_bytes: bytes | None = None) -> dict:
    """Return the agent-runtime catalog dict. ``catalog_bytes`` may be injected (tests/offline)."""
    py_local_src_teleon_agents_agent_runtime_provider__load_catalog__raw = py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__load_catalog__catalog_bytes if py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__load_catalog__catalog_bytes is not None else py_const_src_teleon_agents_agent_runtime_provider__CATALOG_PATH.read_bytes()
    return json.loads(py_local_src_teleon_agents_agent_runtime_provider__load_catalog__raw)


def py_function_src_teleon_agents_agent_runtime_provider__runtime_card(py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__runtime_card__runtime_id: str, *, catalog: dict | None = None) -> dict | None:
    py_local_src_teleon_agents_agent_runtime_provider__runtime_card__cat = catalog if catalog is not None else py_function_src_teleon_agents_agent_runtime_provider__load_catalog()
    for py_local_src_teleon_agents_agent_runtime_provider__runtime_card__r in py_local_src_teleon_agents_agent_runtime_provider__runtime_card__cat.get("runtimes", []):
        if py_local_src_teleon_agents_agent_runtime_provider__runtime_card__r.get("runtime_id") == py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__runtime_card__runtime_id:
            return py_local_src_teleon_agents_agent_runtime_provider__runtime_card__r
    return None


class py_class_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime:
    """The offline correctness invariant: runs a bounded deterministic agent task with NO network and NO real
    container. Output is a CANDIDATE proposal (``serves_truth=False``), never truth."""
    provider_id = py_const_src_teleon_agents_agent_runtime_provider__LOCAL_EMULATOR_RUNTIME_ID

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "role": "emulator", "status": "active",
                "imported": True, "executed": True, "serves_truth": py_const_src_teleon_agents_agent_runtime_provider__AGENT_SERVES_TRUTH}

    def status(self) -> dict:
        return {"provider_id": self.provider_id, "status": "active", "imported": True, "executed": True,
                "runtime_ref": None}

    def run_agent(self, py_arg_src_teleon_agents_agent_runtime_provider__py_class_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__request: py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeRequest, *, backend: str, now: str) -> py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeResult:
        py_local_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__request_id = canonical_id("agentreq", py_arg_src_teleon_agents_agent_runtime_provider__py_class_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__request.task_id, py_arg_src_teleon_agents_agent_runtime_provider__py_class_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__request.tenant_id, py_arg_src_teleon_agents_agent_runtime_provider__py_class_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__request.runtime_id, py_arg_src_teleon_agents_agent_runtime_provider__py_class_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__request.intent)
        # bounded deterministic "work": no side effects, no I/O, no truth — just a recorded proposal.
        py_local_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__max_steps = int(py_arg_src_teleon_agents_agent_runtime_provider__py_class_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__request.bounds.get("max_steps", 1))
        py_local_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__steps = 1 if py_local_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__max_steps <= 0 else min(py_local_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__max_steps, 8)
        py_local_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__result_id = canonical_id("agentres", py_local_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__request_id, backend, now, str(py_local_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__steps))
        return py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeResult(
            runtime_id=self.provider_id, request_id=py_local_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__request_id, task_id=py_arg_src_teleon_agents_agent_runtime_provider__py_class_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__request.task_id,
            status="succeeded", backend=backend, result_ids=(py_local_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__result_id,), serves_truth=py_const_src_teleon_agents_agent_runtime_provider__AGENT_SERVES_TRUTH,
            detail={"steps": py_local_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__steps, "intent_echo": py_arg_src_teleon_agents_agent_runtime_provider__py_class_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime_run_agent__request.intent[:200], "ran_on": backend,
                    "proposal_only": True, "ran_at": now})


class py_class_src_teleon_agents_agent_runtime_provider__CandidateAgentRuntime:
    """A candidate runtime (ClawLess/OpenClaw, Hermes, ...) built from a catalog card. NEVER imported/executed:
    ``status`` reports unavailable; ``run_agent`` raises :class:`AgentRuntimeUnavailable` naming the env:// ref."""

    def __init__(self, card: dict) -> None:
        self._card = card
        self.provider_id = card["runtime_id"]

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "role": "candidate", "status": "candidate",
                "imported": False, "executed": False, "serves_truth": py_const_src_teleon_agents_agent_runtime_provider__AGENT_SERVES_TRUTH,
                "sandbox_profile": self._card.get("sandbox_profile"),
                "is_browser_runtime": bool(self._card.get("is_browser_runtime"))}

    def status(self) -> dict:
        return {"provider_id": self.provider_id, "status": "unavailable", "imported": False, "executed": False,
                "runtime_ref": self._card.get("runtime_ref")}

    def run_agent(self, py_arg_src_teleon_agents_agent_runtime_provider__py_class_src_teleon_agents_agent_runtime_provider__CandidateAgentRuntime_run_agent__request: py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeRequest, *, backend: str, now: str) -> py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeResult:
        raise py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeUnavailable(self.provider_id, self._card.get("runtime_ref"),
                                      "candidate agent runtime; real provisioning is owner-gated")


def py_function_src_teleon_agents_agent_runtime_provider__get_runtime(py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__get_runtime__runtime_id: str, *, catalog: dict | None = None):
    """Return a provider for ``runtime_id``: the live LocalEmulator for the active runtime, else a
    CandidateAgentRuntime (catalog entry only). Returns ``None`` for an unknown id."""
    py_local_src_teleon_agents_agent_runtime_provider__get_runtime__card = py_function_src_teleon_agents_agent_runtime_provider__runtime_card(py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__get_runtime__runtime_id, catalog=catalog)
    if py_local_src_teleon_agents_agent_runtime_provider__get_runtime__card is None:
        return None
    if py_local_src_teleon_agents_agent_runtime_provider__get_runtime__card.get("status") == "active" and py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__get_runtime__runtime_id == py_const_src_teleon_agents_agent_runtime_provider__LOCAL_EMULATOR_RUNTIME_ID:
        return py_class_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime()
    return py_class_src_teleon_agents_agent_runtime_provider__CandidateAgentRuntime(py_local_src_teleon_agents_agent_runtime_provider__get_runtime__card)


def py_function_src_teleon_agents_agent_runtime_provider___selector_task(py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__selector_task__request: py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeRequest) -> dict:
    """Project an agent request onto the execution_backend_selector's task shape (so the SAME numeric policy /
    pricebook / health / creds machinery picks the backend — no parallel selection logic here)."""
    return {"capability_id": f"agent_runtime::{py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__selector_task__request.runtime_id}", "worker_bucket": py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__selector_task__request.worker_bucket,
            "estimated_runtime_ms": int(py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__selector_task__request.estimated_runtime_ms),
            "requires_browser": bool(py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__selector_task__request.requires_browser), "requires_gpu": bool(py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__selector_task__request.requires_gpu),
            "tenant_private": bool(py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__selector_task__request.tenant_private)}


def py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request(py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request: py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeRequest, *, now: str, catalog: dict | None = None,
                           policy_matrix: dict | None = None, pricebook: dict | None = None,
                           provider_health: dict | None = None, available_creds: set | None = None,
                           policy_override: dict | None = None) -> dict:
    """RECEIVE a bounded agent request → SELECT a Teleon execution backend (the 'set up appropriate cloud
    function / K8s' step, via :func:`execution_backend_selector.select_backend`) → run it on the active runtime
    OR degrade gracefully for a candidate/unknown runtime. Returns an envelope ``{request_id, runtime_id,
    backend_decision, runtime_status, result}``. NEVER crashes (returns an :class:`AgentRuntimeUnavailableResult`
    for candidate/unknown runtimes). Deterministic when ``now`` is injected.

    The backend decision is computed for EVERY request (even candidate runtimes) so the caller can SEE which
    backend Teleon WOULD provision — honest degradation. An open-ended agent is hard-guarded off generic cloud
    functions by the selector unless ``policy_override.allow_generic_functions`` asserts a proof.
    """
    py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__cat = catalog if catalog is not None else py_function_src_teleon_agents_agent_runtime_provider__load_catalog()
    py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__provider = py_function_src_teleon_agents_agent_runtime_provider__get_runtime(py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request.runtime_id, catalog=py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__cat)
    py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__decision = py_function_src_teleon_runtime_execution_backend_selector__select_backend(py_function_src_teleon_agents_agent_runtime_provider___selector_task(py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request), policy_matrix=policy_matrix, pricebook=pricebook,
                              provider_health=provider_health, available_creds=available_creds,
                              policy_override=policy_override)
    py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__backend = py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__decision.get("backend")
    py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request_id = canonical_id("agentreq", py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request.task_id, py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request.tenant_id, py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request.runtime_id, py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request.intent)

    if py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__provider is None:
        py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__result = py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeUnavailableResult(runtime_id=py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request.runtime_id,
                                               reason=f"unknown runtime_id {py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request.runtime_id!r} (not in catalog)",
                                               backend_would_be=py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__backend)
        return {"request_id": py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request_id, "runtime_id": py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request.runtime_id, "backend_decision": py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__decision,
                "runtime_status": "unknown", "result": py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__result}

    py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__status = py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__provider.status()
    if py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__status.get("status") != "active":
        py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__result = py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeUnavailableResult(
            runtime_id=py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request.runtime_id,
            reason="candidate agent runtime not imported/executed (owner-gated)",
            runtime_ref=py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__status.get("runtime_ref"), backend_would_be=py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__backend)
        return {"request_id": py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request_id, "runtime_id": py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request.runtime_id, "backend_decision": py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__decision,
                "runtime_status": py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__status.get("status"), "result": py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__result}

    py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__result = py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__provider.run_agent(py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request, backend=py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__backend, now=now)
    return {"request_id": py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request_id, "runtime_id": py_arg_src_teleon_agents_agent_runtime_provider__py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__request.runtime_id, "backend_decision": py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__decision,
            "runtime_status": "active", "result": py_local_src_teleon_agents_agent_runtime_provider__dispatch_agent_request__result}


__all__ = [
    "py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeRequest", "py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeResult", "py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeUnavailableResult", "py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeUnavailable",
    "py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeProviderPort", "py_class_src_teleon_agents_agent_runtime_provider__LocalEmulatorAgentRuntime", "py_class_src_teleon_agents_agent_runtime_provider__CandidateAgentRuntime",
    "py_function_src_teleon_agents_agent_runtime_provider__load_catalog", "py_function_src_teleon_agents_agent_runtime_provider__runtime_card", "py_function_src_teleon_agents_agent_runtime_provider__get_runtime", "py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request",
    "py_const_src_teleon_agents_agent_runtime_provider__AGENT_RUNTIME_SLOT", "py_const_src_teleon_agents_agent_runtime_provider__AGENT_SERVES_TRUTH", "py_const_src_teleon_agents_agent_runtime_provider__DEFAULT_AGENT_BUCKET", "py_const_src_teleon_agents_agent_runtime_provider__LOCAL_EMULATOR_RUNTIME_ID",
]
