#!/usr/bin/env python3
"""src.baltor.distillation.rollback — rollback moves the active pointer only; it never deletes anything.

The lossless law: *rollback is always available; it moves the active pointer only and never deletes the
promoted candidate or prior responses.* A :class:`RollbackPlan` names a ``key`` plus the ``from_id`` (the
currently-active, promoted candidate) and the ``to_id`` (the baseline / prior active version to restore).
``execute(store, plan)`` calls ``LosslessStore.set_current`` — which re-points only — then writes a rollback
**receipt** as a new derived entry (so the rollback itself is lossless and auditable).

What rollback NEVER does: delete the promoted candidate, delete any prior version, or make an old
``ContextResponse`` unreadable. After a rollback both ``get(from_id)`` and ``get(to_id)`` still resolve, and
``versions(key)`` is unchanged in length. Deterministic (injected ``now``, hashlib receipt id, no RNG).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from src.baltor.distillation.lossless_store import EPOCH, DistillationStoreError, LosslessStore


@dataclass
class RollbackPlan:
    """A plan to move ``key``'s active pointer from the promoted candidate back to a prior/baseline version.

    ``from_id`` must currently be the active pointer for ``key``; ``to_id`` must be an existing prior version
    of the same key. Building the plan validates nothing destructive will happen — execution only re-points.
    """
    key: str
    tenant_id: str
    from_id: str          # the currently-active (promoted) candidate — NOT deleted by rollback
    to_id: str            # the baseline / prior active version to restore
    reason: str = ""

    def to_dict(self) -> dict:
        return {"key": self.key, "tenant_id": self.tenant_id, "from_id": self.from_id,
                "to_id": self.to_id, "reason": self.reason}

    @staticmethod
    def of(store: LosslessStore, *, key: str, tenant: str, to_id: str, reason: str = "") -> "RollbackPlan":
        """Build a plan rolling ``key`` back to ``to_id`` (the current active id becomes ``from_id``)."""
        current = store.current_id(key, tenant=tenant)
        if current is None:
            raise DistillationStoreError(f"key {key!r} has no active version to roll back from")
        versions = {e.entry_id for e in store.versions(key, tenant=tenant)}
        if to_id not in versions:
            raise DistillationStoreError(f"rollback target {to_id!r} is not a version of key {key!r}")
        return RollbackPlan(key=key, tenant_id=tenant, from_id=current, to_id=to_id, reason=reason)


@dataclass
class RollbackReceipt:
    receipt_id: str
    key: str
    tenant_id: str
    rolled_from_id: str
    rolled_to_id: str
    reason: str
    receipt_entry_id: str       # the lossless-store entry the receipt was written as
    candidate_preserved: bool   # ALWAYS true — rollback never deletes the candidate
    created_at: str
    schema_version: str = "RollbackReceipt"

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "receipt_id": self.receipt_id, "key": self.key,
                "tenant_id": self.tenant_id, "rolled_from_id": self.rolled_from_id,
                "rolled_to_id": self.rolled_to_id, "reason": self.reason,
                "receipt_entry_id": self.receipt_entry_id,
                "candidate_preserved": self.candidate_preserved, "created_at": self.created_at}


def execute(store: LosslessStore, plan: RollbackPlan, *, now: str = EPOCH) -> RollbackReceipt:
    """Execute a rollback: move ``key``'s active pointer ``from_id`` → ``to_id`` and write a receipt.

    Lossless guarantees enforced here:

    * the pointer is the ONLY thing that moves (``store.set_current``);
    * the promoted candidate (``from_id``) is NOT deleted — verified still present after the move;
    * a rollback **receipt** is appended as a new derived entry (the rollback is itself auditable);
    * the receipt's lineage links both the restored baseline and the (still-present) candidate.
    """
    # guard: from_id must be the live pointer (rolling back something that isn't active is a logic error).
    live = store.current_id(plan.key, tenant=plan.tenant_id)
    if live != plan.from_id:
        raise DistillationStoreError(
            f"rollback from_id {plan.from_id!r} is not the active pointer ({live!r}) for key {plan.key!r}")

    # the ONLY mutation: re-point the active version. set_current deletes nothing.
    prior = store.set_current(plan.key, plan.to_id, tenant=plan.tenant_id)

    # the candidate must still exist after the move (lossless invariant, asserted not assumed).
    candidate_preserved = store.has(plan.from_id)
    if not candidate_preserved:
        raise DistillationStoreError("INVARIANT VIOLATION: rollback removed the promoted candidate")

    rid = "rbkrcpt-" + hashlib.sha256(json.dumps(
        {"key": plan.key, "tenant": plan.tenant_id, "from": plan.from_id, "to": plan.to_id},
        sort_keys=True).encode()).hexdigest()[:16]
    body = {"receipt_id": rid, "rolled_from_id": plan.from_id, "rolled_to_id": plan.to_id,
            "prior_pointer_id": prior, "reason": plan.reason, "candidate_preserved": candidate_preserved}
    # the receipt is itself a lossless layer: a derived entry whose lineage reaches BOTH baseline + candidate,
    # carrying the candidate as a rollback_target so the move is fully reconstructable. Its scope matches the
    # baseline being restored (never promotes a private candidate into a public lineage).
    to_entry = store.get(plan.to_id, tenant=plan.tenant_id)
    receipt_entry = store.put_derived(
        plan.tenant_id, key=f"{plan.key}#rollback-receipt", body=body,
        parent_ids=[plan.to_id, plan.from_id], scope=to_entry.scope, transform_type="rollback",
        transform_run_id=rid, rollback_target_ids=[plan.from_id], role="rollback_receipt", now=now)

    return RollbackReceipt(receipt_id=rid, key=plan.key, tenant_id=plan.tenant_id,
                           rolled_from_id=plan.from_id, rolled_to_id=plan.to_id, reason=plan.reason,
                           receipt_entry_id=receipt_entry.entry_id, candidate_preserved=candidate_preserved,
                           created_at=now)
