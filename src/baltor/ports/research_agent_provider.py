"""src.baltor.ports.research_agent_provider — the BOUNDED-RESEARCH-AGENT capability interfaces.

A research agent provider (the deterministic ``research.local_stub``, or a candidate open-ended provider
such as Hermes / OpenClaw / Claude Code / OpenHands / Open SWE) is the ONLY thing that runs an open-ended
DISCOVERY loop on Baltor's behalf. THE INVARIANT these Protocols make typeable + enforceable:

    **Agents DISCOVER and PROPOSE; Baltor STORES, VERIFIES, RECONCILES, PROVES, CONSUMES.**

A research agent may: search existing Baltor artifacts + (allowlisted) sources, compare candidates, rank
authority, draft an extractor snippet + tests, suggest a reliability rubric. A research agent may NOT: serve
or promote a fact, override reconciliation, bypass SourceArtifact storage, write a production worker queue,
use tenant-private data globally, or skip a receipt. Structurally:

  * A :class:`ResearchAgentProviderPort` ALWAYS returns a ``SourceDiscoveryReport`` whose ``serves_truth`` is
    ``False`` — never a fact. Every candidate it carries MUST carry a ``source_handle``.
  * A :class:`CodegenAgentProviderPort` ALWAYS returns an ``ExtractorSnippet`` whose ``produces`` is
    ``fact_assertion_candidate`` and ``claim_status`` is ``candidate`` — sandboxed + unit-tested, never
    served/canonical, never auto-registered.
  * Every agent action is TRACED (a replayable run trace ref accompanies the report) so a discovery can be
    audited and re-run.

A CANDIDATE provider (Hermes/OpenClaw/Claude Code/OpenHands/Open SWE) is a CATALOG ENTRY ONLY in the lean
core: it is NEVER imported or executed; its in-repo stub raises :class:`ResearchAgentUnavailable` naming the
``env://…`` credential/runtime ref it would need. The working correctness invariant is the deterministic OFFLINE
``research.local_stub@v1``. Stdlib only; no third-party SDK; no implementation that bypasses the port;
implementations MUST be deterministic when ``now`` is injected (content-addressed ids, no RNG/wall-clock).
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

#: the contract a research agent ALWAYS produces — a discovery report (candidate sources), never a fact.
RESEARCH_PRODUCES = "source_discovery_report"

#: the contract a codegen agent ALWAYS produces — a sandboxed candidate extractor, never served/canonical truth.
CODEGEN_PRODUCES = "fact_assertion_candidate"

#: the claim_status every codegen-agent output carries — a candidate, never served/canonical.
CANDIDATE_CLAIM_STATUS = "candidate"

#: serves_truth is pinned False on every agent output — THE INVARIANT, made a constant the proofs assert.
AGENT_SERVES_TRUTH = False

#: capability slot these ports populate (for the external capability catalog / replacement matrix).
RESEARCH_AGENT_SLOT = "research_agent"
SOURCE_DISCOVERY_SLOT = "source_discovery"
CODEGEN_AGENT_SLOT = "codegen_agent"

#: governance fields a SourceDiscoveryReport returned by a provider MUST carry (asserted by the proofs).
DISCOVERY_REPORT_REQUIRED_FIELDS = (
    "schema_version", "report_id", "task_id", "tenant_id", "source_scope",
    "discovered_by", "candidates", "serves_truth", "trace_ref", "discovered_at",
)

#: governance fields an ExtractorSnippet returned by a codegen provider MUST carry (asserted by the proofs).
EXTRACTOR_SNIPPET_REQUIRED_FIELDS = (
    "produces", "claim_status", "has_unit_test", "sandbox_required", "source_handle",
)


@runtime_checkable
class ResearchAgentProviderPort(Protocol):
    """One bounded research agent. ``research`` runs a bounded DISCOVERY loop for a ``ResearchTask`` and
    returns a ``SourceDiscoveryReport`` (``serves_truth=False``) plus a replayable trace — NEVER a fact. A
    candidate provider with no runtime/credential reports ``unavailable`` from ``status`` and raises
    :class:`ResearchAgentUnavailable` from ``research`` (the system stays green; the correctness invariant uses the
    deterministic local stub). Implementations MUST be deterministic when ``now`` is injected."""

    #: stable provider identity, e.g. "research.local_stub@v1" / "research.hermes@candidate".
    provider_id: str

    def describe(self) -> dict[str, Any]:
        """Return the static capability card WITHOUT running anything: provider_id, role (stub|candidate),
        status (active|candidate), the access methods it supports, and whether it is imported/executed in this
        repo (always False for candidates). No I/O, no import of any external runtime."""
        ...

    def research(self, task: dict[str, Any], *, now: str) -> dict[str, Any]:
        """Run the bounded research loop for ``task`` (a ResearchTask.v1 dict) inside task.bounds and return a
        SourceDiscoveryReport.v1 dict whose ``serves_truth`` is False, whose every candidate carries a
        ``source_handle``, and whose ``trace_ref`` points at the replayable run trace. ``now`` is injected
        (deterministic). MUST NOT serve/promote a fact, exceed task.bounds, or use secrets. A candidate
        provider raises :class:`ResearchAgentUnavailable`."""
        ...

    def status(self) -> dict[str, Any]:
        """Report provider liveness WITHOUT raising: {provider_id, status: active|candidate|unavailable,
        imported: bool, executed: bool, credential_ref?, detail}. The local stub returns status='active',
        imported/executed False (it is stdlib, runs offline). A candidate returns status='unavailable',
        imported/executed False, naming its env:// credential/runtime ref."""
        ...


