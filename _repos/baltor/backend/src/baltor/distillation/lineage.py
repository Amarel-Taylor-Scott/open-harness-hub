#!/usr/bin/env python3
"""src.baltor.distillation.lineage — the LineageBundle every promoted artifact must be able to produce.

The lossless law's *promotability test*: a derived artifact is not promotable unless it can answer —
which raw/source backs me · which transform/version made me · what was omitted/held out · which
candidates competed · prior active version · how do I roll back. ``LineageBundle.build`` walks the
:class:`~src.baltor.distillation.lossless_store.LosslessStore` from one artifact id BACKWARD through its
``parent_ids`` to the raw + source layers, gathering every fact the test demands.

A bundle is a pure projection of the store (no clock, no RNG) so it is deterministic. It stays within ONE
tenant: a global_public artifact's lineage can structurally never reach a tenant_private entry (the store
forbids that edge at write time), and ``build`` itself never crosses a tenant boundary on read.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.baltor.distillation.lossless_store import (
    LAYER_RAW,
    LAYER_SOURCE,
    LosslessStore,
    LosslessStoreEntry,
    TenantBoundaryError,
)


@dataclass
class LineageBundle:
    """The full backward lineage of one artifact — everything the promotability test asks for.

    ``raw_ids`` / ``source_ids`` are the raw + source layers reached by the walk; ``transform_run_ids`` and
    ``receipt_ids`` collect the runs and receipts along the way; ``held_out_ids`` / ``rejected_ids`` are the
    siblings held out / rejected by the transforms in this lineage (kept, never deleted);
    ``prior_version_ids`` are the other versions of this artifact's key (older active versions);
    ``rollback_target_ids`` is where it can roll back to.
    """
    artifact_id: str
    tenant_id: str
    scope: str
    key: str
    reached_ids: list[str] = field(default_factory=list)        # every entry id touched by the walk
    raw_ids: list[str] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)
    parent_ids: list[str] = field(default_factory=list)         # direct parents of the artifact
    source_handles: list[str] = field(default_factory=list)
    transform_run_ids: list[str] = field(default_factory=list)
    receipt_ids: list[str] = field(default_factory=list)
    held_out_ids: list[str] = field(default_factory=list)
    rejected_ids: list[str] = field(default_factory=list)
    prior_version_ids: list[str] = field(default_factory=list)
    rollback_target_ids: list[str] = field(default_factory=list)

    def reaches_raw(self) -> bool:
        return bool(self.raw_ids)

    def reaches_source(self) -> bool:
        return bool(self.source_ids)

    def reaches(self, entry_id: str) -> bool:
        """True iff the backward walk from the artifact touched ``entry_id`` (e.g. a baseline, a loser)."""
        return entry_id in self.reached_ids

    def is_complete(self) -> bool:
        """A promoted artifact's bundle is complete iff it reaches raw AND source, carries ≥1 source handle,
        and names the transform_run that produced it (the non-negotiable promotability minimum)."""
        return (self.reaches_raw() and self.reaches_source()
                and bool(self.source_handles) and bool(self.transform_run_ids))

    def to_dict(self) -> dict:
        return {
            "artifact_id": self.artifact_id, "tenant_id": self.tenant_id, "scope": self.scope, "key": self.key,
            "reached_ids": list(self.reached_ids), "raw_ids": list(self.raw_ids),
            "source_ids": list(self.source_ids), "parent_ids": list(self.parent_ids),
            "source_handles": list(self.source_handles), "transform_run_ids": list(self.transform_run_ids),
            "receipt_ids": list(self.receipt_ids), "held_out_ids": list(self.held_out_ids),
            "rejected_ids": list(self.rejected_ids), "prior_version_ids": list(self.prior_version_ids),
            "rollback_target_ids": list(self.rollback_target_ids),
        }

    @staticmethod
    def build(store: LosslessStore, artifact_id: str, *, tenant: str | None = None) -> "LineageBundle":
        """Walk the store BACKWARD from ``artifact_id`` to raw/source, collecting the full lineage.

        ``tenant`` (if given) scopes every read; the walk never crosses a tenant boundary — encountering a
        parent of a different tenant raises ``TenantBoundaryError`` (which the store also forbids at write
        time for global_public → tenant_private edges).
        """
        root = store.get(artifact_id, tenant=tenant)
        scope_tenant = tenant if tenant is not None else root.tenant_id

        reached: list[str] = []
        raw_ids: list[str] = []
        source_ids: list[str] = []
        run_ids: list[str] = []
        receipt_ids: list[str] = []
        held_out: list[str] = []
        rejected: list[str] = []
        handles: list[str] = []

        seen: set[str] = set()
        stack: list[str] = [artifact_id]
        while stack:
            eid = stack.pop()
            if eid in seen:
                continue
            seen.add(eid)
            entry = store.get(eid, tenant=scope_tenant)
            if entry.tenant_id != scope_tenant:  # defensive — should never happen given the write-time law
                raise TenantBoundaryError(f"lineage of {artifact_id!r} reached foreign tenant {entry.tenant_id!r}")
            reached.append(eid)
            if entry.layer == LAYER_RAW:
                raw_ids.append(eid)
            elif entry.layer == LAYER_SOURCE:
                source_ids.append(eid)
            run_ids.extend(entry.transform_run_id and [entry.transform_run_id] or [])
            receipt_ids.extend(entry.receipt_ids)
            held_out.extend(entry.held_out_ids)
            rejected.extend(entry.rejected_ids)
            handles.extend(entry.source_handles)
            stack.extend(p for p in entry.parent_ids if p not in seen)

        # prior versions of THIS artifact's key (other active versions it could roll back across)
        versions = store.versions(root.key, tenant=scope_tenant)
        prior = [e.entry_id for e in versions if e.entry_id != artifact_id]

        def _dedup(xs):  # deterministic order-preserving de-dup
            out, s = [], set()
            for x in xs:
                if x not in s:
                    s.add(x); out.append(x)
            return out

        return LineageBundle(
            artifact_id=artifact_id, tenant_id=scope_tenant, scope=root.scope, key=root.key,
            reached_ids=_dedup(reached), raw_ids=_dedup(raw_ids), source_ids=_dedup(source_ids),
            parent_ids=list(root.parent_ids), source_handles=_dedup(handles),
            transform_run_ids=_dedup(run_ids), receipt_ids=_dedup(receipt_ids),
            held_out_ids=_dedup(held_out), rejected_ids=_dedup(rejected),
            prior_version_ids=prior, rollback_target_ids=list(root.rollback_target_ids))
