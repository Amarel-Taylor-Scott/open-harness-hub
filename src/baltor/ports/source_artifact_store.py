"""src.baltor.ports.source_artifact_store — the SourceArtifactStorePort capability interface.

The append-only ledger of governed SourceArtifacts. Every connector writes here and NOWHERE else; no connector
bypasses this store, and reads/queries are always tenant-scoped so tenant_private artifacts are invisible to
global_public callers. Writes are idempotent on (tenant_id, source_id, content_hash) so a re-ingest of identical
content adds nothing. This is the ingestion boundary's persistence seam — it does NOT serve final facts (that is
the downstream consumption service); it only stores raw governed source artifacts + their provenance.

Stdlib only. No implementation that lets a write skip the artifact shape or cross tenant scope.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SourceArtifactStorePort(Protocol):
    """Append-only, tenant-scoped, idempotent store of SourceArtifact.v1 records."""

    def write_source_artifacts(self, artifacts: list[dict[str, Any]], *, tenant_id: str,
                               run_id: str, now: str) -> dict[str, Any]:
        """Append governed SourceArtifacts for one run. Idempotent on (tenant_id, source_id, content_hash):
        identical content is skipped, not duplicated. Rejects any artifact missing the required governance
        fields or whose tenant_id != the call's tenant_id (no cross-tenant write). Returns an
        IngestionReceipt.v1-shaped dict {written, duplicate, receipt_id, source_artifact_ids}. `now` injected."""
        ...

    def read_source_artifact(self, artifact_id: str, *, tenant_id: str) -> dict[str, Any] | None:
        """Read one SourceArtifact by id, scoped to `tenant_id`. Returns None if not found OR if it belongs to a
        different tenant's private scope (never leaks across tenants)."""
        ...

    def query_source_artifacts(self, *, tenant_id: str, source_id: str | None = None,
                               scope: str | None = None, since_cursor: dict[str, Any] | None = None
                               ) -> list[dict[str, Any]]:
        """List SourceArtifacts visible to `tenant_id` (its own tenant_private/tenant_shared + global_public),
        optionally filtered by source_id/scope/cursor window. Never returns another tenant's private artifacts."""
        ...

    def diff_source_artifacts(self, *, tenant_id: str, source_id: str, from_cursor: dict[str, Any],
                              to_cursor: dict[str, Any]) -> dict[str, Any]:
        """Return the added/changed/unchanged content hashes between two cursors for a source (for CDC + dedupe
        sizing). Pure read; tenant-scoped. Returns {'added': [...], 'changed': [...], 'unchanged': [...]}."""
        ...