@runtime_checkable
class SourceDiscoveryProviderPort(Protocol):
    """A provider that, given a ``ResearchTask``, RANKS discovered source candidates by authority/reliability
    and proposes a ``SourceRecipe`` — the M1→M2 rung. It DISCOVERS + PROPOSES; it never serves a fact. It MUST
    search EXISTING Baltor artifacts FIRST (cheapest rung) before proposing a new external source. Output is a
    SourceDiscoveryReport (``serves_truth=False``) + a proposed SourceRecipe; both are candidates."""

    provider_id: str

    def discover(self, task: dict[str, Any], *, existing_handles: list[str], now: str) -> dict[str, Any]:
        """Search ``existing_handles`` FIRST, then rank candidates by authority_rank (a FAQ can never outrank a
        regulation). Returns {report: SourceDiscoveryReport.v1, candidates: list[SourceCandidate.v1],
        scores: list[SourceReliabilityScore.v1], proposed_recipe: SourceRecipe.v1, reused_existing: bool}.
        ``serves_truth`` on the report is pinned False; ``now`` injected. Proposes, never promotes."""
        ...


@runtime_checkable
class CodegenAgentProviderPort(Protocol):
    """A provider that drafts a DETERMINISTIC extractor snippet (+ unit tests) for a SourceRecipe. Its output
    is an ``ExtractorSnippet`` whose ``produces`` is ``fact_assertion_candidate`` and ``claim_status`` is
    ``candidate`` — sandboxed + unit-tested, NEVER served/canonical, NEVER auto-registered as a production
    worker. A candidate provider raises :class:`ResearchAgentUnavailable` (catalog entry only). The snippet is
    gated by a separate sandbox + proof step (built in the SANDBOX lane / MAIN) before any use."""

    provider_id: str

    def draft_extractor(self, recipe: dict[str, Any], *, now: str) -> dict[str, Any]:
        """Draft an ExtractorSnippet.v1 dict for ``recipe`` (a SourceRecipe.v1). MUST set
        produces='fact_assertion_candidate', claim_status='candidate', has_unit_test=True,
        sandbox_required=True, and a source_handle. MUST NOT mark the snippet served/canonical/active and MUST
        NOT execute the drafted code. ``now`` injected (deterministic)."""
        ...

    def status(self) -> dict[str, Any]:
        """Report liveness WITHOUT raising, same shape as ResearchAgentProviderPort.status."""
        ...


class ResearchAgentUnavailable(Exception):
    """A research/codegen agent provider's runtime / credential is not present in this repo. Carries the
    missing ``credential_ref`` (an ``env://…`` reference, never a value) so callers can report WHAT is missing
    without leaking a secret and WITHOUT importing/executing the candidate runtime.

    Raised by the candidate provider stubs (Hermes/OpenClaw/Claude Code/OpenHands/Open SWE) — they are catalog
    entries only. The system stays green: the correctness invariant uses the deterministic local stub instead."""

    def __init__(self, provider_id: str, credential_ref: str, detail: str = "") -> None:
        self.provider_id = provider_id
        self.credential_ref = credential_ref  # an env://… REF, never a secret value
        msg = (f"research agent {provider_id!r} is a catalog candidate only (not imported/executed in this "
               f"repo): missing runtime/credential {credential_ref}")
        if detail:
            msg += f" ({detail})"
        super().__init__(msg)
