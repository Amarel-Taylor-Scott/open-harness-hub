#!/usr/bin/env python3
"""adapters/source/folder_batch — LocalFolderBatchAdapter (a mixed-extension folder of files as ONE source).

A folder of files (a drag-and-drop upload, an export dump) is a SOURCE. This adapter does NOT parse anything
itself — it CLASSIFIES each file by extension and ROUTES it to the correct EXISTING source adapter via
``scripts.ingest.source_adapters.normalize()`` (json/csv/html/pdf/unknown) or, for markdown, the sibling
``MarkdownFolderAdapter``. It then emits:

  * a **folder manifest** source artifact (``artifact_type=folder_manifest``) listing every file with its
    classified ``source_type``, per-file idempotency key, content hash, and consumable status;
  * the per-file governed artifacts produced by each routed adapter (carried through unchanged);
  * a **batch summary** (counts of consumable / non-consumable / error files).

PARTIAL failure is allowed and HONEST: a file whose parser is unavailable (e.g. ``.pdf``) or that the routed
adapter cannot consume becomes a **non-consumable entry in the manifest** — it does NOT abort the batch, and
no fake claim is produced. An unexpected per-file exception is captured as an ``error`` manifest entry, again
without aborting the batch.

Idempotency: the per-file key is ``tenant_id + relpath + content_hash``. Re-running the same folder yields
byte-identical manifest + artifacts (deterministic; content-addressed; time injected via ``now``; stdlib only).

Source handle: the manifest is ``ctx://tenant/<tid>/source/<sid>#folder.manifest``; per-file artifacts keep
the handles minted by their routed adapter (rooted at the per-file ``source_id`` ``<sid>/file/<relpath>``).
"""
from __future__ import annotations

import json
import os
from typing import Mapping

from scripts.ingest.source_adapters import _base_handle, _hash, normalize

from src.baltor.adapters.source.markdown_folder import MarkdownFolderAdapter

#: extension → source_type routing. Markdown is routed to the MarkdownFolderAdapter (single-note mode).
_EXT_TO_TYPE = {
    "json": "json", "csv": "csv", "md": "markdown", "markdown": "markdown",
    "html": "html", "htm": "html", "pdf": "pdf", "txt": "txt",
}
#: ``.txt`` has no structured parser here → honest non-consumable (raw stored). Keep it explicit, not faked.
_NO_PARSER_TYPES = {"txt", "unknown"}


def _classify(relpath: str) -> str:
    ext = relpath.rsplit(".", 1)[-1].lower() if "." in os.path.basename(relpath) else ""
    return _EXT_TO_TYPE.get(ext, "unknown")


def _content_hash(data) -> str:
    if isinstance(data, bytes):
        return _hash({"bytes": data.decode("utf-8", "ignore")})
    return _hash({"text": str(data)})


def _iter_files(payload) -> list[tuple[str, object]]:
    """Yield ``(relpath, data)`` sorted by relpath for determinism. dict → as-is; path → walked."""
    files: list[tuple[str, object]] = []
    if isinstance(payload, Mapping):
        for rp, data in payload.items():
            files.append((str(rp).replace("\\", "/"), data))
    else:
        root = str(payload)
        for dirpath, dirnames, filenames in os.walk(root):
            for fn in filenames:
                full = os.path.join(dirpath, fn)
                rp = os.path.relpath(full, root).replace("\\", "/")
                with open(full, "rb") as fh:
                    files.append((rp, fh.read()))
    files.sort(key=lambda t: t[0])
    return files


