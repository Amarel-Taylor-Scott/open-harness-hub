#!/usr/bin/env python3
"""facts/classifier — a DETERMINISTIC fragility classifier (no model, no clock, no RNG).

Given a fact's claim_type, source authority, and claim text, it picks a ``volatility_class`` from rules over
text cues ('current', 'deadline', 'rate', 'fee', 'today', 'as of', 'effective', …) + authority, recommends a
``WatchPolicy`` (refresh cadence / no_refresh / escalate-on-conflict), and emits ``FragilityMetadata`` carrying
``last_verified_at`` + a horizon (``next_verify_at`` from the policy) + ``watch_policy_id``. Same inputs →
identical output, every run. Time is INJECTED (``last_verified_at``).

The classifier is the only place the cue→volatility→cadence mapping lives (single source of truth); the planner
and the gate read what it produces.
"""
from __future__ import annotations

from src.baltor.contracts.artifacts.fragility_metadata import FragilityMetadata
from src.baltor.contracts.artifacts.watch_policy import WatchPolicy

DAY = 86400  # seconds in a day — refresh cadences are expressed in days for readability.

#: refresh cadence (seconds) per volatility class. Single source for the watch cadence.
CADENCE_SECONDS = {
    "stable": 0,            # never expires (paired with no_refresh)
    "low": 365 * DAY,       # yearly re-check (settled-ish but not immutable)
    "medium": 30 * DAY,     # monthly (FAQs, summaries, conflict-prone derived facts)
    "high": 7 * DAY,        # weekly (deadlines, rates, fees that move)
    "realtime": 1 * DAY,    # daily (volatile public facts)
}

#: text cues that push a fact UP the volatility scale (lowercased substring match — deterministic).
_HIGH_CUES = ("current", "deadline", "rate", "fee", "today", "as of", "effective", "expires",
              "this week", "this month", "price", "balance", "quote")
_MEDIUM_CUES = ("summary", "faq", "approximately", "around", "estimate", "typically", "may", "generally")

#: source authorities that are IMMUTABLE within the demo / settled-law sense → no_refresh.
_IMMUTABLE_AUTHORITIES = ("demo-fixture", "immutable", "settled-law-constant", "system-reference")
#: high-authority sources of law — durable, lower volatility unless the TEXT says otherwise.
_LAW_AUTHORITIES = ("source-of-law", "regulation", "statute")
#: lower-authority summaries — conflict-prone, medium-to-high volatility.
_SUMMARY_AUTHORITIES = ("agency-faq", "faq", "vendor-doc", "blog", "summary")


def _has_cue(text: str, cues) -> bool:
    t = (text or "").lower()
    return any(c in t for c in cues)


def classify_volatility(*, claim_type: str, source_authority: str, claim_text: str) -> tuple:
    """Return (volatility_class, no_refresh, conflict_prone, decay_signal). Pure + deterministic."""
    auth = (source_authority or "").lower()

    # immutable demo / settled-law constants never refresh.
    if any(a in auth for a in _IMMUTABLE_AUTHORITIES):
        return ("stable", True, False, "immutable_source")

    # derived/interpreted claim-shapes (conclusion / emotion) are inherently conflict-prone & perishable.
    if claim_type in ("conclusion", "emotion_signal"):
        return ("medium", False, True, "derived_interpretation")

    has_high = _has_cue(claim_text, _HIGH_CUES)
    is_summary = any(a in auth for a in _SUMMARY_AUTHORITIES)
    is_law = any(a in auth for a in _LAW_AUTHORITIES)

    # a summary/FAQ that restates a moving fact is conflict-prone medium-to-high.
    if is_summary:
        vc = "high" if has_high else "medium"
        return (vc, False, True, "lower_authority_summary")

    # a source-of-law deadline/rate still moves (amendments) — high; otherwise durable (low).
    if is_law:
        return ("high", False, False, "regulatory_value_change") if has_high else ("low", False, False, "settled_law")

    # default: cue-driven.
    if has_high:
        return ("high", False, False, "value_cue")
    if _has_cue(claim_text, _MEDIUM_CUES):
        return ("medium", False, True, "soft_cue")
    return ("low", False, False, "no_strong_cue")


def recommend_watch_policy(*, claim_type: str, source_authority: str, claim_text: str) -> WatchPolicy:
    """Pick the WatchPolicy a fact of this shape should be watched under (deterministic)."""
    vc, no_refresh, conflict_prone, _ = classify_volatility(
        claim_type=claim_type, source_authority=source_authority, claim_text=claim_text)
    if no_refresh:
        return WatchPolicy(name="immutable_no_refresh", volatility_class=vc, refresh_interval_seconds=0,
                           no_refresh=True, escalate_on_conflict=False)
    return WatchPolicy(name=f"watch_{vc}", volatility_class=vc,
                       refresh_interval_seconds=CADENCE_SECONDS[vc],
                       no_refresh=False, escalate_on_conflict=conflict_prone,
                       max_staleness_seconds=CADENCE_SECONDS[vc] * 2)


def classify(*, fact_id: str, claim_type: str, source_authority: str, claim_text: str,
             last_verified_at: int) -> tuple:
    """Return (FragilityMetadata, WatchPolicy) for a fact. ``last_verified_at`` is INJECTED (no clock)."""
    vc, no_refresh, conflict_prone, decay = classify_volatility(
        claim_type=claim_type, source_authority=source_authority, claim_text=claim_text)
    policy = recommend_watch_policy(
        claim_type=claim_type, source_authority=source_authority, claim_text=claim_text)
    nva = policy.next_verify_at(last_verified_at)  # None when no_refresh
    frag = FragilityMetadata(
        fact_id=fact_id, volatility_class=vc, last_verified_at=last_verified_at,
        watch_policy_id=policy.watch_policy_id, next_verify_at=nva, ttl_seconds=None,
        no_refresh=no_refresh, conflict_prone=conflict_prone, decay_signal=decay)
    return frag, policy
