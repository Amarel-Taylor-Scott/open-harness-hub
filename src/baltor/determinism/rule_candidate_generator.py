#!/usr/bin/env python3
"""src.baltor.determinism.rule_candidate_generator — turn a mined PatternCandidate into a PROPOSED RuleCandidate.

The Determinism Factory's law: *LLMs propose, Baltor verifies, repeated VERIFIED patterns become
deterministic.* The pattern miner (Lane B, ``src.baltor.determinism.pattern_miner``) surfaces a
``PatternCandidate`` — a repeated decision shape seen across VERIFIED traces (adjudicated, source-grounded,
receipt-backed). This module proposes a ``RuleCandidate`` that would reproduce that decision deterministically.

Three load-bearing invariants (enforced here, re-checked downstream by the replay engine + promotion gate):

* **Proposed, NOT active.** A generated candidate is always ``status="proposed"`` / ``active=False``. It is a
  hypothesis to be replayed + shadowed + gated — never a live authority. Nothing here can serve a fact.
* **Lossless link-back.** A candidate carries ``distilled_from_trace_ids`` (the exact VERIFIED traces it was
  distilled from) and ``pattern_candidate_id``. Promotion NEVER deletes those traces; the rule points back to
  them so the lineage rehydrates (``src.baltor.distillation``). A candidate with no source traces is rejected.
* **Consensus is not truth.** A pattern whose ``label_source`` is multi-LLM consensus *alone* (no deterministic
  validator, authority/policy, or human adjudication produced the label) can NOT yield a truth-serving rule —
  ``from_pattern`` raises ``ConsensusOnlyError``. Consensus is an evidence/ambiguity signal only.

A ``RuleCandidate`` is self-describing for downstream replay: input fields, output decision, scope, examples,
counterexamples, expected failure modes, and a mandatory ``fallback`` policy (deterministic rule first, then a
fallback path for low-confidence / unknown / OOD inputs). It does NOT execute its own reconciliation/optimizer —
the rule's ``decision_kind`` records WHICH existing authority it asserts-equivalence to (e.g. the existing
reconciliation reference), and the replay engine evaluates the rule against historical VERIFIED outcomes.

This module is a pure generator: no I/O, no clock (``created_at`` injected), ids are ``hashlib`` content hashes,
no RNG, stdlib only, fully offline. It does NOT import Lane B at module load — it consumes the pattern shape by
duck-typed attribute/dict access so the lanes build in parallel.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

EPOCH = "1970-01-01T00:00:00Z"  # injected default stamp (never a clock read; keeps ids byte-stable)

# ── rule taxonomy (single source of the kinds a candidate may take) ───────────────────────────────
#: the rule TYPES a candidate may take (spec PART 5). One definition; the generator + gate read this.
RULE_TYPES = (
    "decision_table", "regex_or_pattern", "source_authority_rule", "graph_rule", "threshold_rule",
    "schema_rule", "routing_rule", "conflict_detector_rule", "reconciliation_policy_rule", "freshness_rule",
)

#: rules whose output SERVES or selects a fact (truth-serving) → near-zero false positives, human first promo.
#: rules that only ROUTE work (routing/schema/threshold non-fact) → lower risk, may promote earlier.
_TRUTH_SERVING_KINDS = ("source_authority_rule", "reconciliation_policy_rule", "conflict_detector_rule",
                        "graph_rule", "freshness_rule")
_ROUTING_KINDS = ("routing_rule", "schema_rule", "threshold_rule", "regex_or_pattern", "decision_table")

#: how a pattern's verified label was PRODUCED. Consensus alone can never be the producer (it's evidence only).
LABEL_VALIDATOR = "deterministic_validator"      # the existing reconciliation/policy/validator produced it
LABEL_AUTHORITY = "authority_or_policy"          # an authority/precedence rule produced it
LABEL_ADJUDICATION = "human_adjudication"        # a human/policy adjudication record produced it
LABEL_CONSENSUS_ONLY = "consensus_only"          # ONLY multi-LLM agreement — NOT a truth producer
_VERIFIED_LABEL_SOURCES = (LABEL_VALIDATOR, LABEL_AUTHORITY, LABEL_ADJUDICATION)


class RuleCandidateError(Exception):
    """Base class for candidate-generation failures."""


class ConsensusOnlyError(RuleCandidateError):
    """The pattern's label came from multi-LLM consensus ALONE — consensus is evidence, never truth."""


