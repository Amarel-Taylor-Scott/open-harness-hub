"""src.teleon.ports.capability_binding_provider — the CapabilityTask BINDING port (canonical TELEON home).

A *binding* attaches a declared **CapabilityTask** (the WHAT — intent + bounds, declared once) to an
execution **TARGET** (the HOW-it-is-wired — local function now; Nitric / Score / Temporal / Knative / KEDA /
Kratix later). The point is that the CapabilityTask author NEVER writes cloud-function or Kubernetes-worker
code: they declare intent through this contract, and a binding provider wires it onto a target whose actual
execution backend is chosen by POLICY (delegated to
:func:`src.teleon.runtime.execution_backend_selector.select_backend` — open-ended/guarded buckets stay off
generic cloud functions). Local-now vs cloud-/K8s-later is a target + policy choice, never a code rewrite.

Two providers sit behind this port (mirroring the agent-runtime + execution-provider ports):

* the **active golden path** binds onto the offline local function emulator and is deterministic when ``now``
  is injected (content-addressed ``binding_id``; no RNG / no wall-clock);
* a **candidate** target (Nitric/Score/Temporal/Knative/KEDA/Kratix) is a CATALOG CARD only — never imported,
  never executed, never reached over the network. Its ``bind`` returns (NOT raises) a
  :class:`BindingUnavailableResult` naming the owner-gated / ``env://`` reason, while still reporting the
  ``backend_would_be`` the policy WOULD have selected (honest degradation).

THE INVARIANT: **a binding is a wiring decision, never a fact.** Every binding output carries
``serves_truth=False`` (``BINDING_SERVES_TRUTH``); a binding NEVER produces a CanonicalFact/ContextResponse.
Runtime binding is a Teleon concern; Baltor is a TENANT that declares CapabilityTasks through this port —
this module imports only the stdlib + Teleon runtime selection and NEVER ``src.baltor``. Stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

#: pinned False on every binding output — THE INVARIANT, made a constant the proofs assert.
BINDING_SERVES_TRUTH = False
#: the one ACTIVE binding target (offline correctness invariant): the local function emulator family.
LOCAL_FUNCTION_TARGET = "local_function@v1"


@dataclass(frozen=True)
class BindingResult:
    """A successful binding of a CapabilityTask to a target. ``backend`` is the execution backend the policy
    selector chose for the bound task (proving the target abstracts cloud-function/K8s wiring by policy).
    ``serves_truth`` is pinned False: a binding is a wiring decision, never a fact."""
    binding_id: str
    capability_id: str
    target: str
    backend: str
    status: str = "bound"     # bound | unavailable
    serves_truth: bool = BINDING_SERVES_TRUTH
    detail: dict = field(default_factory=dict)


@dataclass(frozen=True)
class BindingUnavailableResult:
    """Returned (NOT raised) when a candidate target has no runtime/owner-authorization in this repo, or the
    target is unknown. Non-consumable: graceful degradation, never a crash. ``ref`` is an ``env://…``
    reference (never a value); ``backend_would_be`` reports which backend the policy WOULD have selected so the
    caller can SEE the honest plan even though nothing was wired."""
    target: str
    reason: str
    ref: str | None = None
    backend_would_be: str | None = None
    consumable: bool = False
    serves_truth: bool = BINDING_SERVES_TRUTH
    detail: dict = field(default_factory=dict)


@runtime_checkable
class CapabilityTaskBindingProvider(Protocol):
    """One binding provider: it wires a declared CapabilityTask onto a target. The active provider binds onto
    the local function emulator and returns a :class:`BindingResult` (``serves_truth=False``); a candidate
    provider returns a :class:`BindingUnavailableResult` (never imported/executed). ``describe``/``status``
    report the target's role + availability. Deterministic when ``now`` is injected."""
    provider_id: str

    def describe(self) -> dict: ...
    def status(self) -> dict: ...
    def bind(self, capability_task: dict, *, now: str) -> dict: ...


__all__ = [
    "CapabilityTaskBindingProvider",
    "BindingResult",
    "BindingUnavailableResult",
    "BINDING_SERVES_TRUTH",
    "LOCAL_FUNCTION_TARGET",
]
