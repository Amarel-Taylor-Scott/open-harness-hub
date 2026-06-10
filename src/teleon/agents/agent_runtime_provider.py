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

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from src.teleon.experiments.ids import canonical_id
from src.teleon.runtime.execution_backend_selector import select_backend

_A = Path(__file__).resolve().parents[3] / "architecture"
#: the single source of agent-runtime entries (CONFIG, not code).
CATALOG_PATH = _A / "agent_runtime_catalog.json"

#: capability slot this port populates (for the external capability catalog / replacement matrix).
AGENT_RUNTIME_SLOT = "agent_runtime"
#: pinned False on every agent runtime output — THE INVARIANT, made a constant the proofs assert.
AGENT_SERVES_TRUTH = False
#: an open-ended agent's default worker bucket (the selector hard-guards this off generic cloud functions).
DEFAULT_AGENT_BUCKET = "open_ended_agent"
#: the offline correctness-invariant runtime id (the one active runtime).
LOCAL_EMULATOR_RUNTIME_ID = "local_emulator@v1"


@dataclass(frozen=True)
class AgentRuntimeRequest:
    """A bounded request to run an agent. ``runtime_id`` selects a catalog runtime; ``bounds`` caps the run;
    ``worker_bucket`` drives backend selection (default ``open_ended_agent`` → hard-guarded off generic functions)."""
    task_id: str
    tenant_id: str
    runtime_id: str
    intent: str
    bounds: dict = field(default_factory=dict)
    worker_bucket: str = DEFAULT_AGENT_BUCKET
    requires_browser: bool = False
    requires_gpu: bool = False
    tenant_private: bool = False
    estimated_runtime_ms: int = 1000


@dataclass(frozen=True)
class AgentRuntimeResult:
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
class AgentRuntimeUnavailableResult:
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


class AgentRuntimeUnavailable(Exception):
    """A candidate agent runtime (ClawLess/OpenClaw/Hermes/...) is not imported/executed in this repo. Carries
    the missing ``runtime_ref`` (an ``env://…`` reference, never a value). The system stays green; the
    correctness invariant uses the deterministic local emulator instead."""

    def __init__(self, runtime_id: str, runtime_ref: str | None, detail: str = "") -> None:
        self.runtime_id = runtime_id
        self.runtime_ref = runtime_ref  # env://… REF, never a secret value
        msg = (f"agent runtime {runtime_id!r} is a catalog candidate only (not imported/executed in this repo): "
               f"missing runtime {runtime_ref}")
        if detail:
            msg += f" ({detail})"
        super().__init__(msg)


@runtime_checkable
class AgentRuntimeProviderPort(Protocol):
    """One agent runtime. ``run_agent`` runs a bounded agent task on a provisioned backend and returns an
    ``AgentRuntimeResult`` (``serves_truth=False``). A candidate runtime reports ``unavailable`` from ``status``
    and raises :class:`AgentRuntimeUnavailable` from ``run_agent`` (never imported/executed). Deterministic when
    ``now`` is injected."""
    provider_id: str

    def describe(self) -> dict: ...
    def status(self) -> dict: ...
    def run_agent(self, request: "AgentRuntimeRequest", *, backend: str, now: str) -> "AgentRuntimeResult": ...


def load_catalog(*, catalog_bytes: bytes | None = None) -> dict:
    """Return the agent-runtime catalog dict. ``catalog_bytes`` may be injected (tests/offline)."""
    raw = catalog_bytes if catalog_bytes is not None else CATALOG_PATH.read_bytes()
    return json.loads(raw)


def runtime_card(runtime_id: str, *, catalog: dict | None = None) -> dict | None:
    cat = catalog if catalog is not None else load_catalog()
    for r in cat.get("runtimes", []):
        if r.get("runtime_id") == runtime_id:
            return r
    return None


class LocalEmulatorAgentRuntime:
    """The offline correctness invariant: runs a bounded deterministic agent task with NO network and NO real
    container. Output is a CANDIDATE proposal (``serves_truth=False``), never truth."""
    provider_id = LOCAL_EMULATOR_RUNTIME_ID

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "role": "emulator", "status": "active",
                "imported": True, "executed": True, "serves_truth": AGENT_SERVES_TRUTH}

    def status(self) -> dict:
        return {"provider_id": self.provider_id, "status": "active", "imported": True, "executed": True,
                "runtime_ref": None}

    def run_agent(self, request: AgentRuntimeRequest, *, backend: str, now: str) -> AgentRuntimeResult:
        request_id = canonical_id("agentreq", request.task_id, request.tenant_id, request.runtime_id, request.intent)
        # bounded deterministic "work": no side effects, no I/O, no truth — just a recorded proposal.
        max_steps = int(request.bounds.get("max_steps", 1))
        steps = 1 if max_steps <= 0 else min(max_steps, 8)
        result_id = canonical_id("agentres", request_id, backend, now, str(steps))
        return AgentRuntimeResult(
            runtime_id=self.provider_id, request_id=request_id, task_id=request.task_id,
            status="succeeded", backend=backend, result_ids=(result_id,), serves_truth=AGENT_SERVES_TRUTH,
            detail={"steps": steps, "intent_echo": request.intent[:200], "ran_on": backend,
                    "proposal_only": True, "ran_at": now})


