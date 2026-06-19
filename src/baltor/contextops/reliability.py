#!/usr/bin/env python3
"""contextops/reliability — DETERMINISTIC source-reliability scoring (Lane D).

Reconciliation needs a checkable answer to "which source wins?". This module produces a
:class:`SourceReliabilityScore` — the multi-factor assessment that carries the load-bearing ``authority_rank``
(source-of-law outranks an agency FAQ) plus the per-factor signals (officialness, freshness, stability,
machine_readability, contradiction_rate, availability, parse_stability, historical_accuracy) and a derived
``overall`` composite. tenant_scope is recorded so a tenant_private source can never silently back a global
fact. A reliability score RANKS sources; it is NEVER itself a served fact (``served_as_truth`` pinned False).

Conforms to ``schemas/contextops/SourceReliabilityScore.v1.schema.json``. Deterministic: the same candidate +
the same factors → the same ``score_id`` and the same ``overall``, every run. Time is INJECTED (``scored_at``);
no clock, no RNG, no network. stdlib only.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

#: AUTHORITY_RANK + default_authority_rank + scope_adjusted_rank are the SHARED canonical contextops map — the
#: three subsystems were unified onto it on 2026-06-18 (A3). reliability and source_discovery now read ONE map;
#: precedence is scope-aware (a tenant's own doc wins for tenant_private facts). Re-exported so existing
#: `from ...reliability import AUTHORITY_RANK` / `default_authority_rank` callers keep working unchanged.
from src.baltor.contextops.authority_rank import (  # noqa: E402  (intra-Baltor shared vocabulary)
    AUTHORITY_RANK, default_authority_rank, scope_adjusted_rank)

#: the eight per-factor signals the composite is derived from (single source — matches the closed factors block
#: in SourceReliabilityScore.v1). contradiction_rate is "lower is better", so it is INVERTED in the composite.
FACTOR_NAMES = (
    "officialness", "freshness", "stability", "machine_readability",
    "contradiction_rate", "availability", "parse_stability", "historical_accuracy",
)
#: factors where a HIGHER raw value is WORSE — inverted before they enter the composite.
_INVERTED_FACTORS = ("contradiction_rate",)

#: weight of the authority_rank (normalized to 0..1 over a 0..100 scale) in the overall composite vs the
#: mean of the eight factors. Authority is the dominant precedence signal but factors temper it.
_AUTHORITY_WEIGHT = 0.5
_FACTOR_WEIGHT = 0.5
_AUTHORITY_SCALE = 100.0  # authority_rank is expressed on a 0..100 scale; normalize by this for the composite.
#: composites are rounded to this many places so the value is stable across platforms (deterministic).
_ROUND = 4


class ReliabilityError(Exception):
    """Raised on a malformed factor set — an explicit failure, never a silently-defaulted score."""


@dataclass(frozen=True)
class SourceReliabilityScore:
    """A derived reliability assessment of one SourceCandidate. RANKS sources; never a served fact.

    ``served_as_truth`` is pinned False. ``overall`` is a pure function of (authority_rank, factors) so the
    same inputs always yield the same composite. ``tenant_scope_ok`` records whether the source's scope
    matches the fact's scope (a tenant_private source can't back a global fact).
    """

    candidate_id: str
    tenant_id: str
    source_scope: str
    authority_rank: int
    factors: dict[str, float]
    scored_at: int                       # injected epoch seconds — never wall-clock
    rate_limit_risk: str = "none"
    tenant_scope_ok: bool = True
    served_as_truth: bool = False        # PINNED False — a score ranks, it is never served truth

    def __post_init__(self) -> None:
        missing = [f for f in FACTOR_NAMES if f not in self.factors]
        if missing:
            raise ReliabilityError(f"factors missing required signals: {missing}")
        extra = [f for f in self.factors if f not in FACTOR_NAMES]
        if extra:
            raise ReliabilityError(f"factors carry unknown signals (closed set): {extra}")
        for f, v in self.factors.items():
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not (0.0 <= float(v) <= 1.0):
                raise ReliabilityError(f"factor {f!r} must be a number in 0..1, got {v!r}")
        if self.served_as_truth:
            raise ReliabilityError("served_as_truth must be False — a reliability score is never served truth")

    @property
    def overall(self) -> float:
        """The derived 0..1 composite: a weighted blend of normalized authority_rank and the eight factors."""
        adj = []
        for f in FACTOR_NAMES:
            v = float(self.factors[f])
            adj.append(1.0 - v if f in _INVERTED_FACTORS else v)
        factor_mean = sum(adj) / len(adj)
        auth_norm = max(0.0, min(1.0, self.authority_rank / _AUTHORITY_SCALE))
        composite = _AUTHORITY_WEIGHT * auth_norm + _FACTOR_WEIGHT * factor_mean
        return round(composite, _ROUND)

    @property
    def score_id(self) -> str:
        body = {"cand": self.candidate_id, "ar": self.authority_rank,
                "factors": {f: float(self.factors[f]) for f in FACTOR_NAMES}, "ten": self.tenant_id}
        return "srs-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {"schema_version": "SourceReliabilityScore.v1", "score_id": self.score_id,
                "candidate_id": self.candidate_id, "tenant_id": self.tenant_id,
                "source_scope": self.source_scope, "authority_rank": self.authority_rank,
                "factors": {f: float(self.factors[f]) for f in FACTOR_NAMES},
                "rate_limit_risk": self.rate_limit_risk, "tenant_scope_ok": self.tenant_scope_ok,
                "composite_score": self.overall, "served_as_truth": self.served_as_truth,
                "scored_at": self.scored_at}


def score_source(*, candidate_id: str, source_type: str, factors: dict, tenant_id: str = "",
                 source_scope: str = "global_public", fact_scope: str | None = None,
                 rate_limit_risk: str = "none", authority_rank: int | None = None,
                 scored_at: int = 0) -> SourceReliabilityScore:
    """Score one SourceCandidate deterministically.

    ``authority_rank`` defaults to the source_type's canonical rank (source-of-law > FAQ) unless an explicit
    rank is supplied. ``tenant_scope_ok`` is computed: a tenant_private source can only back a fact of the
    SAME tenant_private scope; everything else (global/system) requires a non-tenant-private source.
    """
    rank = scope_adjusted_rank(source_type, source_scope, fact_scope) if authority_rank is None else authority_rank
    scope_ok = True
    if fact_scope is not None:
        if source_scope == "tenant_private":
            scope_ok = fact_scope == "tenant_private"
        # a global/system fact may be backed by global_public / system_reference / tenant_shared, not tenant_private.
    return SourceReliabilityScore(
        candidate_id=candidate_id, tenant_id=tenant_id, source_scope=source_scope, authority_rank=rank,
        factors={f: float(factors[f]) for f in FACTOR_NAMES if f in factors} | {f: float(factors.get(f, 0.0)) for f in FACTOR_NAMES},
        rate_limit_risk=rate_limit_risk, tenant_scope_ok=scope_ok, scored_at=scored_at)


def outranks(a: SourceReliabilityScore, b: SourceReliabilityScore) -> bool:
    """True iff ``a`` wins over ``b`` for reconciliation: higher authority_rank, ties broken by overall.

    This is the precedence reconciliation reads. A FAQ (rank 30) can NEVER outrank a regulation (rank 90),
    regardless of its other factors — authority dominates, the composite only breaks ties at equal authority.
    """
    if a.authority_rank != b.authority_rank:
        return a.authority_rank > b.authority_rank
    if a.overall != b.overall:
        return a.overall > b.overall
    return a.score_id > b.score_id  # final deterministic tiebreak (stable, content-addressed)
