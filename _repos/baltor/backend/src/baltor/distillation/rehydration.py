#!/usr/bin/env python3
"""src.baltor.distillation.rehydration — prove that every derived artifact rehydrates to its source.

The lossless law forbids *distillation without a rehydration path*. ``rehydrate(store, artifact_id, tenant)``
walks one artifact's lineage and returns the layers it was distilled from —

    {raw, source, parents, held_out, rejected, receipts}

— so an atomic fact rehydrates to its source field and raw record, an optimized pack rehydrates to its
baseline, and a held-out FAQ rehydrates to the source it was held out of plus the reconciliation receipt
that held it. ``rehydrate_payload`` (re-exported from the store) returns the EXACT raw bytes.

Rehydration is tenant-scoped and NEVER crosses a tenant boundary: ``tenant`` is required and is passed to
every store read, so a caller for tenant A cannot rehydrate tenant B's raw/source layers. Pure projection
(no clock, no RNG) → deterministic.
"""
from __future__ import annotations

from src.baltor.distillation.lineage import LineageBundle
from src.baltor.distillation.lossless_store import LosslessStore, TenantBoundaryError

RehydrationError = TenantBoundaryError  #: rehydration failures are tenant-boundary failures


def rehydrate(store: LosslessStore, artifact_id: str, tenant: str) -> dict:
    """Rehydrate ``artifact_id`` for ``tenant`` → ``{artifact, raw, source, parents, held_out, rejected,
    receipts, bundle}``. Returns the actual store entries (as dicts) the artifact was distilled from.

    Tenant-scoped end to end: every read passes ``tenant`` so the walk cannot cross a tenant boundary; a
    cross-tenant request raises ``RehydrationError`` (a :class:`TenantBoundaryError`).
    """
    if not tenant:
        raise RehydrationError("tenant is required to rehydrate (no anonymous cross-tenant rehydration)")
    bundle = LineageBundle.build(store, artifact_id, tenant=tenant)

    def _entries(ids):
        # every read is tenant-scoped; a foreign-tenant id raises before any payload is returned.
        return [store.get(i, tenant=tenant).to_dict() for i in ids]

    artifact = store.get(artifact_id, tenant=tenant)
    return {
        "artifact": artifact.to_dict(),
        "raw": _entries(bundle.raw_ids),
        "source": _entries(bundle.source_ids),
        "parents": _entries(bundle.parent_ids),
        "held_out": _entries(bundle.held_out_ids),
        "rejected": _entries(bundle.rejected_ids),
        "receipts": list(bundle.receipt_ids),
        "bundle": bundle.to_dict(),
    }


def rehydrate_payload(store: LosslessStore, artifact_id: str, tenant: str) -> bytes:
    """Return the EXACT raw bytes behind an artifact (follows ``payload_ref`` to the nearest raw layer).

    Tenant-scoped: both the lineage walk and the object-store read are checked against ``tenant`` so the
    bytes can never be pulled across a tenant boundary."""
    if not tenant:
        raise RehydrationError("tenant is required to rehydrate raw bytes")
    bundle = LineageBundle.build(store, artifact_id, tenant=tenant)
    for rid in bundle.raw_ids:
        raw = store.get(rid, tenant=tenant)
        if raw.payload_ref:
            return store.rehydrate_payload(raw.payload_ref, tenant=tenant)
    raise RehydrationError(f"no raw payload_ref reachable from {artifact_id!r}")
