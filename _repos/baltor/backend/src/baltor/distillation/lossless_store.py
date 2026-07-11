#!/usr/bin/env python3
"""src.baltor.distillation.lossless_store — the append-only, content-addressed LOSSLESS store.

The lossless law (``_repos/shared-backend-components/docs/codex/lossless-distillation.md``) made operational: *distillation is never
replacement*. Every transform (ingest / decompose / reconcile / optimize / promote) writes a NEW layer —

    put_raw(...)      → raw input bytes (the unmodified source payload)
    put_source(...)   → a normalized source artifact (still a SOURCE layer; raw stays)
    put_derived(...)  → facts / packs / conclusions / reconciliations / candidates (parents preserved)

— and NOTHING already written is ever mutated or removed. The store is **append-only**: ``put_*`` returns
a content-addressed id (``dist:sha256:<hex>:<tenant>``) derived from the entry body, so the same body for
the same tenant is idempotent and re-writing it overwrites nothing observable.

Versions of a logical thing live under a stable ``key`` (e.g. ``"context_pack/cfpb-regE"``). ``versions(key)``
returns every version that key has ever had, oldest→newest. A **current pointer** per key names the active
version; ``set_current(key, id)`` moves that pointer only — the prior version stays fully readable
(``get(prior_id)`` still works). This is exactly what rollback needs: move the pointer back, delete nothing.

``rehydrate_payload(ref)`` returns the EXACT bytes a derived entry was built from, via the wrapped
content-addressed :class:`LocalContentAddressedObjectStore` (large raw payloads are kept out of the entry
body and referenced by an opaque ``objref:sha256:…`` payload_ref; see ``check_object_store_payload_ref``).

Tenant scoping is structural: an id embeds its tenant, every read checks it, and a ``tenant_private`` entry
can NEVER appear in a ``global_public`` entry's lineage (``put_derived`` raises ``TenantBoundaryError``).
Held-out and rejected entries are first-class layers — written, kept, and queryable — never deleted.

Determinism: ids are ``hashlib`` content hashes, ``created_at`` is an injected ``now`` param (never a clock
read), no RNG. Stdlib only; the backing object store is the existing in-memory content-addressed adapter.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Iterable

from src.baltor.adapters.object_store.local_object_store import LocalContentAddressedObjectStore

EPOCH = "1970-01-01T00:00:00Z"  # deterministic default stamp (no wall-clock in compared bytes)

#: id scheme — one definition, reused for build + parse so they can never drift.
_ID_SCHEME = "dist"
_ID_ALGO = "sha256"
_ID_PREFIX = f"{_ID_SCHEME}:{_ID_ALGO}:"  # "dist:sha256:"

#: the two scopes a layer can carry. tenant_private lineage must never enter a global_public layer.
TENANT_PRIVATE = "tenant_private"
GLOBAL_PUBLIC = "global_public"
_SCOPES = (TENANT_PRIVATE, GLOBAL_PUBLIC)

#: the three layers. raw + source are PRESERVED forever; derived is a NEW layer over its parents.
LAYER_RAW = "raw"
LAYER_SOURCE = "source"
LAYER_DERIVED = "derived"


class DistillationStoreError(Exception):
    """Base class for lossless-store failures."""


class TenantBoundaryError(DistillationStoreError):
    """A read or a lineage edge crossed a tenant boundary (or pulled tenant_private into global_public)."""


def _canon(body: Any) -> bytes:
    """Canonical JSON bytes for content hashing (sorted keys, compact, str-coerced)."""
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _hash(body: Any) -> str:
    return hashlib.sha256(_canon(body)).hexdigest()


def make_id(content_hash_hex: str, tenant_id: str) -> str:
    """Build the content-addressed entry id: ``dist:sha256:<hex>:<tenant>``."""
    return f"{_ID_PREFIX}{content_hash_hex}:{tenant_id}"


def parse_id(entry_id: str) -> tuple[str, str]:
    """Parse an entry id → ``(content_hash_hex, tenant_id)``. Raise on any malformation."""
    if not isinstance(entry_id, str) or not entry_id.startswith(_ID_PREFIX):
        raise DistillationStoreError(f"not a {_ID_PREFIX!r} id: {entry_id!r}")
    rest = entry_id[len(_ID_PREFIX):]
    parts = rest.split(":", 1)  # tenant ids may not contain ':'
    if len(parts) != 2:
        raise DistillationStoreError(f"id missing tenant segment: {entry_id!r}")
    content_hash_hex, tenant_id = parts
    if len(content_hash_hex) != 64 or any(c not in "0123456789abcdef" for c in content_hash_hex):
        raise DistillationStoreError(f"id hash is not a sha256 hex digest: {entry_id!r}")
    if not tenant_id:
        raise DistillationStoreError(f"id has empty tenant: {entry_id!r}")
    return content_hash_hex, tenant_id


@dataclass(frozen=True)
class LosslessStoreEntry:
    """One immutable layer in the lossless store. Append-only: once written it is never mutated.

    ``parent_ids`` reach the prior layers (raw←source←derived…). ``payload_ref`` (optional) points at a
    large raw payload in the object store; the exact bytes rehydrate via ``rehydrate_payload``.
    ``held_out_ids`` / ``rejected_ids`` are sibling layers held out of / rejected from THIS derived view but
    kept forever and queryable. ``role`` marks an entry's relation to its key (e.g. ``baseline`` /
    ``candidate`` / ``winner`` / ``loser`` / ``held_out`` / ``rejected``).
    """
    entry_id: str
    tenant_id: str
    scope: str                       # tenant_private | global_public
    layer: str                       # raw | source | derived
    key: str                         # stable logical key whose versions form a chain
    body: dict                       # the entry payload (NOT the large raw bytes — those go to payload_ref)
    content_hash: str                # sha256:<hex> of the canonical body
    parent_ids: tuple[str, ...] = ()        # reaches raw/source/parent layers
    source_handles: tuple[str, ...] = ()    # ctx://…#field handles backing this entry
    transform_run_id: str = ""              # the DistillationRun that produced this entry
    receipt_ids: tuple[str, ...] = ()       # verification/optimization/reconciliation/rollback receipts
    held_out_ids: tuple[str, ...] = ()      # siblings held out of THIS view (kept, never deleted)
    rejected_ids: tuple[str, ...] = ()      # candidates rejected for THIS view (kept, never deleted)
    rollback_target_ids: tuple[str, ...] = ()  # prior active version(s) this entry can roll back to
    payload_ref: str = ""                   # opaque objref:sha256:… for the large raw payload, if any
    transform_type: str = ""                # ingest | decompose | reconcile | optimize | promote | …
    role: str = ""                          # baseline | candidate | winner | loser | held_out | rejected | …
    created_at: str = EPOCH

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id, "tenant_id": self.tenant_id, "scope": self.scope,
            "layer": self.layer, "key": self.key, "body": dict(self.body),
            "content_hash": self.content_hash, "parent_ids": list(self.parent_ids),
            "source_handles": list(self.source_handles), "transform_run_id": self.transform_run_id,
            "receipt_ids": list(self.receipt_ids), "held_out_ids": list(self.held_out_ids),
            "rejected_ids": list(self.rejected_ids), "rollback_target_ids": list(self.rollback_target_ids),
            "payload_ref": self.payload_ref, "transform_type": self.transform_type, "role": self.role,
            "created_at": self.created_at,
        }


def _as_tuple(x: Iterable[str] | None) -> tuple[str, ...]:
    return tuple(x) if x else ()


class LosslessStore:
    """Append-only, content-addressed, tenant-scoped store of raw/source/derived layers + current pointers.

    The lossless guarantees, structurally:

    * **append-only** — ``put_*`` never mutates or removes an existing entry; an idempotent re-put of the
      same body returns the same id and overwrites nothing observable.
    * **versions kept** — ``versions(key)`` returns every version a key ever had; a new version never
      deletes the old one.
    * **pointer moves, nothing dies** — ``set_current(key, id)`` re-points the active version only; the
      prior version stays readable via ``get``.
    * **exact rehydration** — ``rehydrate_payload(ref)`` returns the exact stored bytes (verified).
    * **tenant isolation** — every read is tenant-checked; ``tenant_private`` lineage can never enter a
      ``global_public`` entry (``put_derived`` rejects it).
    """

    def __init__(self, object_store: LocalContentAddressedObjectStore | None = None) -> None:
        # entry_id -> LosslessStoreEntry (the immutable, append-only layer table)
        self._entries: dict[str, LosslessStoreEntry] = {}
        # (tenant_id, key) -> [entry_id, ...] in append order (oldest first); never shrinks
        self._versions: dict[tuple[str, str], list[str]] = {}
        # (tenant_id, key) -> current/active entry_id (a POINTER; moving it deletes nothing)
        self._current: dict[tuple[str, str], str] = {}
        # large raw payloads live here, referenced by an opaque payload_ref (kept out of the entry body)
        self._objects = object_store or LocalContentAddressedObjectStore()

    # ── internal write path (the ONLY place an entry is created) ──────────────────────────────────
    def _put(self, *, tenant_id: str, scope: str, layer: str, key: str, body: dict,
             parent_ids: Iterable[str] | None = None, source_handles: Iterable[str] | None = None,
             transform_run_id: str = "", receipt_ids: Iterable[str] | None = None,
             held_out_ids: Iterable[str] | None = None, rejected_ids: Iterable[str] | None = None,
             rollback_target_ids: Iterable[str] | None = None, payload_ref: str = "",
             transform_type: str = "", role: str = "", now: str = EPOCH) -> LosslessStoreEntry:
        if not tenant_id:
            raise DistillationStoreError("tenant_id is required")
        if scope not in _SCOPES:
            raise DistillationStoreError(f"scope must be one of {_SCOPES}, got {scope!r}")
        # content id is derived from the IDENTITY-bearing fields only (layer/key/body/tenant/scope/parents),
        # NOT from created_at — so the same logical layer is byte-stable and idempotent across runs.
        identity = {"tenant": tenant_id, "scope": scope, "layer": layer, "key": key,
                    "body": body, "parents": sorted(_as_tuple(parent_ids)),
                    "payload_ref": payload_ref, "transform_type": transform_type, "role": role}
        h = _hash(identity)
        entry_id = make_id(h, tenant_id)

        # lossless: an existing entry is NEVER overwritten. Idempotent re-put returns the existing entry.
        existing = self._entries.get(entry_id)
        if existing is not None:
            self._track_version(tenant_id, key, entry_id)
            return existing

        # tenant-boundary law: a global_public entry may not have any tenant_private parent in its lineage.
        if scope == GLOBAL_PUBLIC:
            for pid in _as_tuple(parent_ids):
                parent = self._entries.get(pid)
                if parent is not None and parent.scope == TENANT_PRIVATE:
                    raise TenantBoundaryError(
                        f"tenant_private parent {pid!r} cannot enter a global_public lineage for key {key!r}")

        entry = LosslessStoreEntry(
            entry_id=entry_id, tenant_id=tenant_id, scope=scope, layer=layer, key=key,
            body=dict(body), content_hash=f"{_ID_ALGO}:{h}", parent_ids=_as_tuple(parent_ids),
            source_handles=_as_tuple(source_handles), transform_run_id=transform_run_id,
            receipt_ids=_as_tuple(receipt_ids), held_out_ids=_as_tuple(held_out_ids),
            rejected_ids=_as_tuple(rejected_ids), rollback_target_ids=_as_tuple(rollback_target_ids),
            payload_ref=payload_ref, transform_type=transform_type, role=role, created_at=now)
        self._entries[entry_id] = entry
        self._track_version(tenant_id, key, entry_id)
        return entry

    def _track_version(self, tenant_id: str, key: str, entry_id: str) -> None:
        chain = self._versions.setdefault((tenant_id, key), [])
        if entry_id not in chain:
            chain.append(entry_id)
        # the FIRST version of a key becomes the current pointer by default (pointer never auto-moves later).
        self._current.setdefault((tenant_id, key), entry_id)

    # ── public write surface ──────────────────────────────────────────────────────────────────────
    def put_raw(self, tenant_id: str, *, key: str, raw_bytes: bytes | str, mime_type: str = "application/octet-stream",
                scope: str = TENANT_PRIVATE, transform_run_id: str = "", receipt_ids: Iterable[str] | None = None,
                meta: dict | None = None, now: str = EPOCH) -> LosslessStoreEntry:
        """Write the RAW input layer. The large bytes go to the object store; the entry keeps only an opaque
        ``payload_ref`` + hash + size (no inlined blob). Raw is preserved forever — no transform deletes it."""
        ledger = self._objects.put(tenant_id, raw_bytes, mime_type=mime_type)
        body = {"raw_content_hash": ledger["content_hash"], "size_bytes": ledger["size_bytes"],
                "mime_type": ledger["mime_type"], **(meta or {})}
        return self._put(tenant_id=tenant_id, scope=scope, layer=LAYER_RAW, key=key, body=body,
                         transform_run_id=transform_run_id, receipt_ids=receipt_ids,
                         payload_ref=ledger["payload_ref"], transform_type="ingest", role=LAYER_RAW, now=now)

    def put_source(self, tenant_id: str, *, key: str, body: dict, parent_ids: Iterable[str] | None = None,
                   source_handles: Iterable[str] | None = None, scope: str = TENANT_PRIVATE,
                   transform_run_id: str = "", receipt_ids: Iterable[str] | None = None,
                   payload_ref: str = "", now: str = EPOCH) -> LosslessStoreEntry:
        """Write a normalized SOURCE artifact (a new layer over raw). Raw stays; this never overwrites it."""
        return self._put(tenant_id=tenant_id, scope=scope, layer=LAYER_SOURCE, key=key, body=body,
                         parent_ids=parent_ids, source_handles=source_handles, transform_run_id=transform_run_id,
                         receipt_ids=receipt_ids, payload_ref=payload_ref, transform_type="normalize",
                         role=LAYER_SOURCE, now=now)

    def put_derived(self, tenant_id: str, *, key: str, body: dict, parent_ids: Iterable[str] | None = None,
                    source_handles: Iterable[str] | None = None, scope: str = TENANT_PRIVATE,
                    transform_type: str = "derive", transform_run_id: str = "",
                    receipt_ids: Iterable[str] | None = None, held_out_ids: Iterable[str] | None = None,
                    rejected_ids: Iterable[str] | None = None, rollback_target_ids: Iterable[str] | None = None,
                    role: str = LAYER_DERIVED, payload_ref: str = "", now: str = EPOCH) -> LosslessStoreEntry:
        """Write a DERIVED artifact (fact / pack / conclusion / reconciliation / candidate …) as a NEW layer.

        Parents (raw/source/prior derived) are preserved; held-out and rejected siblings are recorded by id
        and kept queryable, never deleted. Raises ``TenantBoundaryError`` if a global_public entry would pull
        a tenant_private parent into its lineage.
        """
        return self._put(tenant_id=tenant_id, scope=scope, layer=LAYER_DERIVED, key=key, body=body,
                         parent_ids=parent_ids, source_handles=source_handles, transform_type=transform_type,
                         transform_run_id=transform_run_id, receipt_ids=receipt_ids, held_out_ids=held_out_ids,
                         rejected_ids=rejected_ids, rollback_target_ids=rollback_target_ids, role=role,
                         payload_ref=payload_ref, now=now)

    # ── reads (tenant-scoped projections; the store is the truth) ─────────────────────────────────
    def get(self, entry_id: str, *, tenant: str | None = None) -> LosslessStoreEntry:
        """Return the (immutable) entry by id. If ``tenant`` is given it MUST match the entry's tenant —
        a cross-tenant read raises ``TenantBoundaryError`` (the id embeds the tenant, so this is structural)."""
        _, id_tenant = parse_id(entry_id)
        entry = self._entries.get(entry_id)
        if entry is None:
            raise DistillationStoreError(f"no entry for id {entry_id!r}")
        if tenant is not None and tenant != entry.tenant_id:
            raise TenantBoundaryError(
                f"cross-tenant read: caller tenant {tenant!r} != entry tenant {entry.tenant_id!r}")
        return entry

    def has(self, entry_id: str) -> bool:
        return entry_id in self._entries

    def versions(self, key: str, *, tenant: str) -> list[LosslessStoreEntry]:
        """Every version a key has ever had, oldest→newest. A new version NEVER removes an older one, so a
        prior version is always retrievable here (and via ``get``)."""
        chain = self._versions.get((tenant, key), [])
        return [self._entries[eid] for eid in chain]

    def current_id(self, key: str, *, tenant: str) -> str | None:
        """The id the active pointer names for ``key`` (or None if the key has no versions)."""
        return self._current.get((tenant, key))

    def current(self, key: str, *, tenant: str) -> LosslessStoreEntry | None:
        cid = self.current_id(key, tenant=tenant)
        return self._entries[cid] if cid else None

    def set_current(self, key: str, entry_id: str, *, tenant: str) -> str | None:
        """Move the active pointer for ``key`` to ``entry_id``. Returns the PRIOR pointer id (which is NOT
        deleted — it stays fully readable). Lossless: this re-points only; no version is ever removed."""
        if (tenant, key) not in self._versions or entry_id not in self._versions[(tenant, key)]:
            raise DistillationStoreError(f"entry {entry_id!r} is not a version of key {key!r} for tenant {tenant!r}")
        entry = self._entries[entry_id]
        if entry.tenant_id != tenant:
            raise TenantBoundaryError(f"cannot point tenant {tenant!r} key at entry of tenant {entry.tenant_id!r}")
        prior = self._current.get((tenant, key))
        self._current[(tenant, key)] = entry_id
        return prior

    def query(self, *, tenant: str, layer: str | None = None, role: str | None = None,
              key: str | None = None) -> list[LosslessStoreEntry]:
        """All entries for a tenant, optionally filtered by layer/role/key. Held-out and rejected entries are
        first-class and remain queryable here (they are never deleted)."""
        out = [e for e in self._entries.values() if e.tenant_id == tenant]
        if layer is not None:
            out = [e for e in out if e.layer == layer]
        if role is not None:
            out = [e for e in out if e.role == role]
        if key is not None:
            out = [e for e in out if e.key == key]
        return sorted(out, key=lambda e: e.entry_id)

    def rehydrate_payload(self, ref: str, *, tenant: str | None = None) -> bytes:
        """Return the EXACT stored bytes for an opaque ``payload_ref`` (content-hash verified on the way out).

        If ``tenant`` is given it must match the ref's tenant — the underlying object store rejects a
        cross-tenant ref, so a tenant cannot rehydrate another tenant's raw bytes."""
        if tenant is not None and self._objects.tenant_of(ref) != tenant:
            raise TenantBoundaryError(f"cross-tenant rehydrate: caller {tenant!r} != ref tenant {self._objects.tenant_of(ref)!r}")
        return self._objects.get(ref)
