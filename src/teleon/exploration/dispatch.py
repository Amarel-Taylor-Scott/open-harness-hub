"""src.teleon.exploration.dispatch — the GOVERNED dispatch wrapper for a T3 (open-ended exploration) decision.

Given a T3 :class:`~src.teleon.exploration.ladder.EscalationDecision`, this builds a BOUNDED agent request and
runs it through the EXISTING shared agent-runtime port — it does NOT reimplement claiming/leasing/queues/backend
selection. The agent-runtime port (``src.teleon.agents.agent_runtime_provider``) already:

  * picks a Teleon execution backend via ``execution_backend_selector.select_backend`` → ``ExecutionProviderPort``
    (so this rides the SAME FleetLedger + provider machinery — never a second framework);
  * hard-guards the ``open_ended_agent`` worker bucket OFF generic cloud functions (an open-ended explorer
    provisions onto a k8s job / sandbox worker, never a generic function, unless a proof override says so);
  * runs the offline deterministic ``local_emulator@v1`` as the correctness invariant, and degrades HONESTLY for
    a catalog candidate (OpenClaw/Hermes) that has no runtime/credential in this repo — returning an
    ``AgentRuntimeUnavailableResult`` (never a fabricated result, never an import of the candidate).

This wrapper's ONLY additions on top of the port are governance framing:
  * it DEFAULTS the runtime to the offline ``local_emulator@v1`` invariant when no candidate is provisioned
    (honest unavailable for a named candidate, never a fake success);
  * it BOUNDS the request from the ladder's bounds (steps/time/cost/sandbox/allowlisted sources);
  * it wraps the outcome in an :class:`ExplorationProposal` — a CANDIDATE carrying provenance + a content-addressed
    RECEIPT, ``serves_truth=False`` — whose contract is: this RE-ENTERS the gate (lift + durability + receipts);
    it NEVER publishes a fact and a non-promoted capability never compiles to a runtime.

NEVER imports, pip-installs, or executes OpenClaw / Hermes / any third-party agent SDK. Candidate runtimes are
CATALOG REFERENCES only (``architecture/agent_runtime_catalog.json``). Deterministic when ``now`` is injected.

ARCHITECTURAL LAW: Teleon-layer code — stdlib + ``src.teleon`` siblings only; never ``src.baltor`` /
``src.openharnesshub``.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.teleon.experiments.ids import canonical_id
from src.teleon.agents.agent_runtime_provider import (
    AGENT_SERVES_TRUTH,
    DEFAULT_AGENT_BUCKET,
    LOCAL_EMULATOR_RUNTIME_ID,
    AgentRuntimeRequest,
    AgentRuntimeResult,
    AgentRuntimeUnavailableResult,
    dispatch_agent_request,
)
from src.teleon.exploration.ladder import (
    EscalationDecision,
    LADDER_DEFAULT_BOUNDS,
    T3_EXPLORATION,
)

#: the runtime a T3 dispatch uses BY DEFAULT — the offline correctness invariant. A caller may request a catalog
#: candidate (clawless_openclaw@candidate / hermes@candidate) instead; absent a provisioned candidate the system
#: stays on this deterministic emulator (honest), never a fabricated candidate result. One definition (the ladder
#: resolves its default T3 runtime_ref from here lazily).
DEFAULT_EXPLORATION_RUNTIME_ID = LOCAL_EMULATOR_RUNTIME_ID

#: the worker bucket every exploration request rides — the SAME bucket the agent-runtime catalog uses for
#: open-ended agents, which the selector HARD-GUARDS off generic cloud functions. One definition, not a literal.
EXPLORATION_WORKER_BUCKET = DEFAULT_AGENT_BUCKET  # == "open_ended_agent"

#: the dispatch module's view of the default bounds — the SAME named caps the ladder owns (single source). A
#: dispatch never invents looser bounds; it reads the ladder's defaults and applies the decision's merged bounds.
DEFAULT_BOUNDS = dict(LADDER_DEFAULT_BOUNDS)

#: the proposal contract every exploration output carries — it RE-ENTERS the gate; it is never served truth.
EXPLORATION_PRODUCES = "exploration_candidate_proposal"


@dataclass(frozen=True)
class ExplorationProposal:
    """The CANDIDATE outcome of a bounded exploration dispatch. ``serves_truth`` is pinned False — this proposal
    must clear the SAME runtime gate (lift + durability + receipts) before anything derived from it is promoted,
    and only a PROMOTED capability compiles to a runtime. Carries:

      * ``runtime_id`` — the catalog runtime that ran (default ``local_emulator@v1``) / would have run;
      * ``status`` — ``produced`` (a candidate proposal exists) | ``unavailable`` (a named candidate has no
        runtime/credential here — honest degradation, NOT a failure of the system);
      * ``backend`` — the Teleon execution backend the port selected (proves it rode the selector/FleetLedger);
      * ``receipt`` — a content-addressed receipt of the dispatch (deterministic; the audit + re-entry handle);
      * ``provenance`` — runtime + bounds + the originating escalation decision id (lossless lineage);
      * ``result_ids`` — the candidate proposal id(s) the explorer emitted (empty when unavailable).
    """
    proposal_id: str
    task_id: str
    runtime_id: str
    status: str                      # produced | unavailable
    produces: str = EXPLORATION_PRODUCES
    backend: str | None = None
    runtime_ref: str | None = None   # the env:// ref a candidate WOULD need (names only, never a value)
    result_ids: tuple = ()
    receipt: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)
    #: the contract: a candidate proposal re-enters the governance gate; it is never published as a fact.
    reenters_gate: bool = True
    serves_truth: bool = False


def _bounds_to_request_caps(bounds: dict) -> dict:
    """Project the ladder's bounds onto the AgentRuntimeRequest fields the port understands (it caps steps; the
    rest travel in ``bounds`` as honest caps the explorer is told to respect). No magic: read the named keys."""
    return {
        "max_steps": int(bounds.get("max_steps", LADDER_DEFAULT_BOUNDS["max_steps"])),
        "max_seconds": int(bounds.get("max_seconds", LADDER_DEFAULT_BOUNDS["max_seconds"])),
        "max_cost_usd": float(bounds.get("max_cost_usd", LADDER_DEFAULT_BOUNDS["max_cost_usd"])),
        # sandbox is an invariant for an open-ended explorer (the ladder already pins it True).
        "sandbox_required": True,
        # allowlisted sources travel as-is (the explorer may DISCOVER only within them); default empty = none.
        "allowlisted_sources": list(bounds.get("allowlisted_sources", []) or []),
    }


def _receipt(decision: EscalationDecision, request: AgentRuntimeRequest, runtime_id: str, status: str,
             backend: str | None, now: str) -> dict:
    """A content-addressed dispatch RECEIPT — deterministic (no clock/RNG; ``now`` is provenance only). This is
    the audit handle the proposal re-enters the gate with. ``serves_truth`` pinned False."""
    receipt_id = canonical_id("exreceipt", request.task_id, runtime_id, status, str(backend),
                              decision.decision_id, now)
    return {
        "receipt_id": receipt_id,
        "kind": "exploration_dispatch",
        "task_id": request.task_id,
        "tenant_id": request.tenant_id,
        "runtime_id": runtime_id,
        "worker_bucket": request.worker_bucket,
        "status": status,
        "backend": backend,
        "bounds": dict(request.bounds),
        "from_decision_id": decision.decision_id,
        "from_tier": decision.tier,
        "ran_at": now,
        "serves_truth": False,
    }


def dispatch_exploration(
    decision: EscalationDecision,
    *,
    intent: str,
    now: str,
    tenant_id: str = "unknown",
    runtime_id: str | None = None,
    catalog: dict | None = None,
    # the agent-runtime port's selector inputs — passed straight through (one selection authority, no parallel logic).
    policy_matrix: dict | None = None,
    pricebook: dict | None = None,
    provider_health: dict | None = None,
    available_creds: set | None = None,
    policy_override: dict | None = None,
) -> ExplorationProposal:
    """Dispatch a BOUNDED exploration run for a T3 ``decision`` and return a CANDIDATE :class:`ExplorationProposal`.

    REQUIRES a T3 decision (raises ``ValueError`` otherwise — only the open-ended-exploration rung dispatches an
    agent). Builds an :class:`AgentRuntimeRequest` bounded by the decision's bounds, on the ``open_ended_agent``
    worker bucket (hard-guarded off generic cloud functions), then DELEGATES to the agent-runtime port's
    ``dispatch_agent_request`` (which selects the backend via the shared selector/ExecutionProviderPort + rides
    FleetLedger). DEFAULTS the runtime to the offline ``local_emulator@v1`` invariant; a caller may name a
    catalog candidate (OpenClaw/Hermes) but an unprovisioned candidate degrades HONESTLY to
    ``status="unavailable"`` — never imported/executed, never a fabricated result.

    The outcome is always a CANDIDATE (``serves_truth=False``, ``reenters_gate=True``): it carries a receipt +
    provenance and RE-ENTERS the runtime gate. It never publishes a fact; only a promoted capability compiles.

    Deterministic when ``now`` is injected (content-addressed ids; no clock/RNG here).
    """
    if decision.tier != T3_EXPLORATION:
        raise ValueError(
            f"dispatch_exploration requires a T3 (open-ended exploration) decision, got tier {decision.tier} "
            f"(action {decision.action!r}). Only the exploration rung dispatches a bounded agent runtime; "
            "lower tiers run a template/primitive/LLM gate, T4 escalates to a human.")

    # the runtime to request: the decision's named runtime_ref (the ladder's default), overridable by the caller.
    # Defaults to the offline correctness invariant — never a candidate unless explicitly requested.
    runtime_id = runtime_id or decision.runtime_ref or DEFAULT_EXPLORATION_RUNTIME_ID
    caps = _bounds_to_request_caps(decision.bounds)

    request = AgentRuntimeRequest(
        task_id=decision.task_id,
        tenant_id=tenant_id,
        runtime_id=runtime_id,
        intent=intent,
        bounds=caps,
        worker_bucket=EXPLORATION_WORKER_BUCKET,  # → selector hard-guards off generic cloud functions
        # an open-ended explorer is sandboxed; we do not assert browser/gpu here (the catalog card carries that).
        estimated_runtime_ms=int(caps["max_seconds"]) * 1000,
    )

    # DELEGATE to the shared agent-runtime port: it selects the backend (selector/ExecutionProviderPort + FleetLedger)
    # and runs the active emulator OR degrades gracefully for a catalog candidate. We never select a backend here.
    envelope = dispatch_agent_request(
        request, now=now, catalog=catalog, policy_matrix=policy_matrix, pricebook=pricebook,
        provider_health=provider_health, available_creds=available_creds, policy_override=policy_override)

    backend = (envelope.get("backend_decision") or {}).get("backend")
    result = envelope.get("result")

    # The port returns EITHER an AgentRuntimeResult (the emulator ran → a candidate proposal exists) OR an
    # AgentRuntimeUnavailableResult (a named candidate has no runtime here → honest unavailable). Map both to a
    # CANDIDATE proposal; neither is ever truth.
    if isinstance(result, AgentRuntimeResult):
        status = "produced"
        result_ids = tuple(result.result_ids)
        runtime_ref = None
    else:
        # AgentRuntimeUnavailableResult (a named candidate has no runtime/credential here, or an unknown
        # runtime id) — degrade HONESTLY: name the env:// ref + the backend Teleon WOULD provision, never a
        # fabricated result and never an import of the candidate. (isinstance asserts the contract the port
        # documents; any other type would be a port-contract break, not a silent success.)
        assert isinstance(result, AgentRuntimeUnavailableResult), (
            f"agent-runtime port returned an unexpected result type {type(result).__name__}")
        status = "unavailable"
        result_ids = ()
        runtime_ref = result.runtime_ref
        backend = backend or result.backend_would_be

    receipt = _receipt(decision, request, runtime_id, status, backend, now)
    proposal_id = canonical_id("exprop", decision.task_id, runtime_id, status, receipt["receipt_id"])
    provenance = {
        "runtime_id": runtime_id,
        "worker_bucket": request.worker_bucket,
        "backend": backend,
        "bounds": dict(request.bounds),
        "from_decision_id": decision.decision_id,
        "from_tier": decision.tier,
        "request_id": envelope.get("request_id"),
        "runtime_status": envelope.get("runtime_status"),
        # the gate-re-entry contract, recorded in lineage so a reader knows where this goes next.
        "reenters": "runtime_gate (lift + durability + receipts); only a PROMOTED capability compiles",
        "compiled_directly": False,
    }
    return ExplorationProposal(
        proposal_id=proposal_id, task_id=decision.task_id, runtime_id=runtime_id, status=status,
        backend=backend, runtime_ref=runtime_ref, result_ids=result_ids, receipt=receipt,
        provenance=provenance, reenters_gate=True, serves_truth=AGENT_SERVES_TRUTH)


__all__ = [
    "dispatch_exploration", "ExplorationProposal",
    "DEFAULT_EXPLORATION_RUNTIME_ID", "EXPLORATION_WORKER_BUCKET", "DEFAULT_BOUNDS", "EXPLORATION_PRODUCES",
]
