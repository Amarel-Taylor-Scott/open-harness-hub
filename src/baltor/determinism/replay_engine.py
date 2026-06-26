#!/usr/bin/env python3
"""src.baltor.determinism.replay_engine — replay a RuleCandidate against historical VERIFIED traces.

Before a proposed rule may ever be promoted it must be PROVEN to reproduce the VERIFIED outcomes it was
distilled from. This engine evaluates a :class:`~src.baltor.determinism.rule_candidate_generator.RuleCandidate`
against a corpus of historical ``WorkflowTrace`` records whose ``final_decision`` was already produced by an
EXISTING deterministic authority (reconciliation / validator / policy / human adjudication). It compares the
rule's deterministic verdict to each trace's verified ``final_decision`` and computes:

  precision · recall · false positives · false negatives · abstention rate · UNSAFE-promotion count ·
  TENANT-LEAKAGE risk.

It is a META evaluator. It does NOT run reconciliation or the optimizer; it only re-applies the candidate's
declarative ``decision_logic`` and scores it against outcomes the existing authorities already produced. A
global-scope rule replayed over a ``tenant_private`` trace is a tenant LEAK (counted, never silently scored).
An UNSAFE promotion is the dangerous error class — a truth-serving rule that emits the WRONG winner/fact (a
false positive on a truth-serving rule), e.g. serving the held-out FAQ-30 instead of the Reg-E 10-day reference.

Determinism: pure evaluation; ids are ``hashlib`` content hashes; ``created_at`` injected (no clock); no RNG;
stdlib only; offline. Traces are duck-typed (Lane B dataclass OR plain dict) so the lanes decouple.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from src.baltor.determinism.rule_candidate_generator import RuleCandidate

EPOCH = "1970-01-01T00:00:00Z"

#: the verdict an evaluated rule can emit for a single trace.
VERDICT_MATCH = "match"          # rule emitted a decision (may agree or disagree with the verified label)
VERDICT_ABSTAIN = "abstain"      # rule's preconditions did not fire → defers (correct, safe behaviour)

#: scopes — must mirror the lossless-store definition; a global rule over tenant_private data is a LEAK.
GLOBAL_PUBLIC = "global_public"
TENANT_PRIVATE = "tenant_private"


def _canon(body: Any) -> bytes:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _attr(obj: Any, name: str, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


@dataclass
class TraceVerdict:
    """One trace's outcome under the candidate: the rule verdict, the verified label, and the safety class."""
    trace_id: str
    fired: bool                     # did the rule's preconditions match this trace?
    rule_decision: Any              # what the rule decided (None if it abstained)
    verified_decision: Any          # the trace's verified final_decision (truth for scoring)
    correct: bool                   # fired AND rule_decision == verified_decision
    unsafe: bool                    # truth-serving rule fired with the WRONG fact/winner (dangerous FP)
    tenant_leak: bool               # a global rule was applied to a tenant_private trace

    def to_dict(self) -> dict:
        return {"trace_id": self.trace_id, "fired": self.fired, "rule_decision": self.rule_decision,
                "verified_decision": self.verified_decision, "correct": self.correct,
                "unsafe": self.unsafe, "tenant_leak": self.tenant_leak}


@dataclass
class RuleReplayReport:
    """Scored outcome of replaying a candidate against a historical VERIFIED trace corpus."""
    report_id: str
    rule_candidate_id: str
    trace_count: int
    fired_count: int
    precision: float
    recall: float
    false_positives: int
    false_negatives: int
    true_positives: int
    abstentions: int
    abstention_rate: float
    unsafe_count: int               # truth-serving false positives — MUST be 0 to promote a truth-serving rule
    tenant_leak_count: int          # global rule touched tenant_private data — MUST be 0
    verdicts: list
    created_at: str = EPOCH
    schema_version: str = "RuleReplayReport"

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "report_id": self.report_id,
                "rule_candidate_id": self.rule_candidate_id, "trace_count": self.trace_count,
                "fired_count": self.fired_count, "precision": round(self.precision, 4),
                "recall": round(self.recall, 4), "false_positives": self.false_positives,
                "false_negatives": self.false_negatives, "true_positives": self.true_positives,
                "abstentions": self.abstentions, "abstention_rate": round(self.abstention_rate, 4),
                "unsafe_count": self.unsafe_count, "tenant_leak_count": self.tenant_leak_count,
                "verdicts": [v.to_dict() for v in self.verdicts], "created_at": self.created_at}


