#!/usr/bin/env python3
"""src.baltor.adapters.object_store.local_object_store — content-addressed in-memory object store adapter.

Large or raw payloads — original PDFs, OCR/Docling JSON, raw model responses, big context packs, trace
bundles — must NOT be inlined into the artifact JSON or shown on the dashboard. They are stored here and the
artifact ledger keeps only a content-addressed ``payload_ref`` (+ content hash, mime type, size). A
``payload_ref`` is an OPAQUE string ``objref:sha256:<hex>:<tenant>``: it carries no payload bytes, so an
artifact that references one leaks nothing about the blob beyond its sha256 identity.

This adapter structurally satisfies ``scripts.runtime.ports.ObjectStorePort`` (``put(tenant_id, data,
*, mime_type) -> dict`` and ``get(ref) -> bytes``) and adds the guarantees the artifact graph needs:

* **Content addressing** — the ref is derived from ``sha256(bytes)`` + tenant, so the same blob always
  yields the same ref (idempotent, deterministic; no clock, no RNG).
* **Read-time verification** — ``get`` re-hashes the stored bytes and raises ``CorruptObjectError`` if they
  no longer match the ref's hash, and ``ForgedRefError`` if the ref is malformed/unknown. A forged ref
  (right shape, wrong hash) cannot smuggle bytes out.
* **Tenant scoping** — every blob is filed under its tenant; a ref's tenant must match the blob's tenant.
  A cross-tenant ``get`` (a ref whose tenant differs from where the bytes were stored) is rejected.

Backend is an in-memory dict — deterministic and fully offline — but the interface is storage-agnostic so an
S3/GCS/Azure adapter can replace it without touching callers. Stdlib only.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

#: ref scheme prefix — one definition, reused for build + parse so the two can never drift.
_REF_SCHEME = "objref"
_REF_ALGO = "sha256"
_REF_PREFIX = f"{_REF_SCHEME}:{_REF_ALGO}:"  # "objref:sha256:"
DEFAULT_MIME_TYPE = "application/json"


class ObjectStoreError(Exception):
    """Base class for object-store failures."""


class ForgedRefError(ObjectStoreError):
    """The payload_ref is malformed, unknown, or points at a tenant that does not hold the blob."""


class CorruptObjectError(ObjectStoreError):
    """The stored bytes no longer hash to the value embedded in the ref (tamper / bit-rot)."""


def _hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def make_ref(content_hash_hex: str, tenant_id: str) -> str:
    """Build the opaque content-addressed ref. ``objref:sha256:<hex>:<tenant>``."""
    return f"{_REF_PREFIX}{content_hash_hex}:{tenant_id}"


def parse_ref(ref: str) -> tuple[str, str]:
    """Parse an opaque ref → ``(content_hash_hex, tenant_id)``. Raise ForgedRefError on any malformation."""
    if not isinstance(ref, str) or not ref.startswith(_REF_PREFIX):
        raise ForgedRefError(f"ref is not a {_REF_PREFIX!r} ref: {ref!r}")
    rest = ref[len(_REF_PREFIX):]
    # rest == "<hex>:<tenant>"; tenant ids may not contain ':' so split once from the left.
    parts = rest.split(":", 1)
    if len(parts) != 2:
        raise ForgedRefError(f"ref missing tenant segment: {ref!r}")
    content_hash_hex, tenant_id = parts[0], parts[1]
    if len(content_hash_hex) != 64 or any(c not in "0123456789abcdef" for c in content_hash_hex):
        raise ForgedRefError(f"ref hash is not a sha256 hex digest: {ref!r}")
    if not tenant_id:
        raise ForgedRefError(f"ref has empty tenant: {ref!r}")
    return content_hash_hex, tenant_id


@dataclass(frozen=True)
class _StoredObject:
    """The bytes plus the tenant + mime metadata kept alongside them (never inlined into artifacts)."""
    data: bytes
    tenant_id: str
    mime_type: str

    @property
    def size_bytes(self) -> int:
        return len(self.data)


class LocalContentAddressedObjectStore:
    """In-memory, content-addressed object store. Satisfies ObjectStorePort and verifies on read.

    Keyed by ``(tenant_id, content_hash)`` so the same bytes under two tenants are two distinct, isolated
    objects — a ref for tenant A can never resolve bytes written for tenant B.
    """

    def __init__(self) -> None:
        # (tenant_id, content_hash_hex) -> _StoredObject
        self._store: dict[tuple[str, str], _StoredObject] = {}

    # ---- coercion (mirrors the legacy LocalObjectStore so callers can swap freely) ----------------
    @staticmethod
    def _to_bytes(data: Any) -> bytes:
        if isinstance(data, bytes):
            return data
        if isinstance(data, bytearray):
            return bytes(data)
        if isinstance(data, str):
            return data.encode("utf-8")
        import json  # local import: only needed for the non-bytes convenience path

        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")

    # ---- ObjectStorePort surface ------------------------------------------------------------------
    def put(self, tenant_id: str, data: Any, *, mime_type: str = DEFAULT_MIME_TYPE) -> dict:
        """Store ``data`` for ``tenant_id`` and return the artifact-ledger reference dict.

        Returns ``{payload_ref, content_hash, mime_type, size_bytes}``. Content-addressed and idempotent:
        the same bytes for the same tenant return the same ref and overwrite nothing observable.
        The returned dict contains a ref and a hash — never the blob bytes (no leak).
        """
        if not tenant_id:
            raise ObjectStoreError("tenant_id is required to store an object")
        b = self._to_bytes(data)
        h = _hash_bytes(b)
        key = (tenant_id, h)
        stored = self._store.get(key)
        if stored is None:
            self._store[key] = _StoredObject(data=b, tenant_id=tenant_id, mime_type=mime_type)
        # idempotent re-put with the same bytes is a no-op; identical bytes → identical ref.
        ref = make_ref(h, tenant_id)
        return {
            "payload_ref": ref,
            "content_hash": f"{_REF_ALGO}:{h}",
            "mime_type": (stored.mime_type if stored is not None else mime_type),
            "size_bytes": len(b),
        }

    def get(self, ref: str) -> bytes:
        """Resolve ``ref`` to the exact stored bytes, verifying the content hash on the way out.

        Raises ForgedRefError if the ref is malformed/unknown or scoped to a tenant that does not hold the
        blob (cross-tenant access), and CorruptObjectError if the stored bytes no longer match the ref hash.
        """
        content_hash_hex, tenant_id = parse_ref(ref)
        stored = self._store.get((tenant_id, content_hash_hex))
        if stored is None:
            # unknown to this tenant — either never stored, or a cross-tenant ref. Reject either way.
            raise ForgedRefError(f"no object for ref {ref!r} under tenant {tenant_id!r}")
        actual = _hash_bytes(stored.data)
        if actual != content_hash_hex:
            raise CorruptObjectError(
                f"content-hash mismatch for {ref!r}: stored bytes hash to {_REF_ALGO}:{actual}"
            )
        return stored.data

    def exists(self, ref: str) -> bool:
        """True iff ``ref`` is well-formed AND resolves to a stored, tenant-scoped object. A forged/malformed
        ref returns False rather than raising (a cheap pre-check)."""
        try:
            content_hash_hex, tenant_id = parse_ref(ref)
        except ForgedRefError:
            return False
        return (tenant_id, content_hash_hex) in self._store

    # ---- tenant metadata (kept with the blob, not inlined into the artifact) ----------------------
    def head(self, ref: str) -> dict:
        """Return the metadata for a ref WITHOUT the bytes: ``{payload_ref, tenant_id, mime_type,
        content_hash, size_bytes}``. Verifies the ref and tenant scope but never emits the blob."""
        content_hash_hex, tenant_id = parse_ref(ref)
        stored = self._store.get((tenant_id, content_hash_hex))
        if stored is None:
            raise ForgedRefError(f"no object for ref {ref!r} under tenant {tenant_id!r}")
        return {
            "payload_ref": ref,
            "tenant_id": stored.tenant_id,
            "mime_type": stored.mime_type,
            "content_hash": f"{_REF_ALGO}:{content_hash_hex}",
            "size_bytes": stored.size_bytes,
        }

    def tenant_of(self, ref: str) -> str:
        """The tenant a ref is scoped to (parsed from the opaque ref; raises on a forged ref)."""
        _, tenant_id = parse_ref(ref)
        return tenant_id
