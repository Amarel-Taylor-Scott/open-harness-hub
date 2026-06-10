#!/usr/bin/env python3
"""contextops/triage — the ContextTriageClassifier: DETECTION, the first stage of the ContextOps loop.

Given one piece of context (a ``fact_key`` + the ``claim_text`` + the source it came from: ``source_type`` /
``authority_rank`` / ``source_scope`` / freshness) it decides, with DETERMINISTIC rules (no model, no clock,
no RNG), which of the twelve ContextTriage lanes apply, picks a single PRIMARY ``lane`` for the v1 contract,
and sets ``needs_action`` so MAIN / a bounded research agent can commission downstream work.

THE INVARIANT, structurally: a triage is a routing signal, NEVER a served fact. ``serves_truth`` is pinned
``False`` on every result; the classifier never promotes anything, never overrides reconciliation, never
decides truth — it only routes. It maps a lane to a *recommended* ``contextops.*`` command; agents/MAIN
decide whether to run it.

The twelve lanes (single source — must equal ``ContextTriageResult.v1.schema.json``'s ``lane`` enum and
``scripts/check_contextops_contracts.py``'s ``_TRIAGE_LANES``):

  needs_reconciliation · needs_verification · needs_enrichment · is_fragile · is_stale · is_low_authority ·
  is_under_supported · is_conflict_candidate · is_missing_source · is_customer_private_override ·
  is_model_interpretation · is_high_value_reusable_fact

Load-bearing deterministic rules (the spec):

  * a ``narrative_allegation`` can NOT become a verified fact without a stronger source → needs_verification +
    is_under_supported (it is an allegation, not corroborated truth).
  * a ``model_interpretation`` REQUIRES source support → is_model_interpretation + is_under_supported (and
    needs_verification) unless it carries a real source handle + a source-of-law authority.
  * current / rate / fee / deadline claims → is_fragile (their value moves; they decay).
  * FAQ / guidance authority < source-of-law authority → is_low_authority.
  * tenant_private context stays tenant-scoped → is_customer_private_override (the triage never widens it to
    global).
  * the CFPB reference case — a FAQ "30 days" vs a Reg-E "10 business days" — classifies as
    needs_reconciliation + is_low_authority + is_conflict_candidate.

Determinism: ``triage_id`` is a ``hashlib`` content hash over (fact_key, primary lane, source_scope); time
is INJECTED (``triaged_at``); no clock, no RNG. Stdlib only, fully offline.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

# ── the schema version this result conforms to (single source — equals the contract $id stem) ──────────
SCHEMA_VERSION = "ContextTriageResult.v1"

# ── the twelve ContextTriage lanes (single source of the taxonomy). MUST match the contract enum. ──────
NEEDS_RECONCILIATION = "needs_reconciliation"
NEEDS_VERIFICATION = "needs_verification"
NEEDS_ENRICHMENT = "needs_enrichment"
IS_FRAGILE = "is_fragile"
IS_STALE = "is_stale"
IS_LOW_AUTHORITY = "is_low_authority"
IS_UNDER_SUPPORTED = "is_under_supported"
IS_CONFLICT_CANDIDATE = "is_conflict_candidate"
IS_MISSING_SOURCE = "is_missing_source"
IS_CUSTOMER_PRIVATE_OVERRIDE = "is_customer_private_override"
IS_MODEL_INTERPRETATION = "is_model_interpretation"
IS_HIGH_VALUE_REUSABLE_FACT = "is_high_value_reusable_fact"

#: ordered so the PRIMARY lane is the highest-priority fired lane (most-action-warranting first). A context
#: missing its source must be flagged before anything else; a private override is sticky; reconciliation
#: outranks plain verification; an enrichment hint is the gentlest signal; a clean reusable fact is last.
TRIAGE_LANES: tuple[str, ...] = (
    IS_MISSING_SOURCE,
    IS_CUSTOMER_PRIVATE_OVERRIDE,
    NEEDS_RECONCILIATION,
    IS_CONFLICT_CANDIDATE,
    IS_MODEL_INTERPRETATION,
    IS_UNDER_SUPPORTED,
    NEEDS_VERIFICATION,
    IS_FRAGILE,
    IS_STALE,
    IS_LOW_AUTHORITY,
    NEEDS_ENRICHMENT,
    IS_HIGH_VALUE_REUSABLE_FACT,
)

#: lanes that, when fired, mean a bounded research / verification / reconciliation pass is warranted.
#: is_high_value_reusable_fact is the ONLY lane that, on its own, means "fine as-is" (needs_action=False).
_ACTION_LANES = frozenset(TRIAGE_LANES) - {IS_HIGH_VALUE_REUSABLE_FACT}

#: claim shapes the classifier knows about (single source). A model interpretation needs source support; an
#: allegation is not verified truth; an atomic fact is the corroboration-bearing shape.
CLAIM_NARRATIVE_ALLEGATION = "narrative_allegation"
CLAIM_MODEL_INTERPRETATION = "model_interpretation"
CLAIM_ATOMIC_FACT = "atomic_fact"

#: source scopes (single source — equals the contract's source_scope enum). tenant_private stays scoped.
SCOPE_GLOBAL_PUBLIC = "global_public"
SCOPE_TENANT_PRIVATE = "tenant_private"
SCOPE_TENANT_SHARED = "tenant_shared"
SCOPE_SYSTEM_REFERENCE = "system_reference"
_SCOPES = (SCOPE_GLOBAL_PUBLIC, SCOPE_TENANT_PRIVATE, SCOPE_TENANT_SHARED, SCOPE_SYSTEM_REFERENCE)

#: text cues that mark a claim's VALUE as moving (fragile). Reused philosophy from facts/classifier; kept
#: local so triage stays a self-contained detection unit. Lowercased substring match — deterministic.
_FRAGILE_CUES = ("current", "deadline", "rate", "fee", "today", "as of", "effective", "expires",
                 "this week", "this month", "price", "balance", "quote", "days", "business day")

#: source types whose authority is BELOW a source of law (a FAQ / guidance can never outrank a regulation).
_LOW_AUTHORITY_TYPES = ("agency_faq", "faq", "guidance", "vendor_doc", "blog", "secondary_summary",
                        "summary", "help_center")
#: source types that ARE the authoritative source of law / official record.
_SOURCE_OF_LAW_TYPES = ("source_of_law", "regulation", "statute", "ecfr", "official_record", "code_of_law")

#: authority_rank below this is treated as low-authority when no explicit source_type is given. The contract
#: example uses 20 for a FAQ and 90 for a regulation, so a midpoint cleanly separates the two.
LOW_AUTHORITY_RANK_CEILING = 50  # ranks ≤ this are low authority (FAQ-tier); above is source-of-law-tier.

#: when a same-fact_key conflicting value is supplied, the triage is a conflict + reconciliation candidate.
#: (Full graph-wide conflict detection lives in scripts/artifact_graph/conflict_detector.py; triage only
#: detects the SINGLE-context signal — "this claim contradicts a value I was handed for the same fact_key".)

# id scheme — one definition, reused so build can never drift from the documented shape.
_ID_PREFIX = "triage-"


def _canon(body: object) -> bytes:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _has_cue(text: str, cues) -> bool:
    t = (text or "").lower()
    return any(c in t for c in cues)


def make_triage_id(fact_key: str, lane: str, source_scope: str) -> str:
    """Content-addressed triage id over (fact_key, primary lane, source_scope). Version lives in metadata,
    never in the id; same logical triage → byte-stable id across runs (no clock in the hashed body)."""
    h = hashlib.sha256(_canon({"fact_key": fact_key, "lane": lane, "scope": source_scope})).hexdigest()
    return f"{_ID_PREFIX}{h[:16]}"


# recommended downstream command per primary lane (a recommendation only — triage never executes).
_LANE_COMMAND = {
    NEEDS_RECONCILIATION: "contextops.research",
    IS_CONFLICT_CANDIDATE: "contextops.confirm_cross_source",
    NEEDS_VERIFICATION: "contextops.run_verification",
    IS_MODEL_INTERPRETATION: "contextops.research",
    IS_UNDER_SUPPORTED: "contextops.research",
    IS_MISSING_SOURCE: "contextops.research",
    IS_FRAGILE: "contextops.schedule_watch",
    IS_STALE: "contextops.run_verification",
    IS_LOW_AUTHORITY: "contextops.research",
    NEEDS_ENRICHMENT: "contextops.research",
    IS_CUSTOMER_PRIVATE_OVERRIDE: "contextops.run_verification",
    IS_HIGH_VALUE_REUSABLE_FACT: "none",
}


@dataclass(frozen=True)
class ContextTriageResult:
    """The output of one triage: which lanes fired, the single primary ``lane`` (the contract field), whether
    action is warranted, and the recommended downstream command. ``serves_truth`` is ALWAYS False — a triage
    is a routing signal, never a served fact. ``to_dict()`` conforms to ``ContextTriageResult.v1``.

    ``lanes`` is the full multi-label set (deterministic, sorted); ``lane`` is the single highest-priority
    fired lane carried in the v1 contract. ``triaged_at`` is INJECTED (no wall-clock)."""
    triage_id: str
    tenant_id: str
    source_scope: str
    fact_key: str
    lane: str                       # the single PRIMARY lane (the v1 contract field)
    lanes: tuple[str, ...]          # the FULL multi-label set of fired lanes (sorted, deterministic)
    needs_action: bool
    rationale: str
    triaged_at: str
    claim_text: str = ""
    source_handle: str = ""
    authority_rank: int | None = None
    fragility_signal: str = ""
    recommended_command: str = "none"
    serves_truth: bool = False      # PINNED False — a triage can NEVER be served as a fact.
    schema_version: str = SCHEMA_VERSION

    def fired(self, lane: str) -> bool:
        """True iff ``lane`` is one of the lanes this triage fired (multi-label membership test)."""
        return lane in self.lanes

    def to_dict(self) -> dict:
        """The v1-contract-shaped dict (omits the multi-label ``lanes`` helper, which is not a v1 field).

        Conforms to ``schemas/contextops/ContextTriageResult.v1.schema.json``: required keys present,
        ``serves_truth`` pinned False, ``lane`` one of the twelve, ``triaged_at`` the injected time."""
        d: dict = {
            "schema_version": self.schema_version,
            "triage_id": self.triage_id,
            "tenant_id": self.tenant_id,
            "source_scope": self.source_scope,
            "fact_key": self.fact_key,
            "lane": self.lane,
            "needs_action": self.needs_action,
            "rationale": self.rationale,
            "serves_truth": self.serves_truth,
            "triaged_at": self.triaged_at,
            "recommended_command": self.recommended_command,
        }
        if self.claim_text:
            d["claim_text"] = self.claim_text
        if self.source_handle:
            d["source_handle"] = self.source_handle
        if self.authority_rank is not None:
            d["authority_rank"] = self.authority_rank
        if self.fragility_signal:
            d["fragility_signal"] = self.fragility_signal
        return d


class ContextTriageClassifier:
    """DETERMINISTIC ContextTriage classifier — the detection front end of the ContextOps loop.

    No model, no clock, no RNG: identical inputs yield byte-identical results every run. It detects which of
    the twelve lanes apply, never serves/promotes/decides truth. ``now`` is INJECTED on every call."""

    def _is_low_authority(self, source_type: str, authority_rank: int | None) -> bool:
        st = (source_type or "").lower()
        if any(t in st for t in _SOURCE_OF_LAW_TYPES):
            return False
        if any(t in st for t in _LOW_AUTHORITY_TYPES):
            return True
        if authority_rank is not None:
            return authority_rank <= LOW_AUTHORITY_RANK_CEILING
        return False

    def _is_source_of_law(self, source_type: str, authority_rank: int | None) -> bool:
        st = (source_type or "").lower()
        if any(t in st for t in _SOURCE_OF_LAW_TYPES):
            return True
        if any(t in st for t in _LOW_AUTHORITY_TYPES):
            return False
        if authority_rank is not None:
            return authority_rank > LOW_AUTHORITY_RANK_CEILING
        return False

    def classify(
        self,
        *,
        fact_key: str,
        tenant_id: str = "",
        claim_text: str = "",
        claim_type: str = CLAIM_ATOMIC_FACT,
        source_type: str = "",
        source_handle: str = "",
        source_scope: str = SCOPE_GLOBAL_PUBLIC,
        authority_rank: int | None = None,
        last_verified_at: int | None = None,
        max_staleness_seconds: int | None = None,
        conflicts_with_value: bool = False,
        is_high_value: bool = False,
        enrichment_hint: bool = False,
        now: str = "1970-01-01T00:00:00Z",
        now_epoch: int | None = None,
    ) -> ContextTriageResult:
        """Triage one piece of context into the twelve lanes (deterministic).

        ``conflicts_with_value`` is the single-context conflict signal — "this claim contradicts a value I
        was handed for the same fact_key" (graph-wide conflict detection is a separate detector). ``now`` is
        the injected ISO stamp recorded on the result; ``now_epoch`` (injected epoch seconds) is used ONLY
        for the staleness comparison against ``last_verified_at`` + ``max_staleness_seconds``. No clock read.
        """
        if not fact_key:
            raise ValueError("fact_key is required (the context the triage is about)")
        if source_scope not in _SCOPES:
            raise ValueError(f"source_scope must be one of {_SCOPES}, got {source_scope!r}")

        fired: set[str] = set()
        reasons: list[str] = []
        fragility_signal = ""
        ct = (claim_type or "").lower()

        low_auth = self._is_low_authority(source_type, authority_rank)
        is_law = self._is_source_of_law(source_type, authority_rank)
        has_handle = bool(source_handle)

        # 1) missing source — a claim with no source handle is inadmissible until one is found.
        if not has_handle:
            fired.add(IS_MISSING_SOURCE)
            fired.add(NEEDS_VERIFICATION)
            reasons.append("no source_handle — context is unattributed and cannot be verified as-is")

        # 2) tenant_private context stays tenant-scoped — a private override never widens to global.
        if source_scope == SCOPE_TENANT_PRIVATE:
            fired.add(IS_CUSTOMER_PRIVATE_OVERRIDE)
            reasons.append("tenant_private scope — this context stays tenant-scoped, never widened to global")

        # 3) a narrative_allegation can NOT become a verified fact without a stronger source.
        if ct == CLAIM_NARRATIVE_ALLEGATION:
            fired.add(IS_UNDER_SUPPORTED)
            fired.add(NEEDS_VERIFICATION)
            reasons.append("narrative_allegation — an allegation is not verified truth without a stronger source")

        # 4) a model_interpretation REQUIRES source support.
        if ct == CLAIM_MODEL_INTERPRETATION:
            fired.add(IS_MODEL_INTERPRETATION)
            if not (has_handle and is_law):
                fired.add(IS_UNDER_SUPPORTED)
                fired.add(NEEDS_VERIFICATION)
                reasons.append("model_interpretation lacks a high-authority source handle — requires source support")
            else:
                reasons.append("model_interpretation carries a source-of-law handle — supported")

        # 5) current / rate / fee / deadline (value-moving) claims are fragile.
        if _has_cue(claim_text, _FRAGILE_CUES):
            fired.add(IS_FRAGILE)
            for cue in _FRAGILE_CUES:
                if cue in (claim_text or "").lower():
                    fragility_signal = cue
                    break
            reasons.append(f"value-moving cue ({fragility_signal!r}) — this claim decays; it is fragile")

        # 6) FAQ / guidance authority < source-of-law authority.
        if low_auth:
            fired.add(IS_LOW_AUTHORITY)
            reasons.append("source authority is below a source of law (FAQ/guidance) — lower authority")

        # 7) single-context conflict — this claim contradicts a value for the SAME fact_key.
        if conflicts_with_value:
            fired.add(IS_CONFLICT_CANDIDATE)
            fired.add(NEEDS_RECONCILIATION)
            reasons.append("claim contradicts another value for the same fact_key — conflict + reconciliation candidate")

        # 8) a low-authority claim that contradicts a higher source must be reconciled (the CFPB reference case:
        #    a FAQ that conflicts with the source of law is needs_reconciliation + is_low_authority +
        #    is_conflict_candidate).
        if low_auth and conflicts_with_value:
            fired.add(NEEDS_RECONCILIATION)

        # 9) staleness — past its max-staleness horizon (injected epoch comparison; no clock read).
        if (
            last_verified_at is not None
            and max_staleness_seconds is not None
            and now_epoch is not None
            and now_epoch - last_verified_at > max_staleness_seconds
        ):
            fired.add(IS_STALE)
            fired.add(NEEDS_VERIFICATION)
            reasons.append("past its max-staleness horizon — context is stale and must be re-verified")

        # 10) enrichment — an explicit hint that this context is thin and could be enriched (additive).
        if enrichment_hint:
            fired.add(NEEDS_ENRICHMENT)
            reasons.append("flagged thin — could be enriched with additional supporting context")

        # 11) high-value reusable fact — a well-supported, high-authority, non-fragile, non-conflicting fact.
        clean = (
            is_high_value
            and has_handle
            and is_law
            and not _has_cue(claim_text, _FRAGILE_CUES)
            and not conflicts_with_value
            and IS_STALE not in fired
            and ct == CLAIM_ATOMIC_FACT
        )
        if clean:
            fired.add(IS_HIGH_VALUE_REUSABLE_FACT)
            reasons.append("high-authority, source-grounded, non-fragile, non-conflicting — reusable canonical input")

        # nothing fired → it still resolved to a verification need (a default-safe routing, never "served").
        if not fired:
            fired.add(NEEDS_VERIFICATION)
            reasons.append("no strong signal — default to a lightweight verification pass")

        # primary lane = the highest-priority fired lane (TRIAGE_LANES order).
        primary = next(lane for lane in TRIAGE_LANES if lane in fired)
        needs_action = bool(fired & _ACTION_LANES)
        triage_id = make_triage_id(fact_key, primary, source_scope)

        return ContextTriageResult(
            triage_id=triage_id,
            tenant_id=tenant_id,
            source_scope=source_scope,
            fact_key=fact_key,
            lane=primary,
            lanes=tuple(sorted(fired)),
            needs_action=needs_action,
            rationale="; ".join(reasons),
            triaged_at=now,
            claim_text=claim_text,
            source_handle=source_handle,
            authority_rank=authority_rank,
            fragility_signal=fragility_signal,
            recommended_command=_LANE_COMMAND.get(primary, "none"),
            serves_truth=False,
            schema_version=SCHEMA_VERSION,
        )
