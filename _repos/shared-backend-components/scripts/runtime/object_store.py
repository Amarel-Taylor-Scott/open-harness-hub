#!/usr/bin/env python3
"""scripts.runtime.object_store — content-addressed object/blob storage (local now; S3/GCS/Azure later).

Large or raw payloads — original PDFs, OCR/Docling JSON, raw model responses, big context packs, trace
bundles — do NOT belong in the artifact JSON or on the dashboard. They go to the object store; the artifact
ledger keeps only a content-addressed ``payload_ref`` + ``content_hash`` + ``mime_type`` + ``size_bytes``.
Refs are content-addressed (``object://<tenant>/<sha>...``) so the same ref always maps to the same bytes,
and the interface is storage-agnostic (swap LocalObjectStore for an S3/GCS/Azure adapter unchanged).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class ObjectStore:
    def put(self, tenant_id: str, data: Any, *, mime_type: str = "application/json") -> dict:
        raise NotImplementedError

    def get(self, ref: str) -> bytes:
        raise NotImplementedError

    def exists(self, ref: str) -> bool:
        raise NotImplementedError


class LocalObjectStore(ObjectStore):
    backend = "local_object_store"        # named so a facade can report it instead of a literal

    def __init__(self, base_dir: str | Path) -> None:
        self.base = Path(base_dir)

    def _to_bytes(self, data: Any) -> bytes:
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            return data.encode("utf-8")
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def ref_for(self, tenant_id: str, data: Any) -> str:
        """The content-addressed ref this store WOULD produce for ``data`` — computed WITHOUT writing, so
        a caller can answer "is this object present?" from the object itself (id-addressable presence)."""
        return f"object://{tenant_id}/{_hash_bytes(self._to_bytes(data))}"

    def put(self, tenant_id: str, data: Any, *, mime_type: str = "application/json") -> dict:
        b = self._to_bytes(data)
        h = _hash_bytes(b)
        ref = f"object://{tenant_id}/{h}"
        path = self.base / tenant_id / f"{h}.blob"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b)  # content-addressed: same content → same path (idempotent)
        return {"payload_ref": ref, "content_hash": "sha256:" + h[:24], "mime_type": mime_type, "size_bytes": len(b)}

    def _path(self, ref: str) -> Path:
        assert ref.startswith("object://"), ref
        tenant, h = ref[len("object://"):].split("/", 1)
        return self.base / tenant / f"{h}.blob"

    def exists(self, ref: str) -> bool:
        return self._path(ref).exists()

    def get(self, ref: str) -> bytes:
        return self._path(ref).read_bytes()
