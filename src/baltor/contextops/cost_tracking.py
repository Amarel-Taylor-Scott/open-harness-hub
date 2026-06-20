#!/usr/bin/env python3
"""src.baltor.contextops.cost_tracking — the M0→M7 cost-reduction ladder (the economic moat, made visible).

This is the SYNTHESIS metric layer of the ContextOps Verification Foundry. It does not verify anything itself;
it OBSERVES a deterministic sequence of verification events for a fact_key and computes the cost-reduction
story the dashboard tells: *unbounded LLM cost → a bounded research ONCE → deterministic verification FOREVER*.

The economic model (single source — the M0→M7 ladder from the spec):

  * M0 baseline — ask the LLM EVERY time a fact is needed (the cost we are replacing). Every verification, in
    the M0 world, is one expensive LLM call (``LLM_BASELINE_TOKENS`` tokens).
  * M1 ``agent_research`` — the FIRST time a fact is verified, a bounded research agent does the expensive
    discovery (``AGENT_RESEARCH_TOKENS``). This happens ONCE per fact; its product (a SourceRecipe + extractor)
    is reused forever after.
  * M3 ``deterministic_verify`` — every subsequent verification runs the deterministic extractor: cheap, a
    handful of tokens of bookkeeping (``DETERMINISTIC_VERIFY_TOKENS``), no model in the loop.
  * M5/M6 ``cached_fact_hit`` — a query that hits the already-verified canonical fact + its receipt: near-zero
    (``CACHED_HIT_TOKENS``).
  * M5 ``scheduled_hashcheck`` — a scheduled watch re-confirms the source hasn't moved by a hash check:
    near-zero (``HASHCHECK_TOKENS``), and counts as an avoided LLM call (the M0 world would have re-asked).
  * ``source_fetch`` — fetching/refreshing a source recipe's payload; cheap I/O bookkeeping, not an LLM call.

EVERY event that is NOT an ``agent_research`` is an LLM call the M0 baseline would have spent and we did not —
so ``llm_calls_avoided`` rises with every deterministic verify / cached hit / scheduled check.

Determinism: token costs are INJECTED named constants (no pricing lookup, no clock, no RNG); the ladder id is a
``hashlib`` content hash over the event kinds; time is INJECTED. stdlib only, fully offline.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

# ── the event kinds the ladder understands (single source — each maps to one rung of M0→M7). ──────────────
AGENT_RESEARCH = "agent_research"            # M1 — the expensive ONCE-per-fact bounded research discovery
DETERMINISTIC_VERIFY = "deterministic_verify"  # M3 — the cheap deterministic extractor re-verification
CACHED_FACT_HIT = "cached_fact_hit"          # M5/M6 — a query served from the canonical fact + receipt
SCHEDULED_HASHCHECK = "scheduled_hashcheck"  # M5 — a scheduled watch confirms the source hasn't moved
SOURCE_FETCH = "source_fetch"                # source payload fetch/refresh (cheap I/O, not an LLM call)

EVENT_KINDS = (AGENT_RESEARCH, DETERMINISTIC_VERIFY, CACHED_FACT_HIT, SCHEDULED_HASHCHECK, SOURCE_FETCH)

#: INJECTED per-event token costs (no pricing API, no clock). Tokens are a deterministic proxy for cost so the
#: ladder is reproducible. The shape that matters: agent research is EXPENSIVE; the deterministic verify is
#: CHEAP; a cached hit / scheduled hash-check is NEAR-ZERO. One definition each — never literal'd elsewhere.
LLM_BASELINE_TOKENS = 4000        # M0 — what one LLM call would cost if we re-asked the model every time.
AGENT_RESEARCH_TOKENS = 6000      # M1 — the bounded research discovery is MORE than one M0 call, but ONCE.
DETERMINISTIC_VERIFY_TOKENS = 40  # M3 — deterministic extractor bookkeeping; ~100x cheaper than an LLM call.
CACHED_HIT_TOKENS = 2            # M5/M6 — read a stored canonical fact + receipt; near-zero.
HASHCHECK_TOKENS = 5            # M5 — a source-unchanged hash check; near-zero.
SOURCE_FETCH_TOKENS = 10           # source payload fetch; cheap I/O, not a model call.

#: token cost per event kind (single source — derived from the named constants above, never a parallel literal).
EVENT_TOKEN_COST: dict[str, int] = {
    AGENT_RESEARCH: AGENT_RESEARCH_TOKENS,
    DETERMINISTIC_VERIFY: DETERMINISTIC_VERIFY_TOKENS,
    CACHED_FACT_HIT: CACHED_HIT_TOKENS,
    SCHEDULED_HASHCHECK: HASHCHECK_TOKENS,
    SOURCE_FETCH: SOURCE_FETCH_TOKENS,
}

#: event kinds that, in the M0 world, would each have been one fresh LLM call we therefore AVOIDED. An
#: ``agent_research`` is NOT avoided — it is the one bounded research we DO spend so the rest can be avoided.
_AVOIDS_LLM_CALL = frozenset({DETERMINISTIC_VERIFY, CACHED_FACT_HIT, SCHEDULED_HASHCHECK})

#: an event kind that constitutes a "verification" (a fact was actually checked) — used for cost_per_verified_fact.
_VERIFICATION_KINDS = frozenset({AGENT_RESEARCH, DETERMINISTIC_VERIFY})

_ROUND = 4  # round derived ratios so the metrics are byte-stable across platforms (deterministic).
_ID_PREFIX = "costladder-"


class CostTrackingError(Exception):
    """Raised on an unknown event kind — an explicit failure, never a silently-dropped cost."""


@dataclass(frozen=True)
class CostEvent:
    """One observed ContextOps event. ``kind`` is one of EVENT_KINDS; ``fact_key`` ties it to the fact it
    verified/served; ``at`` is an INJECTED ISO stamp (never a clock read). The token cost is DERIVED from the
    kind (EVENT_TOKEN_COST) — a caller never hand-types a cost, so two events of the same kind never drift."""

    kind: str
    fact_key: str
    at: str = "1970-01-01T00:00:00Z"

    def __post_init__(self) -> None:
        if self.kind not in EVENT_KINDS:
            raise CostTrackingError(f"unknown cost event kind {self.kind!r}; not one of {EVENT_KINDS}")

    @property
    def token_cost(self) -> int:
        return EVENT_TOKEN_COST[self.kind]

    @property
    def avoids_llm_call(self) -> bool:
        return self.kind in _AVOIDS_LLM_CALL


@dataclass(frozen=True)
class CostLadderMetrics:
    """The computed M0→M7 cost-reduction metrics for a sequence of events (the dashboard's moat numbers).

    ``token_cost_before`` is the M0 baseline (one LLM call PER verification, every time). ``token_cost_after``
    is what the ContextOps ladder actually spent (one expensive research + cheap deterministic verifies +
    near-zero cached/scheduled). ``cost_reduction_estimate`` is the fraction saved (0..1); it is > 0 the moment
    a single deterministic verify or cached hit replaces an M0 LLM call. ``serves_truth`` is pinned False — a
    cost metric is an OBSERVATION, never a served fact."""

    ladder_id: str
    fact_keys: tuple[str, ...]
    llm_calls_avoided: int
    agent_research_runs: int
    deterministic_verifications: int
    cached_fact_hits: int
    source_fetches: int
    scheduled_watch_runs: int
    token_cost_before: int
    token_cost_after: int
    cost_per_verified_fact: float
    cost_reduction_estimate: float
    serves_truth: bool = False
    computed_at: str = "1970-01-01T00:00:00Z"
    per_rung_tokens: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "schema_version": "CostLadderMetrics.v1",
            "ladder_id": self.ladder_id,
            "fact_keys": list(self.fact_keys),
            "llm_calls_avoided": self.llm_calls_avoided,
            "agent_research_runs": self.agent_research_runs,
            "deterministic_verifications": self.deterministic_verifications,
            "cached_fact_hits": self.cached_fact_hits,
            "source_fetches": self.source_fetches,
            "scheduled_watch_runs": self.scheduled_watch_runs,
            "token_cost_before": self.token_cost_before,
            "token_cost_after": self.token_cost_after,
            "cost_per_verified_fact": self.cost_per_verified_fact,
            "cost_reduction_estimate": self.cost_reduction_estimate,
            "serves_truth": self.serves_truth,
            "computed_at": self.computed_at,
            "per_rung_tokens": dict(self.per_rung_tokens),
        }


def _ladder_id(events) -> str:
    body = {"kinds": [e.kind for e in events], "fks": sorted({e.fact_key for e in events})}
    return _ID_PREFIX + hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]


def compute_cost_ladder(events, *, now: str = "1970-01-01T00:00:00Z") -> CostLadderMetrics:
    """Compute the M0→M7 cost-reduction metrics over a deterministic sequence of :class:`CostEvent`.

    The M0 baseline (``token_cost_before``) is one LLM call PER verification event (the world where we re-ask
    the model every time we need the fact). ``token_cost_after`` is the actual ContextOps spend (the injected
    per-kind token costs). ``llm_calls_avoided`` counts every deterministic verify / cached hit / scheduled
    check (each of which the M0 world would have spent on a fresh LLM call). Deterministic: identical events +
    same ``now`` → identical metrics (no clock, no RNG; costs are injected named constants).
    """
    evs = list(events)
    counts = {k: 0 for k in EVENT_KINDS}
    per_rung = {k: 0 for k in EVENT_KINDS}
    token_cost_after = 0
    llm_calls_avoided = 0
    verifications = 0
    for e in evs:
        if not isinstance(e, CostEvent):
            raise CostTrackingError(f"expected CostEvent, got {type(e).__name__}")
        counts[e.kind] += 1
        per_rung[e.kind] += e.token_cost
        token_cost_after += e.token_cost
        if e.avoids_llm_call:
            llm_calls_avoided += 1
        if e.kind in _VERIFICATION_KINDS:
            verifications += 1

    # M0 baseline: one LLM call per verification event (we re-asked the model every single time).
    token_cost_before = verifications * LLM_BASELINE_TOKENS
    # cost per verified fact: actual spend amortized over the verifications it bought (the ladder's whole point
    # is that this falls as deterministic verifies amortize the one-time research).
    cost_per_verified_fact = round(token_cost_after / verifications, _ROUND) if verifications else 0.0
    # cost reduction estimate: fraction of the M0 baseline we did NOT spend (0..1). > 0 the moment a single
    # deterministic verify / cached hit replaces an M0 LLM call.
    cost_reduction_estimate = (
        round((token_cost_before - token_cost_after) / token_cost_before, _ROUND)
        if token_cost_before > 0 else 0.0
    )

    return CostLadderMetrics(
        ladder_id=_ladder_id(evs),
        fact_keys=tuple(sorted({e.fact_key for e in evs})),
        llm_calls_avoided=llm_calls_avoided,
        agent_research_runs=counts[AGENT_RESEARCH],
        deterministic_verifications=counts[DETERMINISTIC_VERIFY],
        cached_fact_hits=counts[CACHED_FACT_HIT],
        source_fetches=counts[SOURCE_FETCH],
        scheduled_watch_runs=counts[SCHEDULED_HASHCHECK],
        token_cost_before=token_cost_before,
        token_cost_after=token_cost_after,
        cost_per_verified_fact=cost_per_verified_fact,
        cost_reduction_estimate=cost_reduction_estimate,
        computed_at=now,
        per_rung_tokens={k: per_rung[k] for k in EVENT_KINDS if per_rung[k]},
    )


def cfpb_reference_lifecycle(fact_key: str, *, now: str = "1970-01-01T00:00:00Z") -> list[CostEvent]:
    """The canonical CFPB-fact lifecycle as a deterministic event sequence, demonstrating the ladder shape:

      1. FIRST verification — an ``agent_research`` (expensive, ONCE) + the ``source_fetch`` it commissioned;
      2. SECOND verification — a ``deterministic_verify`` (cheap; the extractor reuses M1's product, no LLM);
      3. ongoing consumption — a ``cached_fact_hit`` (near-zero; served from the canonical fact + receipt);
      4. a scheduled watch — a ``scheduled_hashcheck`` (near-zero; confirms the source hasn't moved).

    Reusable by proofs + the dashboard; deterministic over (fact_key, now)."""
    return [
        CostEvent(AGENT_RESEARCH, fact_key, at=now),
        CostEvent(SOURCE_FETCH, fact_key, at=now),
        CostEvent(DETERMINISTIC_VERIFY, fact_key, at=now),
        CostEvent(CACHED_FACT_HIT, fact_key, at=now),
        CostEvent(SCHEDULED_HASHCHECK, fact_key, at=now),
    ]
