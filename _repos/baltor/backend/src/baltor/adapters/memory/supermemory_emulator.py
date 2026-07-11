"""adapters/memory/supermemory_emulator — memory.supermemory_emulator@v1: the DETERMINISTIC offline emulator.

This is the WORKING offline contract implementation of the Supermemory shape. It mimics supermemory's
add/search/profile (profile.static/profile.dynamic) RESPONSE shapes so callers can develop and prove the
governed-memory contract with NO credentials and NO network — the candidate api/mcp stubs are unavailable
without creds, so the emulator (or baltor_local) is what the correctness invariant actually runs on.

It NEVER imports the supermemory SDK and NEVER makes a network call. It is the supermemory_api/mcp stand-in:
status() reports ``emulated`` (available). Every write/search/profile output is a governed ``MemoryArtifact``
with ``claim_status="candidate"`` + external_source_handle + lineage — a remembered/recalled/profiled item is
NEVER a served/canonical fact. (Supermemory is never the source of truth; this emulates its recall, not its
authority — Baltor's gates decide truth downstream.)

The emulator deliberately re-uses the SAME governed MemoryArtifact builder as the local provider, but stamps
an upstream id in the supermemory-ish ``sm_<hash>`` form so the external_source_handle records a realistic
upstream provenance. It additionally returns a thin ``raw_response`` mirror of supermemory's add/search JSON
shape (id/memory/score/metadata) for shape-compat, WITHOUT ever treating that mirror as truth.

Deterministic + offline + stdlib only: content-addressed ids, injected ``now``, no RNG, no wall-clock, no SDK.
"""
from __future__ import annotations

from typing import Any

from src.baltor.adapters.memory import make_memory_artifact, memory_content_hash
from src.baltor.ports.memory_provider import CANDIDATE_CLAIM_STATUS

#: stable provider identity (matches the capability catalog adapter_id).
PROVIDER_ID = "memory.supermemory_emulator@v1"

#: status reported by status() — the emulator is the working offline impl, no creds required.
_STATUS_EMULATED = "emulated"

#: the env:// credential ref the REAL supermemory_api/mcp would need (named, never a value). The emulator
#: declares it so a caller can see what going-live would require — but the emulator itself needs none.
EMULATES_CREDENTIAL_REF = "env://SUPERMEMORY_API_KEY"


def _upstream_id(*, tenant_id: str, project: str, content: Any) -> str:
    """Deterministic supermemory-ish upstream id: ``sm_<contenthash>``. Content-addressed, no RNG."""
    return "sm_" + memory_content_hash({"t": tenant_id, "p": project, "c": content})


