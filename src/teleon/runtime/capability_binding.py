"""src.teleon.runtime.capability_binding — bind a declared CapabilityTask to an execution TARGET, abstracting
all cloud-function / Kubernetes-worker programming behind the binding contract.

A CapabilityTask declares the WHAT (intent + bounds + worker bucket); a *binding* wires it onto a TARGET. The
ACTIVE target is the offline ``local_function@v1`` emulator; the rest (Nitric / Score / Temporal / Knative /
KEDA / Kratix) are CANDIDATE cards — never imported, never executed, never reached over the network. Which
execution backend the bound task actually runs on is a POLICY decision DELEGATED to
:func:`src.teleon.runtime.execution_backend_selector.select_backend` (never reinvented here): the same
CapabilityTask binds to the local emulator today and to a K8s worker / cloud function tomorrow by changing
policy/pricebook, not code — and open-ended/guarded buckets stay off generic cloud functions unless a policy
override asserts a proof.

THE INVARIANT: a binding is a wiring decision, never truth (``serves_truth=False``). Candidate targets degrade
gracefully — :func:`bind_capability_task` returns a :class:`BindingUnavailableResult` (never raises, never
crashes) that STILL reports ``backend_would_be`` so the plan is honest. Runtime binding is a Teleon concern;
this module imports only the stdlib + Teleon runtime selection and NEVER ``src.baltor``. Stdlib only.
"""
from __future__ import annotations

from src.teleon.experiments.ids import canonical_id
from src.teleon.ports.capability_binding_provider import (
    BINDING_SERVES_TRUTH,
    LOCAL_FUNCTION_TARGET,
    BindingResult,
    BindingUnavailableResult,
)
from src.teleon.runtime.execution_backend_selector import generic_functions, select_backend

#: the binding-target registry (CONFIG-shaped data, not code). The local function emulator is the one ACTIVE
#: target; the rest are CANDIDATE cards naming the runtime the OWNER would have to authorize (an ``env://``
#: ref, never a value). A candidate is NEVER imported/executed/reached — its card only describes it.
TARGETS: dict[str, dict] = {
    LOCAL_FUNCTION_TARGET: {
        "target": LOCAL_FUNCTION_TARGET, "status": "active", "kind": "local_function_emulator",
        "imported": True, "executed": True, "ref": None,
        "note": "offline correctness invariant — deterministic local function emulator binding",
    },
    "nitric@candidate": {
        "target": "nitric@candidate", "status": "candidate", "kind": "infra_from_code_framework",
        "imported": False, "executed": False, "ref": "env://NITRIC_DEPLOY_TARGET",
        "note": "Nitric infra-from-code: candidate target; real deploy is owner-gated",
    },
    "score@candidate": {
        "target": "score@candidate", "status": "candidate", "kind": "workload_spec",
        "imported": False, "executed": False, "ref": "env://SCORE_PLATFORM_TARGET",
        "note": "Score workload spec: candidate target; real orchestrator binding is owner-gated",
    },
    "temporal@candidate": {
        "target": "temporal@candidate", "status": "candidate", "kind": "durable_workflow_engine",
        "imported": False, "executed": False, "ref": "env://TEMPORAL_NAMESPACE_TARGET",
        "note": "Temporal durable workflows: candidate target; real cluster binding is owner-gated",
    },
    "knative@candidate": {
        "target": "knative@candidate", "status": "candidate", "kind": "serverless_k8s",
        "imported": False, "executed": False, "ref": "env://KNATIVE_SERVICE_TARGET",
        "note": "Knative serverless-on-K8s: candidate target; real service binding is owner-gated",
    },
    "keda@candidate": {
        "target": "keda@candidate", "status": "candidate", "kind": "event_autoscaler",
        "imported": False, "executed": False, "ref": "env://KEDA_SCALER_TARGET",
        "note": "KEDA event-driven autoscaling: candidate target; real scaler binding is owner-gated",
    },
    "kratix@candidate": {
        "target": "kratix@candidate", "status": "candidate", "kind": "platform_promise",
        "imported": False, "executed": False, "ref": "env://KRATIX_PROMISE_TARGET",
        "note": "Kratix platform Promises: candidate target; real promise binding is owner-gated",
    },
}


def target_card(target: str) -> dict | None:
    """Return the registry card for ``target`` (or ``None`` for an unknown target)."""
    return TARGETS.get(target)


def _selector_task(capability_task: dict) -> dict:
    """Project a declared CapabilityTask onto the execution_backend_selector's task shape so the SAME numeric
    policy / pricebook / health / creds machinery picks the backend — no parallel selection logic here. The
    CapabilityTask declares intent + bounds; the selector turns that into a backend (the cloud-function/K8s
    wiring the author never has to write)."""
    cap_id = str(capability_task.get("capability_id") or capability_task.get("id") or "capability_task")
    bounds = capability_task.get("bounds") or {}
    return {
        "capability_id": f"capability_task::{cap_id}",
        "worker_bucket": capability_task.get("worker_bucket", "utility"),
        "estimated_runtime_ms": int(capability_task.get("estimated_runtime_ms",
                                                         bounds.get("estimated_runtime_ms", 500))),
        "requires_browser": bool(capability_task.get("requires_browser")),
        "requires_gpu": bool(capability_task.get("requires_gpu")),
        "tenant_private": bool(capability_task.get("tenant_private")),
    }


def _capability_id(capability_task: dict) -> str:
    return str(capability_task.get("capability_id") or capability_task.get("id") or "capability_task")