class LocalFolderBatchAdapter:
    """SourceAdapter for a mixed-extension local folder. Routes each file; never aborts on one bad file."""

    source_type = "folder"
    parser_provider = "folder_batch_router"

    def ingest(self, payload, *, tenant_id, source_id, scope="tenant_private", authority="unknown", now=0) -> dict:
        files = _iter_files(payload)
        manifest_entries: list[dict] = []
        all_artifacts: list[dict] = []
        n_consumable = n_nonconsumable = n_error = 0

        for relpath, data in files:
            stype = _classify(relpath)
            file_source_id = f"{source_id}/file/{relpath}"
            entry = {"relpath": relpath, "source_type": stype, "file_source_id": file_source_id}
            try:
                # content hash + per-file idempotency key are computed inside the try so even a pathological
                # file (e.g. bytes whose .decode raises) is captured as an error entry, never an abort.
                chash = _content_hash(data)
                idem_key = _hash({"tenant_id": tenant_id, "relpath": relpath, "content_hash": chash})
                entry["content_hash"] = chash
                entry["idempotency_key"] = idem_key
                if stype in _NO_PARSER_TYPES:
                    raw = data.decode("utf-8", "ignore") if isinstance(data, bytes) else str(data)
                    entry.update(consumable=False,
                                 reason=f"no_local_parser: {stype} has no structured parser in this batch "
                                        f"router; raw stored as a source artifact, no claim extracted")
                    # store a raw source_record so the bytes are ledgered (never a faked parse)
                    fbase = _base_handle(tenant_id, scope, file_source_id)
                    all_artifacts.append({"artifact_id": "source-" + _hash(raw),
                                          "artifact_type": "source_record", "source_handle": fbase,
                                          "content_hash": _hash(raw), "tenant_id": tenant_id, "scope": scope,
                                          "source_id": file_source_id, "source_type": stype,
                                          "is_source_root": True, "relpath": relpath})
                    n_nonconsumable += 1
                elif stype == "markdown":
                    res = MarkdownFolderAdapter().ingest({relpath: data}, tenant_id=tenant_id,
                                                         source_id=file_source_id, scope=scope,
                                                         authority=authority, now=now)
                    entry["consumable"] = bool(res.get("consumable"))
                    all_artifacts.extend(res.get("artifacts", []))
                    n_consumable += 1 if entry["consumable"] else 0
                    n_nonconsumable += 0 if entry["consumable"] else 1
                else:
                    res = normalize(stype, data, tenant_id=tenant_id, source_id=file_source_id,
                                    scope=scope, authority=authority)
                    entry["consumable"] = bool(res.get("consumable"))
                    if not entry["consumable"]:
                        entry["reason"] = res.get("reason", "non_consumable")
                        n_nonconsumable += 1
                    else:
                        n_consumable += 1
                    all_artifacts.extend(res.get("artifacts", []))
            except Exception as exc:  # one bad file does NOT abort the batch — record + continue
                # ensure a stable content hash + idempotency key even when hashing the data itself failed,
                # so the error entry is still content-addressed and idempotent across runs.
                entry.setdefault("content_hash", _hash({"relpath": relpath, "error": type(exc).__name__}))
                entry.setdefault("idempotency_key",
                                 _hash({"tenant_id": tenant_id, "relpath": relpath,
                                        "content_hash": entry["content_hash"], "error": type(exc).__name__}))
                entry.update(consumable=False, reason=f"error: {type(exc).__name__}: {exc}")
                n_error += 1
            manifest_entries.append(entry)

        base = _base_handle(tenant_id, scope, source_id)
        manifest_handle = f"{base}#folder.manifest"
        # batch content hash is derived from the per-file content hashes already captured in the manifest
        # entries (resilient to a file whose raw data cannot be hashed) — never re-hash raw data here.
        raw = {"files": [{"relpath": e["relpath"], "content_hash": e.get("content_hash", "")}
                         for e in manifest_entries]}
        manifest_hash = _hash({"entries": manifest_entries})
        manifest = {"artifact_id": "folder-" + manifest_hash, "artifact_type": "folder_manifest",
                    "source_handle": manifest_handle, "content_hash": manifest_hash, "parent_artifact_id": base,
                    "tenant_id": tenant_id, "scope": scope, "source_id": source_id, "source_type": self.source_type,
                    "parser_provider": self.parser_provider, "authority": authority, "is_source_root": True,
                    "file_count": len(files), "files": manifest_entries, "ingested_at": now,
                    "batch_content_hash": _hash(raw)}
        summary = {"file_count": len(files), "consumable": n_consumable,
                   "non_consumable": n_nonconsumable, "errors": n_error}
        # the batch is consumable as a SOURCE (the manifest exists) even when some files are not consumable.
        return {"consumable": True, "source_type": self.source_type, "parser_provider": self.parser_provider,
                "source_id": source_id, "tenant_id": tenant_id, "scope": scope, "authority": authority,
                "content_hash": manifest_hash, "source_artifacts": [manifest],
                "artifacts": [manifest] + all_artifacts, "manifest": manifest_entries, "summary": summary}


def _self_demo(now: int = 0) -> dict:
    """In-memory fixture demo (used by the proof / docs). Deterministic; time injected."""
    folder = {
        "facts.json": '{"id": "X1", "deadline_days": 10}',
        "rows.csv": "id,amount,note\n1,35,Unfair fee. No refund.\n",
        "readme.md": "---\ntitle: Readme\nstructured: true\n---\n# Readme\n\nThis is a note. It links to [[Other]].\n",
        "scan.pdf": b"%PDF-1.4 fake bytes (no real parser)",
    }
    return LocalFolderBatchAdapter().ingest(folder, tenant_id="acme", source_id="upload1", now=now)


if __name__ == "__main__":  # pragma: no cover - manual inspection only
    print(json.dumps(_self_demo(now=1_000_000)["summary"], indent=2, default=str))
