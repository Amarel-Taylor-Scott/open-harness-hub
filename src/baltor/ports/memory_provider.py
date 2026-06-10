"""src.baltor.ports.memory_provider — the memory/context-provider capability interfaces.

A memory provider (Supermemory candidate, a Baltor-local store, or a deterministic emulator) is the ONLY
thing that touches an upstream memory/recall backend. Its write/search/profile/MCP-tool outputs are always
governed ``MemoryArtifact`` records carrying ``claim_status="candidate"`` + ``tenant_id`` + project/container
scope + an ``external_source_handle`` (the upstream id) + ``lineage`` — and NOTHING that is served/canonical.

GOVERNANCE LINES (the whole point — these Protocols exist to make the lines typeable, enforced in proofs):
  remembered != verified · retrieved != served · profiled != canonical · candidate memory != promoted fact.
A recall result becomes a candidate MemoryArtifact, NEVER a served/canonical fact — it can only become a
CanonicalFact through Baltor's existing VerificationGate + Reconciliation + ConsumptionGate downstream. No
provider here verifies, promotes, serves, or reconciles. Supermemory is NEVER the source of truth.

LOSSLESS DISTILLATION (docs/codex/lossless-distillation.md): any transform is lossless at the system level —
a provider never overwrites/deletes raw/source; it preserves source handles, lineage, version; omitted /
held-out is never deleted. These Protocols carry the fields that make that auditable.

This is the typed, reusable Protocol home for the memory-provider seam. Implementations live under
``src/baltor/adapters/memory/`` (baltor_local working provider, supermemory_emulator working offline
contract impl, supermemory_api / supermemory_mcp candidate contract stubs). Stdlib only; no third-party SDK;
no implementation that bypasses the port. Implementations MUST be deterministic when time is injected.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

#: the ONLY claim_status a fresh provider output may carry. A memory result is a candidate, never served.
CANDIDATE_CLAIM_STATUS = "candidate"

#: claim_status values a provider output must NEVER carry (those are the downstream gates' job, not memory's).
FORBIDDEN_CLAIM_STATUSES = frozenset({"served", "canonical", "verified", "promoted", "fact"})

#: required governance fields on every MemoryArtifact (asserted by the proofs).
MEMORY_ARTIFACT_REQUIRED_FIELDS = (
    "artifact_id", "artifact_type", "claim_status", "tenant_id", "project",
    "external_source_handle", "lineage", "content_hash",
)

#: the artifact_type every memory-provider output uses (a candidate memory, not a source/served record).
MEMORY_ARTIFACT_TYPE = "memory_artifact"

#: capability slots these ports populate (for the external capability catalog / replacement matrix).
MEMORY_PROVIDER_SLOT = "memory_provider"
MCP_TOOL_PROVIDER_SLOT = "mcp_tool_provider"


# ── request / result shapes (plain dict-shaped TypedDict-style contracts; documented, not enforced types) ──
# Implementations accept and return plain dicts so the seam stays stdlib-only and JSON-roundtrippable. The
# docstrings below ARE the contract; the proofs assert the governance-bearing fields are present and correct.

@runtime_checkable
class MemoryProviderPort(Protocol):
    """One governed memory/recall provider. ``write``/``search`` return ``MemoryArtifact`` records that are
    ALWAYS ``claim_status="candidate"`` with a populated ``external_source_handle`` + ``lineage`` — never a
    served/canonical fact. ``status`` reports liveness without raising on a dead/credential-less backend.
    Implementations MUST be deterministic when ``now`` is injected (content-addressed ids, no RNG/wall-clock).
    """

    #: stable provider identity, e.g. "memory.baltor_local@v1" / "memory.supermemory_api@candidate".
    provider_id: str

    def write(self, request: dict[str, Any]) -> dict[str, Any]:
        """Remember one item. ``request`` is a MemoryWriteRequest: {tenant_id, project, content, now,
        metadata?, container_tags?}. Returns ONE MemoryArtifact (claim_status="candidate") carrying
        tenant_id + project scope + external_source_handle (the upstream/provider id) + lineage +
        content_hash. MUST NOT mark the result served/canonical/verified and MUST NOT cross tenant scope."""
        ...

    def search(self, request: dict[str, Any]) -> dict[str, Any]:
        """Recall items. ``request`` is a MemorySearchRequest: {tenant_id, project, query, now, limit?,
        search_mode?}. Returns a MemorySearchResult: {tenant_id, project, query, results: list[MemoryArtifact]}
        where EVERY result is claim_status="candidate" and scoped to ``tenant_id`` — a search in tenant A
        NEVER returns tenant B's artifacts. Results are candidates, never served facts."""
        ...

    def status(self) -> dict[str, Any]:
        """Report provider liveness WITHOUT raising. Returns a MemoryProviderStatus:
        {provider_id, status: available|emulated|unavailable, has_credentials: bool, detail, credential_ref?}.
        A candidate API/MCP stub with no creds returns status="unavailable" naming its env:// credential ref;
        the emulator returns status="emulated"; the local provider returns status="available"."""
        ...


