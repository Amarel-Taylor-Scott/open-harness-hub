"""adapters/memory/baltor_local — memory.baltor_local@v1: the working LOCAL memory provider.

A content-addressed, tenant/project-scoped, in-process memory store. It is the ACTIVE fallback for the
memory_provider slot: no network, no credentials, no third-party SDK — it always works offline. Every
write/search/profile output is a governed ``MemoryArtifact`` with ``claim_status="candidate"`` + a populated
``external_source_handle`` + ``lineage`` — never a served/canonical fact (remembered != verified).

Tenant isolation is enforced at the store boundary: artifacts are keyed by (tenant_id, project) and a search
in tenant A can never return tenant B's artifacts. LOSSLESS: a re-write of identical content is idempotent on
the content hash (no duplicate, nothing overwritten); raw content + lineage are always preserved.

Deterministic + offline + stdlib only: content-addressed ids, injected ``now``, no RNG, no wall-clock.
"""
from __future__ import annotations

from typing import Any

from src.baltor.adapters.memory import make_memory_artifact, memory_content_hash
from src.baltor.ports.memory_provider import CANDIDATE_CLAIM_STATUS

#: stable provider identity (matches the capability catalog adapter_id).
PROVIDER_ID = "memory.baltor_local@v1"

#: status reported by status() — the local provider is always available offline.
_STATUS_AVAILABLE = "available"


class BaltorLocalMemoryProvider:
    """Working local memory/recall/profile provider. Satisfies MemoryProviderPort + MemoryProfileProviderPort.

    State is held in a per-(tenant, project) dict of artifacts keyed by content hash. The store is the only
    place artifacts live; there is no cross-tenant index, so tenant isolation is structural, not a filter.
    """

    provider_id = PROVIDER_ID

    def __init__(self) -> None:
        # {(tenant_id, project): {content_hash: artifact}} — keyed by scope so a search is scope-local.
        self._store: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}

    # ── write ──────────────────────────────────────────────────────────────────────────────────────────
    def write(self, request: dict[str, Any]) -> dict[str, Any]:
        tenant_id = request["tenant_id"]
        project = request["project"]
        now = int(request["now"])
        artifact = make_memory_artifact(
            provider_id=self.provider_id,
            tenant_id=tenant_id,
            project=project,
            content=request["content"],
            now=now,
            container_tags=request.get("container_tags"),
            metadata=request.get("metadata"),
        )
        bucket = self._store.setdefault((tenant_id, project), {})
        ch = artifact["content_hash"]
        # idempotent on content hash: identical content is NOT duplicated, NOT overwritten (lossless).
        bucket.setdefault(ch, artifact)
        return bucket[ch]

    # ── search ─────────────────────────────────────────────────────────────────────────────────────────
    def search(self, request: dict[str, Any]) -> dict[str, Any]:
        tenant_id = request["tenant_id"]
        project = request["project"]
        query = str(request.get("query", ""))
        limit = int(request.get("limit", 10))
        bucket = self._store.get((tenant_id, project), {})  # scope-local read — no cross-tenant access path
        terms = [t for t in query.lower().split() if t]
        scored: list[tuple[int, str, dict[str, Any]]] = []
        for ch, art in bucket.items():
            hay = str(art.get("content", "")).lower()
            score = sum(hay.count(t) for t in terms) if terms else 1
            if score > 0:
                scored.append((score, ch, art))
        # deterministic order: score desc, then content_hash asc (no RNG, stable across runs).
        scored.sort(key=lambda x: (-x[0], x[1]))
        results = [art for _, _, art in scored[:limit]]
        return {
            "provider_id": self.provider_id,
            "tenant_id": tenant_id,
            "project": project,
            "query": query,
            "search_mode": request.get("search_mode", "hybrid"),
            "results": results,
        }

    # ── profile ────────────────────────────────────────────────────────────────────────────────────────
    def profile(self, scope: dict[str, Any]) -> dict[str, Any]:
        tenant_id = scope["tenant_id"]
        project = scope["project"]
        now = int(scope["now"])
        limit = int(scope.get("limit", 10))
        bucket = self._store.get((tenant_id, project), {})
        arts = list(bucket.values())
        # dynamic = most recently remembered (by injected remembered_at, then content_hash for determinism).
        by_recency = sorted(arts, key=lambda a: (-int(a["lineage"]["remembered_at"]), a["content_hash"]))
        # static = stable long-lived candidates (deterministic by content_hash).
        by_stable = sorted(arts, key=lambda a: a["content_hash"])
        return {
            "provider_id": self.provider_id,
            "tenant_id": tenant_id,
            "project": project,
            "static": by_stable[:limit],     # candidate long-term memories (NOT promoted facts)
            "dynamic": by_recency[:limit],   # candidate recent context (NOT served facts)
            "generated_at": now,
        }

    # ── status ─────────────────────────────────────────────────────────────────────────────────────────
    def status(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "status": _STATUS_AVAILABLE,
            "has_credentials": True,   # no external creds needed — always available offline
            "credential_ref": None,
            "detail": "in-process content-addressed local memory store (no network, no SDK)",
        }


def _self_demo(now: int = 1_000_000) -> dict[str, Any]:
    """Deterministic in-memory demo used by the proof. Time injected; offline; no RNG."""
    p = BaltorLocalMemoryProvider()
    a = p.write({"tenant_id": "acme", "project": "default", "content": "The Reg E dispute window is 10 days.",
                 "now": now})
    p.write({"tenant_id": "acme", "project": "default", "content": "Vendor invoice 4471 is under review.",
             "now": now + 1})
    found = p.search({"tenant_id": "acme", "project": "default", "query": "Reg E dispute"})
    prof = p.profile({"tenant_id": "acme", "project": "default", "now": now + 2})
    return {"write": a, "search": found, "profile": prof,
            "round_trip_ok": bool(found["results"]) and found["results"][0]["content_hash"] == a["content_hash"],
            "candidate_only": all(r["claim_status"] == CANDIDATE_CLAIM_STATUS for r in found["results"])}


if __name__ == "__main__":  # pragma: no cover - manual inspection only
    import json
    print(json.dumps(_self_demo(), indent=2, default=str)[:1400])
