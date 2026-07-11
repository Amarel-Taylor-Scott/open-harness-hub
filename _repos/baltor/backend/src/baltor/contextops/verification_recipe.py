#!/usr/bin/env python3
"""src.baltor.contextops.verification_recipe — the M3 rung: a repeatable VERIFICATION for a fact_key.

A :class:`VerificationRecipe` (contract: ``schemas/contextops/VerificationRecipe``) turns one or more
``SourceRecipe`` ids + an ``ExtractorSnippet`` id into a deterministic, re-runnable verification. It pins —
REQUIRED — the fact_key, the input source-recipe ids, the extractor id, the deterministic validators + the
success criteria the extracted value must pass, an authority policy (which source_type may WIN; a FAQ never
wins), a cross-source confirmation policy, a freshness policy, and the tenant scope its result is valid in.

``produces`` is pinned to ``fact_verification_run``: running a recipe yields a candidate result + receipt,
NEVER a served/canonical fact. A recipe VERIFIES; reconciliation + the consumption gate decide what (if
anything) becomes a fact. The authority / cross-source / freshness policies are DERIVED deterministically from
the winning source recipe + whether the fact is a current/moving value — encoded, not hand-typed per recipe.

Determinism: ids are ``hashlib`` content hashes; ``created_at`` is an INJECTED ``now`` (never a clock read);
no RNG. Stdlib only, offline. The drafted recipe validates against VerificationRecipe.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

#: id scheme — one definition, reused for build + parse so they can never drift.
_ID_PREFIX = "vrecipe-"

#: the VerificationRecipe contract version this builder emits (single source).
SCHEMA_VERSION = "VerificationRecipe"

#: REQUIRED — running a recipe ALWAYS yields a candidate run + receipt, never a served/canonical fact.
PRODUCES = "fact_verification_run"

#: only these high-authority source types may WIN a verification — a FAQ/secondary can never be the winner.
#: Single source of the "who can win" set (mirrors VerificationRecipe authority.winning_source_type.enum).
WINNING_SOURCE_TYPES = ("source_of_law", "regulation", "statute", "official_agency", "primary_dataset")

#: default freshness horizon (seconds) — a settled value may be 30 days stale; a current value demands fresh.
_DEFAULT_MAX_STALENESS = 30 * 86400  # 30 days, in seconds — readable horizon for settled facts.
_CURRENT_MAX_STALENESS = 1 * 86400   # 1 day, in seconds — current/moving values must be fresh.

#: text cues that mean the fact is a moving/current value (kept in sync with source_recipe._CURRENT_CUES).
_CURRENT_CUES = ("current", "deadline", "rate", "fee", "today", "as of", "effective", "expires",
                 "this week", "this month", "price", "balance", "quote")

#: the deterministic validators a duration/numeric/text fact's extracted value should pass. Single source.
_DURATION_VALIDATORS = ["non_empty", "unit_check", "source_hash_match"]
_DEFAULT_VALIDATORS = ["non_empty", "type_check", "source_hash_match"]


def _hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:16]


def _is_current_value(fact_key: str) -> bool:
    fk = (fact_key or "").lower()
    return any(c in fk for c in _CURRENT_CUES)


def freshness_policy(*, fact_key: str) -> dict:
    """Derive the freshness block deterministically. A current/moving value (deadline/rate/fee/…) requires a
    fresh source read with a tight horizon; a settled value tolerates a 30-day staleness window."""
    is_current = _is_current_value(fact_key)
    return {
        "max_staleness_seconds": _CURRENT_MAX_STALENESS if is_current else _DEFAULT_MAX_STALENESS,
        "requires_fresh_for_current_values": True,
    }


def build_verification_recipe(*, tenant_id: str, source_scope: str, fact_key: str,
                              input_source_recipe_ids: list[str], extractor_id: str,
                              winning_source_type: str, min_authority_rank: int,
                              cross_source_policy: str, min_independent_sources: int,
                              validators: list[str] | None = None, success_criteria: str = "",
                              tenant_scope: str = "", watch_triggers: list[str] | None = None,
                              now: str) -> dict:
    """Build a VerificationRecipe dict (the M3 rung) for a fact_key.

    Raises ``ValueError`` if ``winning_source_type`` is not a high-authority type — a FAQ/secondary can NEVER
    be allowed to win a verification (the load-bearing authority invariant, enforced at build time, not only by
    the schema). Deterministic: same inputs + same ``now`` → byte-identical recipe (id content-addressed).
    """
    if winning_source_type not in WINNING_SOURCE_TYPES:
        raise ValueError(
            f"winning_source_type {winning_source_type!r} is not high-authority — a FAQ/secondary source can "
            f"never win a verification; allowed winners: {WINNING_SOURCE_TYPES}")

    vals = list(validators) if validators else (
        _DURATION_VALIDATORS if _is_current_value(fact_key) else _DEFAULT_VALIDATORS)
    criteria = success_criteria or (
        f"extracted value passes {vals} AND matches the winning {winning_source_type} source hash")
    scope = tenant_scope or source_scope
    triggers = list(watch_triggers) if watch_triggers else (
        ["scheduled", "source_change", "conflict_triggered"] if _is_current_value(fact_key)
        else ["source_change", "conflict_triggered"])

    identity = {"fact_key": fact_key, "extractor_id": extractor_id,
                "inputs": sorted(input_source_recipe_ids), "scope": scope}
    recipe_id = _ID_PREFIX + _hash(identity)

    return {
        "schema_version": SCHEMA_VERSION,
        "recipe_id": recipe_id,
        "tenant_id": tenant_id,
        "source_scope": source_scope,
        "fact_key": fact_key,
        "input_source_recipe_ids": list(input_source_recipe_ids),
        "extractor_id": extractor_id,
        "validators": vals,
        "success_criteria": criteria,
        "authority": {
            "min_authority_rank": min_authority_rank,
            "winning_source_type": winning_source_type,
        },
        "cross_source": {
            "policy": cross_source_policy,
            "min_independent_sources": min_independent_sources,
        },
        "freshness": freshness_policy(fact_key=fact_key),
        "watch_triggers": triggers,
        "tenant_scope": scope,
        "produces": PRODUCES,
        "created_at": now,
    }