class NoVerifiedTraceError(RuleCandidateError):
    """The pattern carries no VERIFIED distilled-from traces — there is nothing lossless to link back to."""


def _canon(body: Any) -> bytes:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _rule_id(body: dict) -> str:
    return "rulecand-" + hashlib.sha256(_canon(body)).hexdigest()[:16]


def is_truth_serving(decision_kind: str) -> bool:
    """A rule that selects/serves a FACT is truth-serving (strict promotion bar). Routing rules are not."""
    return decision_kind in _TRUTH_SERVING_KINDS


@dataclass(frozen=True)
class FallbackPolicy:
    """The mandatory fallback every active rule must carry: rule-first, then a recorded non-fabricating path.

    ``route`` names where a low-confidence / unknown / OOD input goes (gateway = LLM re-propose, human =
    adjudication queue, hold_out = abstain & exclude from the served pack). ``never_fabricate`` is always True:
    a fallback may abstain or escalate, it may NEVER invent a fact. ``min_confidence`` below which the rule
    defers to the fallback."""
    route: str = "hold_out"               # gateway | human | hold_out
    min_confidence: float = 1.0           # rule must be at least this confident or it defers
    on_unknown_input: str = "hold_out"    # what to do for OOD / unseen input fields
    never_fabricate: bool = True          # invariant — a fallback may abstain/escalate, never invent a fact

    def to_dict(self) -> dict:
        return {"route": self.route, "min_confidence": round(self.min_confidence, 4),
                "on_unknown_input": self.on_unknown_input, "never_fabricate": self.never_fabricate}


@dataclass(frozen=True)
class RuleCandidate:
    """A PROPOSED deterministic rule distilled from a VERIFIED pattern — not active, not authoritative.

    ``decision_logic`` is the declarative spec the replay/shadow engines evaluate (e.g. for a
    ``reconciliation_policy_rule``: ``{"if": {"conflict_type": "deadline_mismatch", "higher_authority_wins":
    true}, "then": {"winner": "higher_authority_source", "loser": "held_out"}}``). The generator does NOT run
    reconciliation — it asserts-equivalence to the EXISTING authority named by ``asserts_equivalence_to``.
    """
    rule_candidate_id: str
    decision_kind: str                          # one of RULE_TYPES
    asserts_equivalence_to: str                 # the EXISTING authority this reproduces (never a 2nd authority)
    scope: str                                  # global_public | tenant_private
    tenant_id: str
    input_fields: tuple[str, ...]               # the fields the rule reads
    output_decision: str                        # what the rule decides (a label/winner/route — declarative)
    decision_logic: dict                        # declarative if/then the replay engine evaluates
    examples: tuple[dict, ...]                   # VERIFIED positive exemplars (rule should match)
    counterexamples: tuple[dict, ...]            # VERIFIED held-out / negative cases (rule must NOT match)
    expected_failure_modes: tuple[str, ...]      # where this rule is expected to abstain / defer
    fallback: FallbackPolicy                    # MANDATORY — rule-first, then a recorded non-fabricating path
    pattern_candidate_id: str                   # the PatternCandidate this came from
    distilled_from_trace_ids: tuple[str, ...]    # the VERIFIED traces it was distilled from (lossless link)
    label_source: str                           # how the verified label was produced (never consensus_only)
    truth_serving: bool                         # selects/serves a fact → strict promotion bar
    status: str = "proposed"                    # ALWAYS proposed at generation
    active: bool = False                        # NEVER active at generation
    created_at: str = EPOCH
    schema_version: str = "RuleCandidate.v1"

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version, "rule_candidate_id": self.rule_candidate_id,
            "decision_kind": self.decision_kind, "asserts_equivalence_to": self.asserts_equivalence_to,
            "scope": self.scope, "tenant_id": self.tenant_id, "input_fields": list(self.input_fields),
            "output_decision": self.output_decision, "decision_logic": dict(self.decision_logic),
            "examples": [dict(e) for e in self.examples],
            "counterexamples": [dict(c) for c in self.counterexamples],
            "expected_failure_modes": list(self.expected_failure_modes), "fallback": self.fallback.to_dict(),
            "pattern_candidate_id": self.pattern_candidate_id,
            "distilled_from_trace_ids": list(self.distilled_from_trace_ids), "label_source": self.label_source,
            "truth_serving": self.truth_serving, "status": self.status, "active": self.active,
            "created_at": self.created_at,
        }