def _backend_for(capability_task: dict, **selector_kwargs) -> dict:
    """DELEGATE backend choice to the policy selector (never reinvented). Computed for EVERY target — even a
    candidate — so callers always see which backend Teleon WOULD provision (honest degradation)."""
    return select_backend(_selector_task(capability_task), **selector_kwargs)


class LocalFunctionBinding:
    """ACTIVE golden path: bind a CapabilityTask onto the offline local function emulator. ``bind`` delegates
    the execution-backend choice to :func:`select_backend` (proving the target abstracts cloud/K8s wiring by
    POLICY) and records it in the :class:`BindingResult`. Deterministic when ``now`` is injected
    (``binding_id`` is content-addressed over (capability_id, target, now)). Output is a wiring decision,
    never truth (``serves_truth=False``)."""
    provider_id = LOCAL_FUNCTION_TARGET

    def describe(self) -> dict:
        card = TARGETS[LOCAL_FUNCTION_TARGET]
        return {"provider_id": self.provider_id, "target": self.provider_id, "role": "active",
                "kind": card["kind"], "status": "active", "imported": True, "executed": True,
                "serves_truth": BINDING_SERVES_TRUTH}

    def status(self) -> dict:
        return {"provider_id": self.provider_id, "target": self.provider_id, "status": "active",
                "imported": True, "executed": True, "ref": None}

    def bind(self, capability_task: dict, *, now: str, **selector_kwargs) -> BindingResult:
        capability_id = _capability_id(capability_task)
        # deterministic binding id: same CapabilityTask + same now → same id (no RNG / no wall-clock).
        binding_id = canonical_id("binding", capability_id, self.provider_id, now)
        decision = _backend_for(capability_task, **selector_kwargs)
        backend = decision.get("backend")
        return BindingResult(
            binding_id=binding_id, capability_id=capability_id, target=self.provider_id, backend=backend,
            status="bound", serves_truth=BINDING_SERVES_TRUTH,
            detail={"bound_at": now, "backend_decision": decision,
                    "worker_bucket": _selector_task(capability_task)["worker_bucket"],
                    "wiring": "local_function_emulator", "proposal_only": True,
                    "note": "execution backend chosen by policy via select_backend; backend is switchable "
                            "(local↔k8s↔cloud-function) without changing the CapabilityTask"})


class CandidateBinding:
    """A candidate binding target (Nitric/Score/Temporal/Knative/KEDA/Kratix) built from a registry card.
    NEVER imported, executed, or reached over the network. ``bind`` returns (NOT raises) a
    :class:`BindingUnavailableResult` naming the owner-gated / ``env://`` reason, while still reporting the
    ``backend_would_be`` the policy WOULD have selected (honest degradation)."""

    def __init__(self, card: dict) -> None:
        self._card = card
        self.provider_id = card["target"]

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "target": self.provider_id, "role": "candidate",
                "kind": self._card.get("kind"), "status": "candidate", "imported": False, "executed": False,
                "serves_truth": BINDING_SERVES_TRUTH, "ref": self._card.get("ref")}

    def status(self) -> dict:
        return {"provider_id": self.provider_id, "target": self.provider_id, "status": "candidate",
                "imported": False, "executed": False, "ref": self._card.get("ref")}

    def bind(self, capability_task: dict, *, now: str, **selector_kwargs) -> BindingUnavailableResult:
        decision = _backend_for(capability_task, **selector_kwargs)
        reason = (f"target {self.provider_id!r} ({self._card.get('kind')}) is a catalog candidate only — not "
                  f"imported/executed/reached in this repo; real binding is owner-gated ({self._card.get('ref')})")
        return BindingUnavailableResult(
            target=self.provider_id, reason=reason, ref=self._card.get("ref"),
            backend_would_be=decision.get("backend"), consumable=False, serves_truth=BINDING_SERVES_TRUTH,
            detail={"checked_at": now, "backend_decision": decision, "kind": self._card.get("kind")})


def get_binding(target: str):
    """Return a binding provider for ``target``: the live :class:`LocalFunctionBinding` for the one active
    target, a :class:`CandidateBinding` for a known candidate card, or ``None`` for an unknown target."""
    card = target_card(target)
    if card is None:
        return None
    if card.get("status") == "active" and target == LOCAL_FUNCTION_TARGET:
        return LocalFunctionBinding()
    return CandidateBinding(card)


def bind_capability_task(capability_task: dict, *, target: str = LOCAL_FUNCTION_TARGET, now: str,
                         **selector_kwargs):
    """Dispatch: resolve ``target`` → run the active :class:`LocalFunctionBinding` (returns a
    :class:`BindingResult`), or degrade gracefully for a candidate / unknown target (returns a
    :class:`BindingUnavailableResult`). NEVER crashes; NEVER imports/executes a candidate target. Deterministic
    when ``now`` is injected. ``selector_kwargs`` (policy_matrix/pricebook/provider_health/available_creds/
    policy_override) are passed straight through to the policy selector — the ONE place backend choice lives."""
    provider = get_binding(target)
    if provider is None:
        # unknown target: still report the backend the policy WOULD pick (honest plan), never crash.
        decision = _backend_for(capability_task, **selector_kwargs)
        return BindingUnavailableResult(
            target=target, reason=f"unknown binding target {target!r} (not in TARGETS registry)",
            ref=None, backend_would_be=decision.get("backend"), consumable=False,
            serves_truth=BINDING_SERVES_TRUTH,
            detail={"checked_at": now, "known_targets": sorted(TARGETS)})
    return provider.bind(capability_task, now=now, **selector_kwargs)


__all__ = [
    "TARGETS",
    "target_card",
    "get_binding",
    "bind_capability_task",
    "LocalFunctionBinding",
    "CandidateBinding",
]