class CandidateAgentRuntime:
    """A candidate runtime (ClawLess/OpenClaw, Hermes, ...) built from a catalog card. NEVER imported/executed:
    ``status`` reports unavailable; ``run_agent`` raises :class:`AgentRuntimeUnavailable` naming the env:// ref."""

    def __init__(self, card: dict) -> None:
        self._card = card
        self.provider_id = card["runtime_id"]

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "role": "candidate", "status": "candidate",
                "imported": False, "executed": False, "serves_truth": AGENT_SERVES_TRUTH,
                "sandbox_profile": self._card.get("sandbox_profile"),
                "is_browser_runtime": bool(self._card.get("is_browser_runtime"))}

    def status(self) -> dict:
        return {"provider_id": self.provider_id, "status": "unavailable", "imported": False, "executed": False,
                "runtime_ref": self._card.get("runtime_ref")}

    def run_agent(self, request: AgentRuntimeRequest, *, backend: str, now: str) -> AgentRuntimeResult:
        raise AgentRuntimeUnavailable(self.provider_id, self._card.get("runtime_ref"),
                                      "candidate agent runtime; real provisioning is owner-gated")


def get_runtime(runtime_id: str, *, catalog: dict | None = None):
    """Return a provider for ``runtime_id``: the live LocalEmulator for the active runtime, else a
    CandidateAgentRuntime (catalog entry only). Returns ``None`` for an unknown id."""
    card = runtime_card(runtime_id, catalog=catalog)
    if card is None:
        return None
    if card.get("status") == "active" and runtime_id == LOCAL_EMULATOR_RUNTIME_ID:
        return LocalEmulatorAgentRuntime()
    return CandidateAgentRuntime(card)


def _selector_task(request: AgentRuntimeRequest) -> dict:
    """Project an agent request onto the execution_backend_selector's task shape (so the SAME numeric policy /
    pricebook / health / creds machinery picks the backend — no parallel selection logic here)."""
    return {"capability_id": f"agent_runtime::{request.runtime_id}", "worker_bucket": request.worker_bucket,
            "estimated_runtime_ms": int(request.estimated_runtime_ms),
            "requires_browser": bool(request.requires_browser), "requires_gpu": bool(request.requires_gpu),
            "tenant_private": bool(request.tenant_private)}


def dispatch_agent_request(request: AgentRuntimeRequest, *, now: str, catalog: dict | None = None,
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
    cat = catalog if catalog is not None else load_catalog()
    provider = get_runtime(request.runtime_id, catalog=cat)
    decision = select_backend(_selector_task(request), policy_matrix=policy_matrix, pricebook=pricebook,
                              provider_health=provider_health, available_creds=available_creds,
                              policy_override=policy_override)
    backend = decision.get("backend")
    request_id = canonical_id("agentreq", request.task_id, request.tenant_id, request.runtime_id, request.intent)

    if provider is None:
        result = AgentRuntimeUnavailableResult(runtime_id=request.runtime_id,
                                               reason=f"unknown runtime_id {request.runtime_id!r} (not in catalog)",
                                               backend_would_be=backend)
        return {"request_id": request_id, "runtime_id": request.runtime_id, "backend_decision": decision,
                "runtime_status": "unknown", "result": result}

    status = provider.status()
    if status.get("status") != "active":
        result = AgentRuntimeUnavailableResult(
            runtime_id=request.runtime_id,
            reason="candidate agent runtime not imported/executed (owner-gated)",
            runtime_ref=status.get("runtime_ref"), backend_would_be=backend)
        return {"request_id": request_id, "runtime_id": request.runtime_id, "backend_decision": decision,
                "runtime_status": status.get("status"), "result": result}

    result = provider.run_agent(request, backend=backend, now=now)
    return {"request_id": request_id, "runtime_id": request.runtime_id, "backend_decision": decision,
            "runtime_status": "active", "result": result}


__all__ = [
    "AgentRuntimeRequest", "AgentRuntimeResult", "AgentRuntimeUnavailableResult", "AgentRuntimeUnavailable",
    "AgentRuntimeProviderPort", "LocalEmulatorAgentRuntime", "CandidateAgentRuntime",
    "load_catalog", "runtime_card", "get_runtime", "dispatch_agent_request",
    "AGENT_RUNTIME_SLOT", "AGENT_SERVES_TRUTH", "DEFAULT_AGENT_BUCKET", "LOCAL_EMULATOR_RUNTIME_ID",
]