@runtime_checkable
class MemoryProfileProviderPort(Protocol):
    """A provider that can project a governed PROFILE for a scope (static long-term + dynamic recent), modeled
    on supermemory's profile.static/profile.dynamic but as a CANDIDATE projection — never canonical. The
    profile's entries are MemoryArtifacts (claim_status="candidate"); a static entry is NOT a promoted fact.
    """

    def profile(self, scope: dict[str, Any]) -> dict[str, Any]:
        """Project a MemoryProfile for ``scope`` ({tenant_id, project, now, limit?}). Returns
        {tenant_id, project, static: list[MemoryArtifact], dynamic: list[MemoryArtifact], generated_at} where
        EVERY entry is claim_status="candidate", tenant/project-scoped, and carries external_source_handle +
        lineage. ``static`` = long-lived candidate memories; ``dynamic`` = recent candidate context. Neither
        is a served/canonical fact — promotion happens only downstream through the existing gates."""
        ...


@runtime_checkable
class MemoryMCPProviderPort(Protocol):
    """An MCP-tool surface for governed memory (the ``memory`` / ``recall`` / ``context`` tools). Each tool
    returns governed candidate MemoryArtifacts, NEVER served facts. A candidate stub with no creds raises a
    clear UnavailableProvider naming its env:// credential ref (the system stays green; tool just unavailable).
    """

    #: stable MCP provider identity, e.g. "mcp.supermemory@candidate".
    provider_id: str

    def tools(self) -> list[str]:
        """List the MCP tool names this provider exposes (a subset/superset of {'memory','recall','context'})."""
        ...

    def memory(self, request: dict[str, Any]) -> dict[str, Any]:
        """MCP ``memory`` tool — remember. Same contract as MemoryProviderPort.write: returns ONE
        candidate MemoryArtifact (claim_status="candidate") with external_source_handle + lineage."""
        ...

    def recall(self, request: dict[str, Any]) -> dict[str, Any]:
        """MCP ``recall`` tool — search. Same contract as MemoryProviderPort.search: returns a
        MemorySearchResult of candidate MemoryArtifacts, tenant/project-scoped, never served facts."""
        ...

    def context(self, scope: dict[str, Any]) -> dict[str, Any]:
        """MCP ``context`` tool — project a MemoryProfile (static + dynamic), all candidate MemoryArtifacts."""
        ...


class UnavailableProvider(Exception):
    """A memory provider's upstream backend / credential is not present. Carries the missing ``credential_ref``
    (an ``env://…`` reference, never a value) so callers can report WHAT is missing without leaking a secret.

    Raised by the candidate API/MCP stubs when no credentials are configured. The system stays green — the
    provider is simply unavailable and the correctness invariant uses the working local provider / emulator instead.
    """

    def __init__(self, provider_id: str, credential_ref: str, detail: str = "") -> None:
        self.provider_id = provider_id
        self.credential_ref = credential_ref  # an env://… REF, never a secret value
        msg = f"memory provider {provider_id!r} is unavailable: missing credential {credential_ref}"
        if detail:
            msg += f" ({detail})"
        super().__init__(msg)
