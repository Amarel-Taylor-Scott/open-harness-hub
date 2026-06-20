"""src.baltor.ports.sync_planner — the SyncPlannerPort capability interface.

A sync planner decides WHAT a connector should fetch next: a full sweep, an incremental window from a cursor, or
a bounded backfill. It reads the durable SyncState (SyncState.v1), emits an IngestionRun plan + a SyncCursor
(SyncCursor.v1), and applies a cursor back onto state idempotently. It NEVER fetches and NEVER writes served
facts — it only computes windows so ingestion stays incremental, resumable, and replayable.

Determinism: planners take an injected `now` (no wall-clock) and content-address run ids; the same state + inputs
always yield the same plan. Tenant isolation: a tenant_private source's cursor never advances a global_public one.
Stdlib only.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SyncPlannerPort(Protocol):
    """Compute and apply sync windows for a (tenant, source). Pure planning — no fetch, no fact writes."""

    def plan_full_sync(self, *, tenant_id: str, source_id: str, scope: str, sync_state: dict[str, Any] | None,
                       now: str) -> dict[str, Any]:
        """Plan a complete re-read of the source (ignores the existing cursor; resets the high-water mark).
        Returns an IngestionRun.v1-shaped plan with sync_mode='full_sync'. `now` injected."""
        ...

    def plan_incremental_sync(self, *, tenant_id: str, source_id: str, scope: str,
                              sync_state: dict[str, Any], now: str) -> dict[str, Any]:
        """Plan a delta read from the current cursor in `sync_state`. Returns an IngestionRun.v1-shaped plan
        (sync_mode='incremental_sync') whose from_cursor is the state's high-water mark. `now` injected."""
        ...

    def plan_backfill(self, *, tenant_id: str, source_id: str, scope: str, from_cursor: dict[str, Any],
                      to_cursor: dict[str, Any], now: str) -> dict[str, Any]:
        """Plan a bounded historical sweep between two explicit cursors (does NOT move the live high-water mark).
        Returns an IngestionRun.v1-shaped plan with sync_mode='backfill'. `now` injected."""
        ...

    def apply_cursor(self, *, sync_state: dict[str, Any], cursor: dict[str, Any], run_id: str,
                     now: str) -> dict[str, Any]:
        """Fold a completed run's SyncCursor.v1 into SyncState.v1 and return the new state. Idempotent: applying
        a cursor that is <= the current high-water mark is a no-op (returns equivalent state). `now` injected."""
        ...