def evaluate_rule(rule: RuleCandidate, trace: Any) -> tuple[bool, Any]:
    """Evaluate a candidate's declarative ``decision_logic`` against ONE trace → (fired, rule_decision).

    A trace is duck-typed and exposes the rule's ``input_fields`` (via ``inputs`` dict or top-level keys). The
    ``decision_logic`` is a declarative ``{"if": {field: expected, ...}, "then": <decision>}``. Special
    precondition predicates (``higher_authority_wins`` / ``newer_version_wins``) compare two sides named in the
    trace inputs. ``then`` may be a literal decision OR a selector (``"higher_authority_source"`` etc.) resolved
    from the trace. The engine never runs reconciliation — it only re-applies this declarative form.
    """
    logic = rule.decision_logic or {}
    cond = logic.get("if", {}) or {}
    inputs = _attr(trace, "inputs", None)
    if inputs is None:
        inputs = trace if isinstance(trace, dict) else {f: _attr(trace, f) for f in rule.input_fields}

    def field(name):
        return inputs.get(name) if isinstance(inputs, dict) else _attr(trace, name)

    # plain field-equality preconditions
    for key, expected in cond.items():
        if key in ("higher_authority_wins", "newer_version_wins"):
            continue
        if field(key) != expected:
            return (False, None)

    # selector preconditions: the two sides must be comparable for the rule to fire deterministically
    if cond.get("higher_authority_wins"):
        a_auth, b_auth = field("authority_a"), field("authority_b")
        if a_auth is None or b_auth is None or a_auth == b_auth:
            return (False, None)  # cannot deterministically pick a winner → abstain
    if cond.get("newer_version_wins"):
        a_v, b_v = field("version_a"), field("version_b")
        if a_v is None or b_v is None or a_v == b_v:
            return (False, None)

    then = logic.get("then")
    decision = _resolve_then(then, field, cond)
    return (True, decision)


def _resolve_then(then: Any, field, cond: dict) -> Any:
    """Resolve a ``then`` clause into a concrete decision. Selectors read the winning side from the trace."""
    if isinstance(then, str):
        if then == "higher_authority_source":
            return field("source_a") if (field("authority_a") or 0) > (field("authority_b") or 0) else field("source_b")
        if then == "newer_version_source":
            return field("source_a") if (field("version_a") or 0) >= (field("version_b") or 0) else field("source_b")
        return then  # a literal label
    if isinstance(then, dict):
        return {k: _resolve_then(v, field, cond) for k, v in then.items()}
    return then


def replay(rule: RuleCandidate, traces: list, *, now: str = EPOCH) -> RuleReplayReport:
    """Replay a candidate against a historical VERIFIED trace corpus → a scored RuleReplayReport.

    Each trace MUST carry a verified ``final_decision`` (the truth for scoring) and may carry
    ``rule_applicable`` (whether a correct rule SHOULD fire here — used for recall/FN). A trace's ``scope`` /
    ``tenant_id`` decide tenant-leak: a ``global_public`` rule applied to a ``tenant_private`` trace is a leak.
    """
    verdicts: list[TraceVerdict] = []
    tp = fp = fn = abst = 0
    unsafe = leak = 0

    for trace in sorted(traces, key=lambda t: str(_attr(t, "trace_id", _attr(t, "workflow_id", "")))):
        tid = str(_attr(trace, "trace_id", _attr(trace, "workflow_id", "")))
        verified = _attr(trace, "final_decision")
        t_scope = _attr(trace, "scope", GLOBAL_PUBLIC)
        applicable = bool(_attr(trace, "rule_applicable", True))

        # tenant-leak: a global rule must NEVER be applied to tenant_private data (counted; verdict marked).
        this_leak = (rule.scope == GLOBAL_PUBLIC and t_scope == TENANT_PRIVATE)
        if this_leak:
            leak += 1

        fired, decision = evaluate_rule(rule, trace)
        if not fired:
            abst += 1
            # a MISS on a trace where a correct rule should have fired is a false negative.
            if applicable:
                fn += 1
            verdicts.append(TraceVerdict(tid, False, None, verified, correct=False, unsafe=False,
                                         tenant_leak=this_leak))
            continue

        correct = (decision == verified)
        # an UNSAFE error = a truth-serving rule fired but emitted the WRONG fact/winner (a dangerous FP).
        this_unsafe = bool(rule.truth_serving and not correct)
        if this_unsafe:
            unsafe += 1
        if correct:
            tp += 1
        else:
            fp += 1
        verdicts.append(TraceVerdict(tid, True, decision, verified, correct=correct, unsafe=this_unsafe,
                                     tenant_leak=this_leak))

    fired = tp + fp
    precision = (tp / fired) if fired else 0.0
    recall = (tp / (tp + fn)) if (tp + fn) else 0.0
    abst_rate = (abst / len(traces)) if traces else 0.0
    body = {"rule": rule.rule_candidate_id, "tp": tp, "fp": fp, "fn": fn, "abst": abst,
            "unsafe": unsafe, "leak": leak, "n": len(traces)}
    rid = "replay-" + hashlib.sha256(_canon(body)).hexdigest()[:16]
    return RuleReplayReport(
        report_id=rid, rule_candidate_id=rule.rule_candidate_id, trace_count=len(traces), fired_count=fired,
        precision=precision, recall=recall, false_positives=fp, false_negatives=fn, true_positives=tp,
        abstentions=abst, abstention_rate=abst_rate, unsafe_count=unsafe, tenant_leak_count=leak,
        verdicts=verdicts, created_at=now)
