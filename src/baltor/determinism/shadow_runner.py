#!/usr/bin/env python3
"""src.baltor.determinism.shadow_runner — run a candidate rule in SHADOW alongside the live authority.

Maturity ladder M6: before a proven rule may be promoted (M7), it runs in **shadow** next to the live path —
the existing deterministic authority (reconciliation / validator / policy / human adjudication) that already
produces the served decision. The shadow rule's output is RECORDED but is **never authoritative**: the live
decision is returned unchanged, byte-for-byte, whether the shadow agreed, disagreed, or abstained. Shadow is
pure observation; it cannot serve a fact, change a winner, or mutate the live path.

Each shadow tick captures ``(live_decision, shadow_decision, agreement)``. A disagreement on a NON-truth-
serving rule is a benign signal (feeds future mining). A disagreement on a TRUTH-serving rule where the shadow
fired with the WRONG fact is an **unsafe mismatch** — exactly the error class that must never reach production.
``ShadowRunReport.unsafe_mismatch_count > 0`` BLOCKS promotion (the promotion gate reads this report).

This module wraps the live path by callable so the engine stays decoupled from any concrete authority. It does
NOT call reconciliation/optimizer itself — MAIN injects the live decision (or a callable producing it). The
shadow verdict reuses :func:`replay_engine.evaluate_rule` so shadow + replay can never diverge in how a rule
is interpreted (single source of rule evaluation).

Determinism: live decision injected; ids ``hashlib`` content hashes; ``created_at`` injected; no RNG; offline.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable

from src.baltor.determinism.replay_engine import evaluate_rule
from src.baltor.determinism.rule_candidate_generator import RuleCandidate

EPOCH = "1970-01-01T00:00:00Z"

GLOBAL_PUBLIC = "global_public"
TENANT_PRIVATE = "tenant_private"


def _canon(body: Any) -> bytes:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _attr(obj: Any, name: str, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


@dataclass
class ShadowTick:
    """One shadow observation: live (authoritative) vs shadow (recorded, non-authoritative)."""
    trace_id: str
    live_decision: Any              # the authoritative decision actually served (UNCHANGED by shadow)
    shadow_fired: bool
    shadow_decision: Any            # what the shadow rule would have decided (recorded only)
    agreement: bool                 # shadow fired AND shadow_decision == live_decision
    unsafe_mismatch: bool           # truth-serving rule fired with a decision != live → dangerous
    served_authority: str           # which authority produced the live decision (provenance, never the rule)

    def to_dict(self) -> dict:
        return {"trace_id": self.trace_id, "live_decision": self.live_decision,
                "shadow_fired": self.shadow_fired, "shadow_decision": self.shadow_decision,
                "agreement": self.agreement, "unsafe_mismatch": self.unsafe_mismatch,
                "served_authority": self.served_authority}


@dataclass
class ShadowRunReport:
    """Summary of a shadow run. ``live_authoritative`` is always True (shadow never serves)."""
    report_id: str
    rule_candidate_id: str
    tick_count: int
    shadow_fired_count: int
    agreement_count: int
    disagreement_count: int
    abstain_count: int
    unsafe_mismatch_count: int      # >0 BLOCKS promotion
    agreement_rate: float
    live_authoritative: bool        # invariant — the live path stayed authoritative throughout
    ticks: list
    created_at: str = EPOCH
    schema_version: str = "ShadowRunReport.v1"

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "report_id": self.report_id,
                "rule_candidate_id": self.rule_candidate_id, "tick_count": self.tick_count,
                "shadow_fired_count": self.shadow_fired_count, "agreement_count": self.agreement_count,
                "disagreement_count": self.disagreement_count, "abstain_count": self.abstain_count,
                "unsafe_mismatch_count": self.unsafe_mismatch_count,
                "agreement_rate": round(self.agreement_rate, 4),
                "live_authoritative": self.live_authoritative,
                "ticks": [t.to_dict() for t in self.ticks], "created_at": self.created_at}


def _live_decision_of(trace: Any, live_decider: Callable[[Any], Any] | None) -> tuple[Any, str]:
    """Resolve the AUTHORITATIVE live decision for a trace. Prefer an injected callable (the real authority);
    else read the trace's already-served ``final_decision``. Returns (decision, authority_name)."""
    if live_decider is not None:
        return live_decider(trace), str(_attr(trace, "served_authority", "injected_live_authority"))
    return _attr(trace, "final_decision"), str(_attr(trace, "served_authority", "existing_authority"))


def run_shadow(rule: RuleCandidate, traces: list, *, live_decider: Callable[[Any], Any] | None = None,
               now: str = EPOCH) -> ShadowRunReport:
    """Run ``rule`` in shadow over ``traces``. The live decision is returned UNCHANGED; the shadow verdict is
    recorded only. An unsafe mismatch on a truth-serving rule is counted and will block promotion downstream.
    """
    ticks: list[ShadowTick] = []
    fired = agree = disagree = abstain = unsafe = 0

    for trace in sorted(traces, key=lambda t: str(_attr(t, "trace_id", _attr(t, "workflow_id", "")))):
        tid = str(_attr(trace, "trace_id", _attr(trace, "workflow_id", "")))
        live, authority = _live_decision_of(trace, live_decider)
        s_fired, s_decision = evaluate_rule(rule, trace)

        if not s_fired:
            abstain += 1
            ticks.append(ShadowTick(tid, live, False, None, agreement=False, unsafe_mismatch=False,
                                    served_authority=authority))
            continue

        fired += 1
        agreed = (s_decision == live)
        if agreed:
            agree += 1
        else:
            disagree += 1
        this_unsafe = bool(rule.truth_serving and not agreed)
        if this_unsafe:
            unsafe += 1
        ticks.append(ShadowTick(tid, live, True, s_decision, agreement=agreed, unsafe_mismatch=this_unsafe,
                                served_authority=authority))

    rate = (agree / fired) if fired else 0.0
    body = {"rule": rule.rule_candidate_id, "fired": fired, "agree": agree, "dis": disagree,
            "abst": abstain, "unsafe": unsafe, "n": len(traces)}
    rid = "shadow-" + hashlib.sha256(_canon(body)).hexdigest()[:16]
    return ShadowRunReport(
        report_id=rid, rule_candidate_id=rule.rule_candidate_id, tick_count=len(traces),
        shadow_fired_count=fired, agreement_count=agree, disagreement_count=disagree, abstain_count=abstain,
        unsafe_mismatch_count=unsafe, agreement_rate=rate, live_authoritative=True, ticks=ticks, created_at=now)
