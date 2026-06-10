"""src.teleon.ports.stateful_swarm_provider — the SHARED STATEFUL-SWARM runner port (canonical TELEON home).

A stateful swarm runs many BOUNDED workers against ONE shared, append-only, provenance-tracked blackboard (see
:class:`~src.teleon.ports.blackboard_provider.BlackboardProviderPort`) so the workers build persistent typed
source-backed STATE instead of re-reading docs at every handoff. A worker POSTS a typed entry (signal /
observation / gap / analysis / synthesis) onto the blackboard under a MANDATORY worker receipt; the NEXT worker
reads the BLACKBOARD (not the raw docs) and posts the next entry. Teleon RUNS the swarm as a runtime substrate;
Baltor GOVERNS what (if anything) becomes served truth.

THE INVARIANT (mirrors the blackboard / agent-runtime / environment ports): **a swarm run produces analytical
WORKING STATE, never served truth.** Every result carries ``serves_truth=False`` — a worker DISCOVERS/REASONS and
PROPOSES onto the blackboard; Baltor STORES/VERIFIES/RECONCILES/CONSUMES separately (the served-truth decision is
a distinct, gated step keyed off ``GovernedBlackboardEntry.promotion_eligible``, which itself never makes an entry
truth). Held-out / minority / stale items are PRESERVED as warnings (lossless distillation), never merged into the
served answer.

The deterministic OFFLINE :class:`~src.teleon.stateful_swarms.local_swarm.LocalStatefulSwarm` is the correctness
invariant + the local-first golden path (``swarm.local_stub@v1``, the single active runner in
``architecture/stateful_swarm_provider_catalog.json``). External/hosted swarm runners (e.g. Irys Stateful Swarms)
are CANDIDATES behind this same port — catalog/config concerns, never imported or executed here.

Teleon-owned: imports only the stdlib — never Baltor. Deterministic when ``now`` is injected (content-addressed
ids; no RNG / no wall-clock here). Stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

#: pinned False on every swarm run output — THE INVARIANT, made a constant the proofs assert. A swarm run is
#: working state; only Baltor's separate governance + verification rail may promote anything derived from it.
SWARM_SERVES_TRUTH = False


@dataclass(frozen=True)
class SwarmWorkerResult:
    """The structured outcome of ONE bounded worker's turn on the shared blackboard.

    A worker reads the blackboard, posts zero-or-more typed entries (under a mandatory receipt), and reports what
    it wrote. ``serves_truth`` is pinned False: a worker proposes onto the blackboard, it never serves truth.
    ``entry_ids`` are the BlackboardEntry ids it appended; ``receipt_id`` is the BlackboardWorkerReceipt backing
    the turn; ``read_entry_ids`` records which blackboard entries the worker consumed (so a synthesis worker can
    prove it read the BOARD, not the raw docs).
    """
    worker_id: str
    worker_kind: str
    entry_ids: tuple = ()
    receipt_id: str | None = None
    read_entry_ids: tuple = ()
    serves_truth: bool = False
    detail: dict = field(default_factory=dict)


@runtime_checkable
class StatefulSwarmProviderPort(Protocol):
    """One stateful-swarm runner the spine MAY route an analytical task to.

    ``run`` orchestrates the bounded workers writing to the shared blackboard ``blackboard_id`` and returns an
    envelope dict ``{provider_id, blackboard_id, task, worker_results, synthesis_entry_id, governed_entry,
    serves_truth, ...}`` — ``serves_truth`` is pinned False (the run produced analytical state, not truth). Every
    worker writes a BlackboardWorkerReceipt to the blackboard; the synthesis worker reads BLACKBOARD ENTRIES (not
    the raw docs). Deterministic when ``now`` is injected (content-addressed ids; no RNG / no wall-clock). A
    candidate (external/hosted) runner degrades gracefully — it never crashes and never serves truth.
    """

    provider_id: str

    def describe(self) -> dict:
        """Static capability card: ``{provider_id, name, status, requires_network, requires_keys,
        local_equivalent, serves_truth}`` — the local-first golden-path shape (serves_truth const False)."""
        ...

    def run(self, task: str, *, blackboard_id: str, now: str) -> dict:
        """Orchestrate the bounded workers writing typed entries to the blackboard ``blackboard_id`` for ``task``.

        Returns an envelope dict (``serves_truth`` pinned False). Each worker posts entries under a MANDATORY
        receipt; the synthesis worker reads the BLACKBOARD (not raw docs). Deterministic when ``now`` is injected.
        """
        ...


__all__ = [
    "StatefulSwarmProviderPort",
    "SwarmWorkerResult",
    "SWARM_SERVES_TRUTH",
]
