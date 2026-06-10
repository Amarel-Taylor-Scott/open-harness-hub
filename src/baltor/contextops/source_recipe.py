#!/usr/bin/env python3
"""src.baltor.contextops.source_recipe — the M2 rung: distill a discovered source into a REUSABLE recipe.

A :class:`SourceRecipe` (contract: ``schemas/contextops/SourceRecipe.v1``) is the deterministic, reusable
"how to reach + read this authoritative source" distilled from an M1 ``SourceDiscoveryReport`` so the same
source never has to be re-researched by an LLM. It encodes — REQUIRED — the source's authority (so
reconciliation precedence is checkable, source-of-law > FAQ), the access method (http_get/api/file/fixture)
with a retry + rate-limit policy, the cross-source confirmation policy, watch triggers (when it must re-run),
the paired parser provider, the expected output schema, and a reliability-score back-link.

A recipe is a METHOD, never a fact: it tells an extractor WHERE to look; the extractor's output is still only
a ``fact_assertion_candidate``. The watch triggers + cross-source policy are DERIVED deterministically from the
source's authority/officialness + the fact's volatility — current/rate/fee/deadline facts demand a fresh read.

Determinism: ids are ``hashlib`` content hashes; ``created_at`` is an INJECTED ``now`` (never a clock read);
no RNG. Stdlib only, offline. The drafted recipe validates against SourceRecipe.v1.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

#: id scheme — one definition, reused for build + parse so build/parse can never drift.
_ID_PREFIX = "srecipe-"

#: the SourceRecipe contract version this builder emits (single source — never literal'd elsewhere).
SCHEMA_VERSION = "SourceRecipe.v1"

#: REQUIRED — the recipe ALWAYS targets a candidate fact, read into a candidate (never a served/canonical) value.
EXPECTED_OUTPUT_SCHEMA = "fact_assertion_candidate"

#: default access method in the lean core — fixtures back the correctness invariant (offline, deterministic).
DEFAULT_ACCESS_METHOD = "fixture"

#: cross-source policy per source authority. Single source for the M2 cross-source-policy mapping.
#: an official source-of-record can stand alone; a restatement (FAQ/secondary) needs corroboration; a
#: tenant_private source needs human signoff before it backs anything.
_OFFICIAL_TYPES = ("source_of_law", "regulation", "statute", "official_agency", "primary_dataset")
_SECONDARY_TYPES = ("agency_faq", "vendor_doc", "secondary_summary", "blog")

#: text cues that mean the fact is a moving/current value → it requires a fresh read (current_value policy /
#: source_change watch). Mirrors facts.classifier's high-volatility cues (kept narrow + deterministic).
_CURRENT_CUES = ("current", "deadline", "rate", "fee", "today", "as of", "effective", "expires",
                 "this week", "this month", "price", "balance", "quote")


def _hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:16]


def _is_current_value(fact_key: str, question: str) -> bool:
    blob = f"{fact_key} {question}".lower()
    return any(c in blob for c in _CURRENT_CUES)


def cross_source_policy(*, source_type: str, source_scope: str, is_current_value: bool) -> tuple[str, int]:
    """Derive (policy, min_independent_sources) for a source of this type/scope deterministically.

    tenant_private → human signoff (1). official source-of-record → single source ok (1) unless the fact is a
    current/moving value → fresh-source-required (still 1 official). secondary/restatement → two independent
    sources required (2). Single source of the M2 cross-source mapping; reconciliation reads what this emits.
    """
    if source_scope == "tenant_private":
        return ("tenant_private_requires_human_signoff", 1)
    if source_type in _OFFICIAL_TYPES:
        if is_current_value:
            return ("current_value_requires_fresh_source", 1)
        return ("single_official_source_ok", 1)
    # a restatement / lower-authority source can never stand alone — demand independent corroboration.
    return ("two_independent_sources_required", 2)


def watch_triggers(*, source_type: str, is_current_value: bool) -> list[str]:
    """Derive the watch triggers (when the recipe must re-run) deterministically. Always includes
    ``source_change`` (the source may move) + ``conflict_triggered`` (re-check when reconciliation flags a
    conflict). A current/moving value adds ``scheduled`` + ``high_value_periodic``."""
    triggers = ["source_change", "conflict_triggered"]
    if is_current_value:
        triggers = ["scheduled", "source_change", "conflict_triggered", "high_value_periodic"]
    return triggers


def build_source_recipe(*, tenant_id: str, source_scope: str, fact_key: str, question: str,
                        source_handle: str, source_type: str, authority_rank: int, officialness: str,
                        access_method: str = DEFAULT_ACCESS_METHOD, locator: str,
                        parser_provider: str = "parser.stub@v1", reliability_score_id: str = "",
                        derived_from_report_id: str = "", rate_limit_per_min: int = 30, now: str) -> dict:
    """Distil one discovered, authority-ranked source into a SourceRecipe.v1 dict (the M2 rung).

    The cross_source policy + watch triggers + retry policy are DERIVED from the source's authority/type +
    whether the fact is a current/moving value — they are encoded, not hand-typed per recipe. Deterministic:
    same inputs + same ``now`` → byte-identical recipe (the id is content-addressed over the identity fields).
    """
    is_current = _is_current_value(fact_key, question)
    policy, min_sources = cross_source_policy(
        source_type=source_type, source_scope=source_scope, is_current_value=is_current)
    triggers = watch_triggers(source_type=source_type, is_current_value=is_current)
    # an official source can retry harder; a flaky restatement uses fixed backoff.
    retry = "exponential_backoff" if source_type in _OFFICIAL_TYPES else "fixed_backoff"

    identity = {"source_handle": source_handle, "fact_key": fact_key, "method": access_method,
                "locator": locator, "scope": source_scope}
    recipe_id = _ID_PREFIX + _hash(identity)

    recipe: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "recipe_id": recipe_id,
        "tenant_id": tenant_id,
        "source_scope": source_scope,
        "fact_key": fact_key,
        "source_handle": source_handle,
        "authority": {
            "source_type": source_type,
            "authority_rank": authority_rank,
            "officialness": officialness,
        },
        "access": {
            "method": access_method,
            "locator": locator,
            "retry_policy": retry,
            "rate_limit_per_min": rate_limit_per_min,
        },
        "cross_source": {
            "policy": policy,
            "min_independent_sources": min_sources,
        },
        "watch_triggers": triggers,
        "parser_provider": parser_provider,
        "expected_output_schema": EXPECTED_OUTPUT_SCHEMA,
        "created_at": now,
    }
    if derived_from_report_id:
        recipe["derived_from_report_id"] = derived_from_report_id
    if reliability_score_id:
        recipe["reliability_score_id"] = reliability_score_id
    return recipe
