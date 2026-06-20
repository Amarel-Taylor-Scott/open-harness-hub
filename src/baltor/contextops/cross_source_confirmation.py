#!/usr/bin/env python3
"""contextops/cross_source_confirmation — DETERMINISTIC cross-source confirmation policies (Lane D).

A VerificationRecipe declares HOW MANY and WHICH KINDS of sources must agree before an extracted candidate
counts as confirmed. This module evaluates those policies over the candidate's backing sources + their
reliability scores and returns a checkable :class:`ConfirmationResult` (confirmed / why / which handles /
whether a human must sign off). It NEVER serves or promotes a fact — it only decides whether the
cross-source bar is met; reconciliation/publication happen elsewhere.

The six policies (single source — matches the VerificationRecipe.cross_source.policy enum):
  single_official_source_ok · two_independent_sources_required · official_source_plus_secondary_confirmation ·
  tenant_private_requires_human_signoff · llm_claim_requires_source_artifact · current_value_requires_fresh_source.

Two invariant-bearing policies: ``tenant_private_requires_human_signoff`` (a tenant-private source can never
auto-confirm a fact — a human must sign off) and ``llm_claim_requires_source_artifact`` (an LLM-origin claim
with no backing SourceArtifact handle is NEVER confirmed — the model cannot be its own evidence).

Deterministic + offline: no clock (freshness uses INJECTED ``now`` + each source's ``fetched_at``), no RNG,
no network. stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.baltor.contextops.reliability import default_authority_rank

#: the six confirmation policies (single source — matches VerificationRecipe.cross_source.policy + the spec).
POLICIES = (
    "single_official_source_ok",
    "two_independent_sources_required",
    "official_source_plus_secondary_confirmation",
    "tenant_private_requires_human_signoff",
    "llm_claim_requires_source_artifact",
    "current_value_requires_fresh_source",
)

#: source_types that count as "official" / source-of-record for the official-source policies.
_OFFICIAL_TYPES = ("source_of_law", "regulation", "statute", "official_agency", "primary_dataset")
#: the minimum authority_rank an official source must clear (a low-rank "official" can't carry it alone) —
#: DERIVED from the reliability map (the lowest-ranked official type's rank), not a hand-typed literal coupled
#: to that scale; pinned to min(_OFFICIAL_TYPES) so it tracks the map if the official tiers are re-ranked.
_OFFICIAL_MIN_RANK = min(default_authority_rank(t) for t in _OFFICIAL_TYPES)


class CrossSourceError(Exception):
    """Raised on a malformed policy / source record — explicit failure, never a silent pass."""


@dataclass(frozen=True)
class ConfirmedSource:
    """One backing source for a candidate, as seen by the confirmation evaluator (a discovered/stored source)."""

    source_handle: str            # REQUIRED — a source with no handle cannot confirm anything
    source_type: str
    scope: str = "global_public"  # global_public / tenant_private / tenant_shared / system_reference
    authority_rank: int | None = None  # None → derived from source_type
    fetched_at: int | None = None      # injected epoch seconds of the read (for freshness); None → unknown
    origin: str = "source_artifact"    # "source_artifact" | "llm_claim" — an llm_claim is never its own evidence
    independent_group: str = ""        # publisher/lineage group; two sources in the SAME group aren't independent

    @property
    def effective_rank(self) -> int:
        return default_authority_rank(self.source_type) if self.authority_rank is None else self.authority_rank

    @property
    def is_official(self) -> bool:
        return self.source_type in _OFFICIAL_TYPES and self.effective_rank >= _OFFICIAL_MIN_RANK

    @property
    def group_key(self) -> str:
        return self.independent_group or self.source_handle


@dataclass(frozen=True)
class ConfirmationResult:
    """The checkable outcome of evaluating a cross-source policy. NEVER a served fact."""

    policy: str
    confirmed: bool
    reason: str
    confirming_handles: list[str] = field(default_factory=list)
    human_signoff_required: bool = False
    served_as_truth: bool = False  # PINNED False — confirmation decides the bar, it never serves truth

    def to_dict(self) -> dict:
        return {"policy": self.policy, "confirmed": self.confirmed, "reason": self.reason,
                "confirming_handles": list(self.confirming_handles),
                "human_signoff_required": self.human_signoff_required, "served_as_truth": self.served_as_truth}


def _independent(sources) -> list:
    """Distinct sources by independence group (two readings of the same publisher are NOT independent)."""
    seen, out = set(), []
    for s in sorted(sources, key=lambda x: x.source_handle):
        if s.group_key not in seen:
            seen.add(s.group_key)
            out.append(s)
    return out


def confirm(policy: str, sources, *, now: int = 0, is_current_value: bool = False,
            max_staleness_seconds: int = 0, has_human_signoff: bool = False) -> ConfirmationResult:
    """Evaluate a cross-source confirmation ``policy`` over the candidate's backing ``sources``.

    ``now`` + ``max_staleness_seconds`` drive the freshness policy (injected time). ``is_current_value`` marks
    a fact whose value moves (rate/fee/deadline/current) and therefore needs a fresh read.
    ``has_human_signoff`` is the human-approval hook for tenant-private confirmation.
    """
    if policy not in POLICIES:
        raise CrossSourceError(f"unknown cross-source policy {policy!r}; not one of {POLICIES}")
    srcs = [s for s in sources if isinstance(s, ConfirmedSource)]
    # an llm-origin "source" with no real source artifact handle never counts as evidence under ANY policy.
    with_handles = [s for s in srcs if s.source_handle and s.origin == "source_artifact"]
    official = [s for s in with_handles if s.is_official]
    indep = _independent(with_handles)

    if policy == "single_official_source_ok":
        if official:
            return ConfirmationResult(policy, True, "a single official source-of-record is sufficient for this fact",
                                      [official[0].source_handle])
        return ConfirmationResult(policy, False, "no official source-of-record among the backing sources")

    if policy == "two_independent_sources_required":
        if len(indep) >= 2:
            return ConfirmationResult(policy, True, "two independent sources agree",
                                      [indep[0].source_handle, indep[1].source_handle])
        return ConfirmationResult(policy, False,
                                  f"need 2 independent sources, have {len(indep)} (same-publisher reads don't count)")

    if policy == "official_source_plus_secondary_confirmation":
        # one official anchor + any INDEPENDENT second source (a different publisher/lineage group);
        # the secondary may itself be official — it only has to corroborate from a distinct group.
        if official:
            anchor = official[0]
            secondary = [s for s in indep if s.group_key != anchor.group_key]
            if secondary:
                return ConfirmationResult(policy, True, "an official source plus an independent secondary confirm",
                                          [anchor.source_handle, secondary[0].source_handle])
        return ConfirmationResult(policy, False,
                                  "need an official source AND an independent secondary confirmation")

    if policy == "tenant_private_requires_human_signoff":
        # a tenant_private source can NEVER auto-confirm — a human must sign off (invariant).
        if not has_human_signoff:
            return ConfirmationResult(policy, False,
                                      "tenant_private source cannot auto-confirm a fact; human signoff required",
                                      [s.source_handle for s in srcs if s.scope == "tenant_private"],
                                      human_signoff_required=True)
        return ConfirmationResult(policy, True, "human signed off on the tenant_private source",
                                  [s.source_handle for s in srcs if s.scope == "tenant_private"],
                                  human_signoff_required=True)

    if policy == "llm_claim_requires_source_artifact":
        # the model cannot be its own evidence — an LLM claim must be backed by a stored SourceArtifact handle.
        if with_handles:
            return ConfirmationResult(policy, True, "the LLM claim is backed by a stored source artifact",
                                      [with_handles[0].source_handle])
        return ConfirmationResult(policy, False,
                                  "an LLM-origin claim with no backing source artifact is never confirmed")

    # current_value_requires_fresh_source
    if is_current_value:
        fresh = [s for s in with_handles
                 if s.fetched_at is not None and (now - s.fetched_at) <= max_staleness_seconds]
        if fresh:
            return ConfirmationResult(policy, True,
                                      f"a current value confirmed by a fresh source read (<= {max_staleness_seconds}s old)",
                                      [fresh[0].source_handle])
        return ConfirmationResult(policy, False,
                                  "a current/rate/fee/deadline value requires a FRESH source read; none is fresh enough")
    # not a current value → a stored source is acceptable.
    if with_handles:
        return ConfirmationResult(policy, True, "value is not time-sensitive; a stored source confirms it",
                                  [with_handles[0].source_handle])
    return ConfirmationResult(policy, False, "no backing source artifact to confirm against")