class SupermemoryEmulatorProvider:
    """Deterministic offline emulator. Satisfies MemoryProviderPort + MemoryProfileProviderPort with NO creds.

    Mimics supermemory add/search/profile shapes; the canonical output is always a governed candidate
    MemoryArtifact. Tenant/project isolation is structural (per-scope store), identical to the local provider.
    """

    provider_id = PROVIDER_ID

    def __init__(self) -> None:
        # {(tenant_id, project): {content_hash: artifact}} — scope-local, no cross-tenant index.
        self._store: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}

    # ── add / write ────────────────────────────────────────────────────────────────────────────────────
    def write(self, request: dict[str, Any]) -> dict[str, Any]:
        tenant_id = request["tenant_id"]
        project = request["project"]
        now = int(request["now"])
        content = request["content"]
        uid = _upstream_id(tenant_id=tenant_id, project=project, content=content)
        artifact = make_memory_artifact(
            provider_id=self.provider_id,
            tenant_id=tenant_id,
            project=project,
            content=content,
            now=now,
            upstream_id=uid,                       # supermemory-ish upstream provenance, preserved in lineage
            container_tags=request.get("container_tags"),
            metadata=request.get("metadata"),
            lineage_extra={"emulated": True, "emulates_credential_ref": EMULATES_CREDENTIAL_REF},
        )
        # shape-compat mirror of supermemory's add response (NOT treated as truth — informational only).
        artifact["raw_response"] = {"id": uid, "memory": str(content), "status": "queued",
                                    "containerTags": list(request.get("container_tags") or [])}
        bucket = self._store.setdefault((tenant_id, project), {})
        ch = artifact["content_hash"]
        bucket.setdefault(ch, artifact)  # idempotent on content; nothing overwritten (lossless)
        return bucket[ch]

    # ── search ─────────────────────────────────────────────────────────────────────────────────────────
    def search(self, request: dict[str, Any]) -> dict[str, Any]:
        tenant_id = request["tenant_id"]
        project = request["project"]
        query = str(request.get("query", ""))
        limit = int(request.get("limit", 10))
        mode = request.get("search_mode", "hybrid")  # mirrors supermemory searchMode hybrid|memories|documents
        bucket = self._store.get((tenant_id, project), {})  # scope-local — no cross-tenant access path
        terms = [t for t in query.lower().split() if t]
        scored: list[tuple[float, str, dict[str, Any]]] = []
        for ch, art in bucket.items():
            hay = str(art.get("content", "")).lower()
            hits = sum(hay.count(t) for t in terms) if terms else 1
            if hits <= 0:
                continue
            # deterministic pseudo-relevance score in [0,1] (mimics supermemory's score field; not RNG).
            denom = (len(terms) or 1) + 1
            score = round(min(1.0, hits / denom), 4)
            scored.append((score, ch, art))
        scored.sort(key=lambda x: (-x[0], x[1]))  # score desc, content_hash asc — deterministic
        results: list[dict[str, Any]] = []
        for score, ch, art in scored[:limit]:
            # annotate each candidate with the emulated relevance, WITHOUT changing its claim_status.
            r = dict(art)
            r["relevance_score"] = score
            results.append(r)
        return {
            "provider_id": self.provider_id,
            "tenant_id": tenant_id,
            "project": project,
            "query": query,
            "search_mode": mode,
            "results": results,
        }

    # ── profile (profile.static / profile.dynamic shape) ─────────────────────────────────────────────────
    def profile(self, scope: dict[str, Any]) -> dict[str, Any]:
        tenant_id = scope["tenant_id"]
        project = scope["project"]
        now = int(scope["now"])
        limit = int(scope.get("limit", 10))
        bucket = self._store.get((tenant_id, project), {})
        arts = list(bucket.values())
        by_recency = sorted(arts, key=lambda a: (-int(a["lineage"]["remembered_at"]), a["content_hash"]))
        by_stable = sorted(arts, key=lambda a: a["content_hash"])
        return {
            "provider_id": self.provider_id,
            "tenant_id": tenant_id,
            "project": project,
            "static": by_stable[:limit],     # candidate long-term (≈ supermemory profile.static) — NOT promoted
            "dynamic": by_recency[:limit],   # candidate recent (≈ supermemory profile.dynamic) — NOT served
            "generated_at": now,
        }

    # ── status ─────────────────────────────────────────────────────────────────────────────────────────
    def status(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "status": _STATUS_EMULATED,
            "has_credentials": True,    # the emulator needs none; it IS the offline impl
            "credential_ref": None,
            "emulates_credential_ref": EMULATES_CREDENTIAL_REF,  # what going-live would require
            "detail": "deterministic offline Supermemory emulator (no network, no SDK, no creds)",
        }


def _self_demo(now: int = 1_000_000) -> dict[str, Any]:
    """Deterministic offline demo used by the proof. Time injected; offline; no RNG; no creds."""
    p = SupermemoryEmulatorProvider()
    a = p.write({"tenant_id": "acme", "project": "default",
                 "content": "Sanctions list updated for entity OFAC-123.", "now": now})
    p.write({"tenant_id": "acme", "project": "default", "content": "Customer asked about wire limits.",
             "now": now + 1})
    found = p.search({"tenant_id": "acme", "project": "default", "query": "sanctions OFAC"})
    prof = p.profile({"tenant_id": "acme", "project": "default", "now": now + 2})
    st = p.status()
    return {"write": a, "search": found, "profile": prof, "status": st,
            "candidate_only": all(r["claim_status"] == CANDIDATE_CLAIM_STATUS for r in found["results"]),
            "no_creds_available": st["status"] == _STATUS_EMULATED}


if __name__ == "__main__":  # pragma: no cover - manual inspection only
    import json
    print(json.dumps(_self_demo(), indent=2, default=str)[:1600])
