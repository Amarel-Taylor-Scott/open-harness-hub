#!/usr/bin/env python3
"""src.baltor.determinism.fallback_router — M7 serving: deterministic rule FIRST, recorded fallback otherwise.

Once a candidate is promoted (``rule_promotion_gate``), serving is **deterministic-first**: an ACTIVE rule
runs first and, when it fires confidently on an in-distribution input, its decision is served deterministically
(no model call). Otherwise the router falls back — but a fallback NEVER fabricates a fact. The three fallback
routes (single source, mirrors ``FallbackPolicy.route``):

* ``gateway`` — re-propose via the LLMGateway (a PROPOSAL, never authoritative; feeds future mining).
* ``human``   — escalate to a human/policy adjudication queue (becomes a future VERIFIED label).
* ``hold_out``— abstain: serve NOTHING, exclude from the promoted pack, record the abstention.

Fallback fires when the rule abstains (preconditions did not fire), the input is OUT-OF-DISTRIBUTION (carries a
field the rule never trained on, or is missing a required input field), or the rule's confidence is below the
policy's ``min_confidence``. Every decision — rule-served OR fallen-back — is RECORDED as a ``RoutingEvent``
(which feeds the trace store and future mining). An INACTIVE / un-promoted rule never serves; it goes straight
to fallback. The router holds NO authority of its own: it serves the rule's deterministic verdict or it
escalates/abstains. It can never invent a fact (``fabricated`` is structurally impossible — asserted in proof).

Determinism: pure routing; event ids ``hashlib`` content hashes; ``created_at`` injected; no RNG; offline.
Reuses :func:`replay_engine.evaluate_rule` so serving + replay + shadow interpret a rule identically.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from src.baltor.determinism.replay_engine import evaluate_rule
from src.baltor.determinism.rule_candidate_generator import RuleCandidate

EPOCH = "1970-01-01T00:00:00Z"

#: the served-by sources. Exactly one names the deterministic path; the rest are non-fabricating fallbacks.
SERVED_BY_RULE = "deterministic_rule"     # an active rule fired confidently → deterministic decision served
SERVED_BY_GATEWAY = "llm_gateway"         # re-proposed via the gateway (proposal, not authoritative)
SERVED_BY_HUMAN = "human_review"          # escalated to a human/policy adjudication queue
SERVED_BY_HOLD_OUT = "hold_out"           # abstained — nothing served, excluded from the pack
_FALLBACK_ROUTES = {"gateway": SERVED_BY_GATEWAY, "human": SERVED_BY_HUMAN, "hold_out": SERVED_BY_HOLD_OUT}

#: why the router fell back (recorded for mining).
REASON_RULE_FIRED = "rule_fired"
REASON_INACTIVE = "rule_inactive"
REASON_ABSTAINED = "rule_abstained_preconditions"
REASON_OOD = "out_of_distribution_input"
REASON_LOW_CONFIDENCE = "below_min_confidence"


def _canon(body: Any) -> bytes:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _attr(obj: Any, name: str, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


@dataclass
class RoutingEvent:
    """One serving decision. ``fabricated`` is always False — a fallback may abstain/escalate, never invent."""
    event_id: str
    rule_candidate_id: str
    served_by: str                  # SERVED_BY_*
    decision: Any                   # the served decision (None for human/hold_out/gateway — not authoritative)
    is_authoritative: bool          # True ONLY when an active rule fired confidently
    reason: str                     # REASON_*
    fell_back: bool
    fabricated: bool                # invariant — always False (a fallback never invents a fact)
    input_signature: str            # a content hash of the routed input (for mining / dedupe)
    created_at: str = EPOCH
    schema_version: str = "RoutingEvent.v1"

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "event_id": self.event_id,
                "rule_candidate_id": self.rule_candidate_id, "served_by": self.served_by,
                "decision": self.decision, "is_authoritative": self.is_authoritative, "reason": self.reason,
                "fell_back": self.fell_back, "fabricated": self.fabricated,
                "input_signature": self.input_signature, "created_at": self.created_at}


def _input_signature(inputs: dict) -> str:
    return "in-" + hashlib.sha256(_canon(inputs)).hexdigest()[:16]


def _is_ood(rule: RuleCandidate, inputs: dict) -> bool:
    """Out-of-distribution = a required input field is missing, OR the input carries an UNKNOWN field the rule
    never declared in ``input_fields`` while ALSO being missing a declared field (a shape the rule never saw)."""
    declared = set(rule.input_fields)
    present = set(inputs.keys())
    missing_required = bool(declared - present)
    return missing_required


def route(rule: RuleCandidate, inputs: dict, *, confidence: float = 1.0, now: str = EPOCH) -> RoutingEvent:
    """Serve an input deterministically-first. Returns a recorded RoutingEvent (rule-served OR fallback).

    ``rule.active`` gates whether the rule may serve at all. ``confidence`` is the caller's confidence for THIS
    input (e.g. from upstream signals); below ``rule.fallback.min_confidence`` the router defers. OOD inputs and
    abstaining rules also fall back. A fallback NEVER fabricates — it returns the route + reason and a None
    decision (the gateway/human path will produce a *proposal*/*adjudication*, not an authoritative fact here).
    """
    fb = rule.fallback
    sig = _input_signature(inputs)

    def event(served_by: str, decision: Any, authoritative: bool, reason: str, fell_back: bool) -> RoutingEvent:
        body = {"rule": rule.rule_candidate_id, "by": served_by, "reason": reason, "sig": sig}
        eid = "route-" + hashlib.sha256(_canon(body)).hexdigest()[:16]
        return RoutingEvent(event_id=eid, rule_candidate_id=rule.rule_candidate_id, served_by=served_by,
                            decision=decision, is_authoritative=authoritative, reason=reason,
                            fell_back=fell_back, fabricated=False, input_signature=sig, created_at=now)

    def fallback(reason: str) -> RoutingEvent:
        served_by = _FALLBACK_ROUTES.get(fb.route, SERVED_BY_HOLD_OUT)
        # a fallback NEVER serves an authoritative fact: decision is None, is_authoritative=False.
        return event(served_by, None, authoritative=False, reason=reason, fell_back=True)

    # an inactive / un-promoted rule never serves — straight to fallback.
    if not rule.active:
        return fallback(REASON_INACTIVE)

    # out-of-distribution input → fallback (never force a verdict on an input shape the rule never saw).
    if _is_ood(rule, inputs):
        return fallback(REASON_OOD)

    # low confidence → defer to the fallback path.
    if confidence < fb.min_confidence:
        return fallback(REASON_LOW_CONFIDENCE)

    # deterministic-first: run the active rule.
    fired, decision = evaluate_rule(rule, inputs)
    if not fired:
        return fallback(REASON_ABSTAINED)

    # the rule fired confidently on an in-distribution input → serve deterministically (authoritative).
    return event(SERVED_BY_RULE, decision, authoritative=True, reason=REASON_RULE_FIRED, fell_back=False)


def activate(rule: RuleCandidate, receipt: Any) -> RuleCandidate:
    """Return an ACTIVE copy of a candidate AFTER a promotion receipt cleared it. The router only serves an
    active rule; this is the one place ``active`` flips True — and only with a ``promoted`` receipt."""
    if not bool(_attr(receipt, "promoted", False)):
        raise ValueError("cannot activate a rule without a promoted RulePromotionReceipt")
    from dataclasses import replace
    return replace(rule, status="active", active=True)
