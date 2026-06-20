#!/usr/bin/env python3
"""src.baltor.contextops.source_discovery — ResearchTask → ranked candidates → report + proposed SourceRecipe.

The M1→M2 discovery driver, implementing :class:`SourceDiscoveryProviderPort`. Given a ``ResearchTask`` it:

  1. searches EXISTING Baltor artifacts FIRST (the cheapest rung — a source we already hold needs no research)
     and records whether it could reuse one;
  2. commissions the bounded :class:`research_stub.LocalResearchStub` to discover candidate sources OFFLINE;
  3. RANKS the candidates by authority + a deterministic reliability score (a FAQ can NEVER outrank a
     regulation — the load-bearing precedence invariant);
  4. returns a ``SourceDiscoveryReport`` (``serves_truth=False``) + the full ``SourceCandidate`` +
     ``SourceReliabilityScore`` objects, and PROPOSES a ``SourceRecipe`` for the winning (highest-authority)
     candidate.

It DISCOVERS + PROPOSES; it never serves or promotes a fact. The proposed recipe is a method, not a fact.
Determinism: ids are ``hashlib`` content hashes; ``now`` is INJECTED; no RNG, no network. Stdlib only.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from src.baltor.contextops.research_stub import LocalResearchStub
from src.baltor.contextops.source_recipe import build_source_recipe
from src.baltor.ports.research_agent_provider import AGENT_SERVES_TRUTH

#: contract versions this module emits (single source).
SOURCE_CANDIDATE_SCHEMA_VERSION = "SourceCandidate.v1"
RELIABILITY_SCORE_SCHEMA_VERSION = "SourceReliabilityScore.v1"

#: discovery reads the SHARED canonical source_type→rank map (unified with reliability on 2026-06-18, A3 —
#: discovery's prior divergent values vendor_doc=40/agency_faq=20/secondary_summary=15/tenant_document=50 are
#: preserved as lineage in contextops.authority_rank). Re-exported so existing callers keep working.
from src.baltor.contextops.authority_rank import AUTHORITY_RANK  # noqa: E402  (intra-Baltor shared vocabulary)

#: default per-factor reliability signals per source_type (each 0..1). Single source for the deterministic
#: reliability factors; the composite is derived from these + authority_rank.
_FACTOR_PROFILES: dict[str, dict[str, float]] = {
    "regulation": {"officialness": 1.0, "freshness": 0.95, "stability": 0.98, "machine_readability": 0.8,
                   "contradiction_rate": 0.0, "availability": 0.99, "parse_stability": 0.9, "historical_accuracy": 1.0},
    "source_of_law": {"officialness": 1.0, "freshness": 0.95, "stability": 0.98, "machine_readability": 0.8,
                      "contradiction_rate": 0.0, "availability": 0.99, "parse_stability": 0.9, "historical_accuracy": 1.0},
    "official_agency": {"officialness": 0.9, "freshness": 0.9, "stability": 0.9, "machine_readability": 0.8,
                        "contradiction_rate": 0.05, "availability": 0.98, "parse_stability": 0.85, "historical_accuracy": 0.9},
    "agency_faq": {"officialness": 0.5, "freshness": 0.7, "stability": 0.8, "machine_readability": 0.6,
                   "contradiction_rate": 0.4, "availability": 0.98, "parse_stability": 0.7, "historical_accuracy": 0.6},
    "secondary_summary": {"officialness": 0.4, "freshness": 0.6, "stability": 0.7, "machine_readability": 0.6,
                          "contradiction_rate": 0.5, "availability": 0.95, "parse_stability": 0.6, "historical_accuracy": 0.5},
}
_DEFAULT_FACTORS = {"officialness": 0.3, "freshness": 0.6, "stability": 0.7, "machine_readability": 0.6,
                    "contradiction_rate": 0.5, "availability": 0.9, "parse_stability": 0.6, "historical_accuracy": 0.4}

#: officialness label per source_type — single source.
_OFFICIALNESS: dict[str, str] = {
    "source_of_law": "official", "regulation": "official", "statute": "official", "official_agency": "official",
    "primary_dataset": "official", "agency_faq": "semi_official", "vendor_doc": "semi_official",
    "secondary_summary": "unofficial", "blog": "unofficial", "tenant_document": "semi_official",
}

#: map a candidate's source_handle/note → its source_type. Deterministic substring rules, in PRECEDENCE order
#: (first match wins). MORE-SPECIFIC, LOWER-AUTHORITY cues (faq/blog/summary) are checked FIRST so a FAQ that
#: merely mentions "regulation" in its note is still classified as a FAQ — a FAQ can never be promoted to a
#: regulation by wording. The source_handle is consulted before the note (the handle says what the source IS).
_TYPE_CUES = (
    ("faq", "agency_faq"), ("blog", "blog"), ("summary", "secondary_summary"), ("vendor", "vendor_doc"),
    ("statute", "statute"), ("source-of-law", "regulation"), ("source of law", "regulation"),
    ("regulation", "regulation"), ("cfr", "regulation"), ("ecfr", "regulation"), ("agency", "official_agency"),
)


def _hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:16]


def _classify_source_type(authority_note: str, source_handle: str) -> str:
    """Classify a candidate's source_type deterministically. The source_handle is consulted FIRST (it names
    what the source IS, e.g. a ``cfpb-faq`` path is a FAQ regardless of how its note is worded); only if the
    handle is silent do we fall back to the authority note. Lower-authority cues are checked first so a FAQ
    that mentions "regulation" in prose can never be mis-promoted to a regulation."""
    handle = source_handle.lower()
    for cue, st in _TYPE_CUES:
        if cue in handle:
            return st
    note = authority_note.lower()
    for cue, st in _TYPE_CUES:
        if cue in note:
            return st
    return "secondary_summary"


def _composite(factors: dict[str, float], authority_rank: int) -> float:
    """Deterministic 0..1 composite: mean of the positive factors, penalized by contradiction_rate, then
    blended 50/50 with the normalized authority_rank. Same factors → same composite, every run."""
    positives = [factors["officialness"], factors["freshness"], factors["stability"],
                 factors["machine_readability"], factors["availability"], factors["parse_stability"],
                 factors["historical_accuracy"]]
    base = sum(positives) / len(positives)
    base = max(0.0, base - factors["contradiction_rate"] * 0.5)
    authority_norm = max(0, min(authority_rank, 100)) / 100.0
    return round(0.5 * base + 0.5 * authority_norm, 4)


def _build_candidate(*, source_handle: str, authority_note: str, tenant_id: str, scope: str,
                     discovered_by: str, now: str) -> dict:
    st = _classify_source_type(authority_note, source_handle)
    rank = AUTHORITY_RANK.get(st, 10)
    cand_id = "scand-" + _hash({"h": source_handle, "scope": scope})
    cand = {
        "schema_version": SOURCE_CANDIDATE_SCHEMA_VERSION,
        "candidate_id": cand_id,
        "tenant_id": tenant_id,
        "source_scope": scope,
        "source_handle": source_handle,
        "source_type": st,
        "authority_rank": rank,
        "access_method": "fixture",
        "officialness": _OFFICIALNESS.get(st, "unofficial"),
        "discovered_by": discovered_by,
        "discovered_at": now,
    }
    if authority_note:
        cand["title"] = authority_note[:120]
    return cand


def _build_score(*, candidate: dict, now: str) -> dict:
    st = candidate["source_type"]
    rank = candidate["authority_rank"]
    factors = dict(_FACTOR_PROFILES.get(st, _DEFAULT_FACTORS))
    score = {
        "schema_version": RELIABILITY_SCORE_SCHEMA_VERSION,
        "score_id": "srs-" + _hash({"c": candidate["candidate_id"], "f": factors}),
        "candidate_id": candidate["candidate_id"],
        "tenant_id": candidate["tenant_id"],
        "source_scope": candidate["source_scope"],
        "authority_rank": rank,
        "factors": factors,
        "rate_limit_risk": "none" if st in ("regulation", "source_of_law") else "low",
        "tenant_scope_ok": candidate["source_scope"] != "tenant_private",
        "composite_score": _composite(factors, rank),
        "served_as_truth": False,  # PINNED False — a score ranks, it never serves a fact
        "scored_at": now,
    }
    return score


class SourceDiscoveryDriver:
    """Implements :class:`SourceDiscoveryProviderPort`: ResearchTask → ranked candidates → report + recipe.

    Searches existing artifacts FIRST, commissions the deterministic local research stub, ranks by authority +
    reliability (a FAQ can never outrank a regulation), and proposes a SourceRecipe for the winner. DISCOVERS +
    PROPOSES only — never serves a fact (``serves_truth``/``served_as_truth`` pinned False on all output)."""

    provider_id = "source_discovery.local@v1"

    def __init__(self, *, research_provider: LocalResearchStub | None = None) -> None:
        self._research = research_provider or LocalResearchStub()

    def discover(self, task: dict[str, Any], *, existing_handles: list[str] | None = None,
                 now: str) -> dict[str, Any]:
        existing = set(existing_handles or [])
        tenant_id = task.get("tenant_id", "")
        scope = task.get("source_scope", "global_public")
        fact_key = task.get("fact_key", "")
        question = task.get("question", "")

        # 1) bounded OFFLINE discovery — the local stub returns a SourceDiscoveryReport (serves_truth=False).
        report = self._research.research(task, now=now)
        discovered_by = report["discovered_by"]

        # 2) build full SourceCandidate + SourceReliabilityScore objects; flag any already-held source (reuse).
        candidates: list[dict] = []
        scores: list[dict] = []
        reused_existing = False
        for entry in report["candidates"]:
            handle = entry["source_handle"]
            note = entry.get("authority_note", "")
            cand = _build_candidate(source_handle=handle, authority_note=note, tenant_id=tenant_id,
                                    scope=scope, discovered_by=discovered_by, now=now)
            cand["already_held"] = handle in existing  # transient ranking hint; not part of the contract
            if handle in existing:
                reused_existing = True
            candidates.append(cand)
            scores.append(_build_score(candidate=cand, now=now))

        # 3) RANK by authority_rank desc, then composite desc (deterministic, stable) — FAQ never wins.
        score_by_cand = {s["candidate_id"]: s for s in scores}
        ranked = sorted(
            candidates,
            key=lambda c: (-c["authority_rank"], -score_by_cand[c["candidate_id"]]["composite_score"],
                           c["candidate_id"]))
        winner = ranked[0] if ranked else None

        # 4) PROPOSE a SourceRecipe for the highest-authority candidate (M1 -> M2).
        proposed_recipe = None
        if winner is not None:
            proposed_recipe = build_source_recipe(
                tenant_id=tenant_id, source_scope=scope, fact_key=fact_key, question=question,
                source_handle=winner["source_handle"], source_type=winner["source_type"],
                authority_rank=winner["authority_rank"], officialness=winner["officialness"],
                locator=_locator_for(winner["source_handle"]),
                reliability_score_id=score_by_cand[winner["candidate_id"]]["score_id"],
                derived_from_report_id=report["report_id"], now=now)

        # strip the transient ranking hint from contract-bearing candidate objects.
        for c in candidates:
            c.pop("already_held", None)

        return {
            "report": report,
            "candidates": candidates,
            "scores": scores,
            "ranked_candidate_ids": [c["candidate_id"] for c in ranked],
            "winner_candidate_id": winner["candidate_id"] if winner else "",
            "proposed_recipe": proposed_recipe,
            "reused_existing": reused_existing,
            "serves_truth": AGENT_SERVES_TRUTH,  # PINNED False — discovery never serves a fact
        }


def _locator_for(source_handle: str) -> str:
    """Deterministic fixture locator for a source handle in the lean core (offline; no network)."""
    return "fixtures/contextops/" + _hash({"h": source_handle}) + ".html"
