"""src.baltor.distillation — the lossless-distillation CORE subsystem.

Makes the [[lossless-distillation-law]] (``docs/codex/lossless-distillation.md``) a CHECKABLE subsystem:
distillation is never replacement. Every transform creates a NEW derived layer while preserving raw +
source + intermediates + lineage + held-out + rejected + receipts + rollback target. Nothing is
overwritten; every derived artifact rehydrates to its source.

This package owns the runtime (Lane B):

* :class:`~src.baltor.distillation.lossless_store.LosslessStore` — append-only, content-addressed
  (sha256) raw/source/derived store; ``set_current`` moves a pointer WITHOUT deleting any prior version;
  ``rehydrate_payload`` returns exact bytes; tenant-scoped; ``tenant_private`` never enters a
  ``global_public`` lineage.
* :class:`~src.baltor.distillation.lineage.LineageBundle` — reaches raw/source ids + source_handles +
  transform_run_ids + receipts + prior_version_ids + rollback_target_ids + held_out/rejected ids.
* :func:`~src.baltor.distillation.rehydration.rehydrate` — ``{raw, source, parents, held_out, rejected,
  receipts}`` for an artifact, never crossing a tenant boundary.
* :class:`~src.baltor.distillation.rollback.RollbackPlan` + ``execute`` — moves the current pointer only;
  never deletes the promoted candidate or prior responses; writes a rollback receipt.

Stdlib only, deterministic (injected ``now``, hashlib ids, no RNG), fully offline.
"""
from __future__ import annotations

from src.baltor.distillation.lineage import LineageBundle
from src.baltor.distillation.lossless_store import (
    GLOBAL_PUBLIC,
    TENANT_PRIVATE,
    DistillationStoreError,
    LosslessStore,
    LosslessStoreEntry,
    TenantBoundaryError,
)
from src.baltor.distillation.rehydration import RehydrationError, rehydrate
from src.baltor.distillation.rollback import RollbackPlan, execute

__all__ = [
    "LosslessStore",
    "LosslessStoreEntry",
    "DistillationStoreError",
    "TenantBoundaryError",
    "GLOBAL_PUBLIC",
    "TENANT_PRIVATE",
    "LineageBundle",
    "rehydrate",
    "RehydrationError",
    "RollbackPlan",
    "execute",
]
