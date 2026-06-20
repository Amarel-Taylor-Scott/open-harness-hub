"""src.baltor.ports.source_adapter — the SourceAdapterPort capability interface.

A source adapter is the ONLY thing that touches a raw upstream source. It turns a fetched object into governed
SourceArtifacts (SourceArtifact.v1) carrying tenant_id/source_id/source_version/source_handle/content_hash/scope/
authority/lineage/security — and NOTHING ELSE. It never writes final served facts, never bypasses the artifact
ledger, and never lets a tenant_private source update global_public. Decomposition → ledger → gate happen downstream.

This is the typed, reusable Protocol home for the seam whose current working implementation lives at
``scripts/ingest/source_adapters.py`` (the ``SourceAdapter`` Protocol + ``normalize()``). New adapters describe
themselves here; the in-repo registry routes to them. Stdlib only, no implementation that bypasses the port.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SourceAdapterPort(Protocol):
    """One governed source connector. Every method is side-effect-bounded to producing SourceArtifacts /
    plans / health — never served facts. Implementations MUST be deterministic when time is injected."""

    #: stable adapter identity, e.g. "source.cfpb_structured@v1" (matches the connector catalog adapter_id).
    adapter_id: str
    #: the source class this adapter handles, e.g. "cfpb_structured" / "csv_table" / "webhook_json".
    source_class: str

    def describe(self) -> dict[str, Any]:
        """Return the static capability card: adapter_id, source_class, supported sync_modes, cursor_strategy,
        idempotency_strategy, default scope/authority, and input/output contract refs. No I/O."""
        ...

    def plan(self, *, tenant_id: str, source_id: str, scope: str, authority: str,
             sync_mode: str, cursor: dict[str, Any] | None, now: str) -> dict[str, Any]:
        """Produce a deterministic IngestionRun plan (run_id, mode, cursor window) for this source WITHOUT
        fetching. `now` is injected — no wall-clock. Returns an IngestionRun.v1-shaped dict (status='planned')."""
        ...

    def scan(self, *, tenant_id: str, source_id: str, scope: str, cursor: dict[str, Any] | None,
             now: str) -> list[dict[str, Any]]:
        """Cheaply enumerate candidate items in the cursor window (locator + upstream metadata, no full bodies),
        so the planner can size/dedupe a sync before fetching. Returns a list of lightweight item descriptors."""
        ...

    def fetch(self, *, tenant_id: str, source_id: str, scope: str, locator: str,
              now: str) -> bytes | str | dict[str, Any]:
        """Fetch ONE raw object by locator. May read from an upstream OR a deterministic local fixture when the
        real source is unavailable (the fixture stays behind the same port). Returns the raw payload only."""
        ...

    def normalize(self, payload: Any, *, tenant_id: str, source_id: str, source_version: str,
                  scope: str, authority: str, now: str) -> dict[str, Any]:
        """Turn one raw payload into governed SourceArtifact.v1 records + the per-type source handles. MUST set
        tenant_id/source_id/source_version/source_handle/content_hash/scope/authority on every artifact and MUST
        NOT emit any served/promotion-final fact. Returns {'consumable', 'source_artifacts', 'artifacts', ...}.
        A source whose parser is a cataloged candidate returns consumable=False with a reason + the raw stored."""
        ...

    def health(self) -> dict[str, Any]:
        """Return liveness/reachability for this connector: {'status': healthy|degraded|unavailable,
        'using_fixture': bool, 'detail': str}. Used by the catalog/maturity matrix; never raises on a dead source."""
        ...
