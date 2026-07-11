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
from src.teleon.runtime.execution_backend_selector import py_function_src_teleon_runtime_execution_backend_selector__generic_functions, py_function_src_teleon_runtime_execution_backend_selector__select_backend

#: the binding-target registry (CONFIG-shaped data, not code). The local function emulator is the one ACTIVE
#: target; the rest are CANDIDATE cards naming the runtime the OWNER would have to authorize (an ``env://``
#: ref, never a value). A candidate is NEVER imported/executed/reached — its card only describes it.
py_const_src_teleon_runtime_capability_binding__TARGETS: dict[str, dict] = {
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


def py_function_src_teleon_runtime_capability_binding__target_card(py_arg_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__target_card__target: str) -> dict | None:
    """Return the registry card for ``target`` (or ``None`` for an unknown target)."""
    return py_const_src_teleon_runtime_capability_binding__TARGETS.get(py_arg_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__target_card__target)


def py_function_src_teleon_runtime_capability_binding___selector_task(py_arg_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__selector_task__capability_task: dict) -> dict:
    """Project a declared CapabilityTask onto the execution_backend_selector's task shape so the SAME numeric
    policy / pricebook / health / creds machinery picks the backend — no parallel selection logic here. The
    CapabilityTask declares intent + bounds; the selector turns that into a backend (the cloud-function/K8s
    wiring the author never has to write)."""
    py_local_src_teleon_runtime_capability_binding__selector_task__cap_id = str(py_arg_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__selector_task__capability_task.get("capability_id") or py_arg_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__selector_task__capability_task.get("id") or "capability_task")
    py_local_src_teleon_runtime_capability_binding__selector_task__bounds = py_arg_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__selector_task__capability_task.get("bounds") or {}
    return {
        "capability_id": f"capability_task::{py_local_src_teleon_runtime_capability_binding__selector_task__cap_id}",
        "worker_bucket": py_arg_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__selector_task__capability_task.get("worker_bucket", "utility"),
        "estimated_runtime_ms": int(py_arg_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__selector_task__capability_task.get("estimated_runtime_ms",
                                                         py_local_src_teleon_runtime_capability_binding__selector_task__bounds.get("estimated_runtime_ms", 500))),
        "requires_browser": bool(py_arg_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__selector_task__capability_task.get("requires_browser")),
        "requires_gpu": bool(py_arg_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__selector_task__capability_task.get("requires_gpu")),
        "tenant_private": bool(py_arg_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__selector_task__capability_task.get("tenant_private")),
    }


def py_function_src_teleon_runtime_capability_binding___capability_id(py_arg_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__capability_id__capability_task: dict) -> str:
    return str(py_arg_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__capability_id__capability_task.get("capability_id") or py_arg_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__capability_id__capability_task.get("id") or "capability_task")


def py_function_src_teleon_runtime_capability_binding___backend_for(capability_task: dict, **selector_kwargs) -> dict:
    """DELEGATE backend choice to the policy selector (never reinvented). Computed for EVERY target — even a
    candidate — so callers always see which backend Teleon WOULD provision (honest degradation)."""
    return py_function_src_teleon_runtime_execution_backend_selector__select_backend(py_function_src_teleon_runtime_capability_binding___selector_task(capability_task), **selector_kwargs)


class py_class_src_teleon_runtime_capability_binding__LocalFunctionBinding:
    """ACTIVE golden path: bind a CapabilityTask onto the offline local function emulator. ``bind`` delegates
    the execution-backend choice to :func:`select_backend` (proving the target abstracts cloud/K8s wiring by
    POLICY) and records it in the :class:`BindingResult`. Deterministic when ``now`` is injected
    (``binding_id`` is content-addressed over (capability_id, target, now)). Output is a wiring decision,
    never truth (``serves_truth=False``)."""
    provider_id = LOCAL_FUNCTION_TARGET

    def describe(self) -> dict:
        py_local_src_teleon_runtime_capability_binding__py_class_src_teleon_runtime_capability_binding__LocalFunctionBinding_describe__card = py_const_src_teleon_runtime_capability_binding__TARGETS[LOCAL_FUNCTION_TARGET]
        return {"provider_id": self.provider_id, "target": self.provider_id, "role": "active",
                "kind": py_local_src_teleon_runtime_capability_binding__py_class_src_teleon_runtime_capability_binding__LocalFunctionBinding_describe__card["kind"], "status": "active", "imported": True, "executed": True,
                "serves_truth": BINDING_SERVES_TRUTH}

    def status(self) -> dict:
        return {"provider_id": self.provider_id, "target": self.provider_id, "status": "active",
                "imported": True, "executed": True, "ref": None}

    def bind(self, capability_task: dict, *, now: str, **selector_kwargs) -> BindingResult:
        py_local_src_teleon_runtime_capability_binding__py_class_src_teleon_runtime_capability_binding__LocalFunctionBinding_bind__capability_id = py_function_src_teleon_runtime_capability_binding___capability_id(capability_task)
        # deterministic binding id: same CapabilityTask + same now → same id (no RNG / no wall-clock).
        py_local_src_teleon_runtime_capability_binding__py_class_src_teleon_runtime_capability_binding__LocalFunctionBinding_bind__binding_id = canonical_id("binding", py_local_src_teleon_runtime_capability_binding__py_class_src_teleon_runtime_capability_binding__LocalFunctionBinding_bind__capability_id, self.provider_id, now)
        py_local_src_teleon_runtime_capability_binding__py_class_src_teleon_runtime_capability_binding__LocalFunctionBinding_bind__decision = py_function_src_teleon_runtime_capability_binding___backend_for(capability_task, **selector_kwargs)
        py_local_src_teleon_runtime_capability_binding__py_class_src_teleon_runtime_capability_binding__LocalFunctionBinding_bind__backend = py_local_src_teleon_runtime_capability_binding__py_class_src_teleon_runtime_capability_binding__LocalFunctionBinding_bind__decision.get("backend")
        return BindingResult(
            binding_id=py_local_src_teleon_runtime_capability_binding__py_class_src_teleon_runtime_capability_binding__LocalFunctionBinding_bind__binding_id, capability_id=py_local_src_teleon_runtime_capability_binding__py_class_src_teleon_runtime_capability_binding__LocalFunctionBinding_bind__capability_id, target=self.provider_id, backend=py_local_src_teleon_runtime_capability_binding__py_class_src_teleon_runtime_capability_binding__LocalFunctionBinding_bind__backend,
            status="bound", serves_truth=BINDING_SERVES_TRUTH,
            detail={"bound_at": now, "backend_decision": py_local_src_teleon_runtime_capability_binding__py_class_src_teleon_runtime_capability_binding__LocalFunctionBinding_bind__decision,
                    "worker_bucket": py_function_src_teleon_runtime_capability_binding___selector_task(capability_task)["worker_bucket"],
                    "wiring": "local_function_emulator", "proposal_only": True,
                    "note": "execution backend chosen by policy via select_backend; backend is switchable "
                            "(local↔k8s↔cloud-function) without changing the CapabilityTask"})


class py_class_src_teleon_runtime_capability_binding__CandidateBinding:
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
        py_local_src_teleon_runtime_capability_binding__py_class_src_teleon_runtime_capability_binding__CandidateBinding_bind__decision = py_function_src_teleon_runtime_capability_binding___backend_for(capability_task, **selector_kwargs)
        py_local_src_teleon_runtime_capability_binding__py_class_src_teleon_runtime_capability_binding__CandidateBinding_bind__reason = (f"target {self.provider_id!r} ({self._card.get('kind')}) is a catalog candidate only — not "
                  f"imported/executed/reached in this repo; real binding is owner-gated ({self._card.get('ref')})")
        return BindingUnavailableResult(
            target=self.provider_id, reason=py_local_src_teleon_runtime_capability_binding__py_class_src_teleon_runtime_capability_binding__CandidateBinding_bind__reason, ref=self._card.get("ref"),
            backend_would_be=py_local_src_teleon_runtime_capability_binding__py_class_src_teleon_runtime_capability_binding__CandidateBinding_bind__decision.get("backend"), consumable=False, serves_truth=BINDING_SERVES_TRUTH,
            detail={"checked_at": now, "backend_decision": py_local_src_teleon_runtime_capability_binding__py_class_src_teleon_runtime_capability_binding__CandidateBinding_bind__decision, "kind": self._card.get("kind")})


def py_function_src_teleon_runtime_capability_binding__get_binding(py_arg_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__get_binding__target: str):
    """Return a binding provider for ``target``: the live :class:`LocalFunctionBinding` for the one active
    target, a :class:`CandidateBinding` for a known candidate card, or ``None`` for an unknown target."""
    py_local_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__get_binding__card = py_function_src_teleon_runtime_capability_binding__target_card(py_arg_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__get_binding__target)
    if py_local_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__get_binding__card is None:
        return None
    if py_local_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__get_binding__card.get("status") == "active" and py_arg_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__get_binding__target == LOCAL_FUNCTION_TARGET:
        return py_class_src_teleon_runtime_capability_binding__LocalFunctionBinding()
    return py_class_src_teleon_runtime_capability_binding__CandidateBinding(py_local_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__get_binding__card)


def py_function_src_teleon_runtime_capability_binding__bind_capability_task(capability_task: dict, *, target: str = LOCAL_FUNCTION_TARGET, now: str,
                         **selector_kwargs):
    """Dispatch: resolve ``target`` → run the active :class:`LocalFunctionBinding` (returns a
    :class:`BindingResult`), or degrade gracefully for a candidate / unknown target (returns a
    :class:`BindingUnavailableResult`). NEVER crashes; NEVER imports/executes a candidate target. Deterministic
    when ``now`` is injected. ``selector_kwargs`` (policy_matrix/pricebook/provider_health/available_creds/
    policy_override) are passed straight through to the policy selector — the ONE place backend choice lives."""
    py_local_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__bind_capability_task__provider = py_function_src_teleon_runtime_capability_binding__get_binding(target)
    if py_local_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__bind_capability_task__provider is None:
        # unknown target: still report the backend the policy WOULD pick (honest plan), never crash.
        py_local_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__bind_capability_task__decision = py_function_src_teleon_runtime_capability_binding___backend_for(capability_task, **selector_kwargs)
        return BindingUnavailableResult(
            target=target, reason=f"unknown binding target {target!r} (not in TARGETS registry)",
            ref=None, backend_would_be=py_local_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__bind_capability_task__decision.get("backend"), consumable=False,
            serves_truth=BINDING_SERVES_TRUTH,
            detail={"checked_at": now, "known_targets": sorted(py_const_src_teleon_runtime_capability_binding__TARGETS)})
    return py_local_src_teleon_runtime_capability_binding__py_function_src_teleon_runtime_capability_binding__bind_capability_task__provider.bind(capability_task, now=now, **selector_kwargs)


__all__ = [
    "py_const_src_teleon_runtime_capability_binding__TARGETS",
    "py_function_src_teleon_runtime_capability_binding__target_card",
    "py_function_src_teleon_runtime_capability_binding__get_binding",
    "py_function_src_teleon_runtime_capability_binding__bind_capability_task",
    "py_class_src_teleon_runtime_capability_binding__LocalFunctionBinding",
    "py_class_src_teleon_runtime_capability_binding__CandidateBinding",
]