def _attr(obj: Any, name: str, default=None):
    """Duck-typed read: works on a Lane B dataclass (attribute) OR a plain dict (key) — so lanes decouple."""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def from_pattern(pattern: Any, *, decision_kind: str, asserts_equivalence_to: str, output_decision: str,
                 decision_logic: dict, fallback: FallbackPolicy | None = None,
                 expected_failure_modes: tuple[str, ...] = (), now: str = EPOCH) -> RuleCandidate:
    """Generate a PROPOSED RuleCandidate from a VERIFIED PatternCandidate.

    ``pattern`` is duck-typed (Lane B ``PatternCandidate`` or a dict) and MUST carry:
      ``pattern_candidate_id``, ``scope``, ``tenant_id``, ``input_fields``, ``label_source``,
      ``distilled_from_trace_ids`` (≥1), ``examples`` (verified positives), ``counterexamples`` (held-out).

    Raises ``ConsensusOnlyError`` if the label came from consensus alone, ``NoVerifiedTraceError`` if there are
    no verified traces to link back to, and ``RuleCandidateError`` for an unknown ``decision_kind``.
    """
    if decision_kind not in RULE_TYPES:
        raise RuleCandidateError(f"unknown decision_kind {decision_kind!r}; must be one of {RULE_TYPES}")

    label_source = _attr(pattern, "label_source", LABEL_CONSENSUS_ONLY)
    if label_source not in _VERIFIED_LABEL_SOURCES:
        # consensus_only (or anything not a real producer) can NEVER mint a rule — it is evidence, not truth.
        raise ConsensusOnlyError(
            f"pattern label_source={label_source!r} is not a truth producer; consensus alone cannot mint a "
            f"rule — a deterministic validator / authority / human adjudication must have produced the label")

    trace_ids = tuple(_attr(pattern, "distilled_from_trace_ids", ()) or ())
    if not trace_ids:
        raise NoVerifiedTraceError(
            "pattern has no distilled_from_trace_ids — no VERIFIED traces to losslessly link back to")

    scope = _attr(pattern, "scope", "global_public")
    tenant_id = _attr(pattern, "tenant_id", "")
    input_fields = tuple(_attr(pattern, "input_fields", ()) or ())
    examples = tuple(dict(e) for e in (_attr(pattern, "examples", ()) or ()))
    counterexamples = tuple(dict(c) for c in (_attr(pattern, "counterexamples", ()) or ()))
    pattern_id = _attr(pattern, "pattern_candidate_id", "")

    fb = fallback or FallbackPolicy()
    truth = is_truth_serving(decision_kind)

    # identity = the rule's declarative meaning + scope + its source pattern, so the same rule is byte-stable.
    body = {"k": decision_kind, "eq": asserts_equivalence_to, "scope": scope, "tenant": tenant_id,
            "in": sorted(input_fields), "out": output_decision, "logic": decision_logic, "pat": pattern_id}
    return RuleCandidate(
        rule_candidate_id=_rule_id(body), decision_kind=decision_kind,
        asserts_equivalence_to=asserts_equivalence_to, scope=scope, tenant_id=tenant_id,
        input_fields=input_fields, output_decision=output_decision, decision_logic=dict(decision_logic),
        examples=examples, counterexamples=counterexamples,
        expected_failure_modes=tuple(expected_failure_modes), fallback=fb, pattern_candidate_id=pattern_id,
        distilled_from_trace_ids=trace_ids, label_source=label_source, truth_serving=truth,
        status="proposed", active=False, created_at=now)
