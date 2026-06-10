"""src.teleon.ports.blackboard_provider — the SHARED GOVERNED-BLACKBOARD provider port (canonical TELEON home).

A blackboard provider is the durable, typed analytical STATE substrate for one stateful-swarm task: a shared
workspace where bounded workers post signals, observations, gaps, calculations, analyses and a synthesis across
iterations (see ``schemas/blackboard/Blackboard.v1`` + ``BlackboardEntry.v1`` and the typed-body contracts).
The thesis: agents build persistent typed source-backed state (a blackboard) instead of re-reading docs every
turn. Teleon RUNS the blackboard as a runtime substrate; Baltor governs what (if anything) becomes served truth.

THE INVARIANT (mirrors the agent-runtime / environment ports): **a blackboard entry is analytical WORKING STATE,
never served truth.** Every stored entry carries ``serves_truth=False`` (pinned const false by the schema) — a
worker DISCOVERS/REASONS and PROPOSES onto the blackboard; Baltor STORES/VERIFIES/RECONCILES/CONSUMES separately
(see ``GovernedBlackboardEntry.v1``, the governance seam — it never makes an entry truth either).

The store is APPEND-ONLY: entries are written once, with a mandatory :class:`BlackboardWorkerReceipt` recording
WHAT a worker did (never asserting the entries are true). There is no update and no delete — provenance is
tamper-evident. Governance violations (a sourceless observation, an attempt to set ``serves_truth`` true, a
mutate/delete, a missing tenant scope, a missing receipt) are REJECTED by raising :class:`BlackboardWriteRejected`.

The deterministic OFFLINE :class:`~src.teleon.blackboard.local_sqlite_blackboard.LocalSqliteBlackboard` is the
correctness invariant + the local-first golden path; external/hosted blackboard stores are CANDIDATES behind
this same port. Candidate stores are catalog/config concerns — never imported or executed here.

Teleon-owned: imports only the stdlib (and Teleon id helpers via the modules that USE this port) — never Baltor.
Deterministic when ``now`` is injected (content-addressed ids; no RNG / no wall-clock here). Stdlib only.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

#: pinned False on every stored blackboard entry — THE INVARIANT, made a constant the proofs assert.
#: A blackboard is working state; only Baltor's separate governance + verification rail may promote anything
#: derived from it (and even ``GovernedBlackboardEntry`` keeps ``serves_truth`` const false).
BLACKBOARD_SERVES_TRUTH = False

#: the typed BlackboardEntry kinds (mirrors the ``BlackboardEntry.v1`` enum; single source for the providers).
KIND_SIGNAL = "signal"
KIND_OBSERVATION = "observation"
KIND_GAP = "gap"
KIND_CALCULATION = "calculation"
KIND_ANALYSIS = "analysis"
KIND_SYNTHESIS = "synthesis"
KIND_SOURCE = "source"
BLACKBOARD_ENTRY_KINDS = (
    KIND_SIGNAL,
    KIND_OBSERVATION,
    KIND_GAP,
    KIND_CALCULATION,
    KIND_ANALYSIS,
    KIND_SYNTHESIS,
    KIND_SOURCE,
)

#: the Blackboard.v1 status enum (open -> converged -> compressed). Single source for the providers.
STATUS_OPEN = "open"
STATUS_CONVERGED = "converged"
STATUS_COMPRESSED = "compressed"
BLACKBOARD_STATUSES = (STATUS_OPEN, STATUS_CONVERGED, STATUS_COMPRESSED)


class BlackboardWriteRejected(Exception):
    """A write was REJECTED by the blackboard's governance guards (the entry is not stored).

    Raised — not silently dropped — so the violation is visible and auditable. ``code`` is a stable,
    machine-checkable reason (graph data, not a display label): one of ``missing_tenant_scope`` |
    ``sourceless_observation`` | ``serves_truth_forbidden`` | ``append_only_violation`` | ``missing_receipt`` |
    ``unknown_blackboard`` | ``invalid_kind``. The blackboard stays append-only and truth-free; nothing was written.
    """

    #: stable reason codes (the single source — providers raise with one of these, proofs assert on them).
    MISSING_TENANT_SCOPE = "missing_tenant_scope"
    SOURCELESS_OBSERVATION = "sourceless_observation"
    SERVES_TRUTH_FORBIDDEN = "serves_truth_forbidden"
    APPEND_ONLY_VIOLATION = "append_only_violation"
    MISSING_RECEIPT = "missing_receipt"
    UNKNOWN_BLACKBOARD = "unknown_blackboard"
    INVALID_KIND = "invalid_kind"

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code  # stable machine-checkable reason; not a display label
        msg = f"blackboard write rejected [{code}]"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)


@runtime_checkable
class BlackboardProviderPort(Protocol):
    """One blackboard store the spine MAY route a stateful-swarm task's working state to.

    The store is APPEND-ONLY and truth-free. ``create_blackboard`` opens a tenant-scoped workspace;
    ``append_entry`` writes exactly one typed entry under a MANDATORY worker receipt (no update / no delete —
    a mutate or delete attempt raises :class:`BlackboardWriteRejected`); ``query`` returns stored entries in a
    DETERMINISTIC order; ``get_receipts`` returns the worker-turn provenance. Every stored entry carries
    ``serves_truth=False``. Deterministic when ``now`` is injected (content-addressed ids; no RNG / no wall-clock).
    A candidate (external/hosted) store degrades gracefully — it never crashes and never serves truth.
    """

    provider_id: str

    def describe(self) -> dict:
        """Static capability card: ``{provider_id, name, status, append_only, requires_network,
        local_equivalent, serves_truth}`` — the local-first golden-path shape (serves_truth const False)."""
        ...

    def create_blackboard(self, task: str, tenant_scope: str, *, now: str) -> dict:
        """Open a new tenant-scoped Blackboard.v1 workspace and return its row dict.

        ``tenant_scope`` is REQUIRED — working state is tenant-isolated and never crosses tenants; an empty
        scope raises :class:`BlackboardWriteRejected` (``missing_tenant_scope``). The blackboard is born
        ``status=open`` with ``entry_count=0``; its id is content-addressed from (task, tenant_scope, now).
        """
        ...

    def append_entry(
        self,
        blackboard_id: str,
        entry: dict,
        *,
        worker_receipt: dict,
        now: str,
    ) -> dict:
        """APPEND exactly one typed BlackboardEntry under a MANDATORY worker receipt; return the stored row.

        Governance guards (each raises :class:`BlackboardWriteRejected`, storing nothing): the entry must carry
        a non-empty ``tenant_scope`` (matching the blackboard); an ``observation`` must have non-empty
        ``source_refs``; the entry must NOT set ``serves_truth`` true; an attempt to re-write an existing
        ``entry_id`` with DIFFERENT content is an append-only violation (identical content is idempotent); a
        ``worker_receipt`` is required and is recorded. The stored entry's ``serves_truth`` is pinned False.
        Deterministic when ``now`` is injected.
        """
        ...

    def query(
        self,
        blackboard_id: str,
        *,
        kind: str | None = None,
        author_worker_id: str | None = None,
        iteration: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Return stored entries for ``blackboard_id`` in a DETERMINISTIC order (insertion order, then entry_id).

        Optional filters narrow by ``kind`` / ``author_worker_id`` / ``iteration``; ``limit`` caps the count.
        The same (store contents, filters) ALWAYS yields the same rows in the same order — the read is a pure
        projection of the append-only stream; nothing here is served truth.
        """
        ...

    def get_receipts(self, blackboard_id: str) -> list[dict]:
        """Return the :class:`BlackboardWorkerReceipt` rows for ``blackboard_id`` (worker-turn provenance), in a
        deterministic order. A receipt records WHAT a worker did; it never asserts the written entries are true."""
        ...


__all__ = [
    "BlackboardProviderPort",
    "BlackboardWriteRejected",
    "BLACKBOARD_SERVES_TRUTH",
    "BLACKBOARD_ENTRY_KINDS",
    "KIND_SIGNAL",
    "KIND_OBSERVATION",
    "KIND_GAP",
    "KIND_CALCULATION",
    "KIND_ANALYSIS",
    "KIND_SYNTHESIS",
    "KIND_SOURCE",
    "BLACKBOARD_STATUSES",
    "STATUS_OPEN",
    "STATUS_CONVERGED",
    "STATUS_COMPRESSED",
]
