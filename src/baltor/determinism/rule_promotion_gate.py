#!/usr/bin/env python3
"""src.baltor.determinism.rule_promotion_gate — the M7 gate that promotes a candidate to a deterministic rule.

A proposed rule becomes deterministic-first (LLM fallback only) ONLY through this gate. The gate is a hard,
deterministic AND of every safety check; ANY failed check BLOCKS promotion. A blocked candidate stays
``proposed`` — it is never silently activated. The promotion bar SCALES WITH RISK:

* **truth-serving rule** (selects/serves a fact): unsafe false positives MUST be ZERO, precision ≥ the strict
  bar, AND ``first_promotion`` requires a human-review sign-off flag. Near-zero FP, never auto.
* **routing rule** (routes work only): may promote on a lower precision bar with no unsafe-FP gate (a
  misroute is recoverable via the fallback), no human review required.

Every promotion is LOSSLESS: the resulting :class:`RulePromotionReceipt` PRESERVES the candidate's
``distilled_from_trace_ids`` (and pattern id) so the promoted rule always links back to the VERIFIED traces it
was distilled from — promotion never deletes the LLM/consensus/adjudication traces. The gate also enforces:

  schema-valid candidate · source handles preserved (promotion must NOT drop the source handles a truth-serving
  decision rests on) · a fallback policy EXISTS · tenant-safe (a global rule may not be minted from
  tenant_private traces; no tenant-leak in the replay; no unsafe shadow mismatch) · a replay report EXISTS and
  was run against THIS candidate · the shadow report (if given) had no unsafe mismatch.

This gate is a META authority over the existing authorities — it decides whether a candidate may go live, not
what a fact is. It never serves a fact and never creates a second reconciliation/optimizer.

Determinism: pure checks; receipt id ``hashlib`` content hash; ``created_at`` injected; no RNG; offline.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from src.baltor.determinism.replay_engine import RuleReplayReport
from src.baltor.determinism.rule_candidate_generator import RuleCandidate
from src.baltor.determinism.shadow_runner import ShadowRunReport

EPOCH = "1970-01-01T00:00:00Z"

GLOBAL_PUBLIC = "global_public"
TENANT_PRIVATE = "tenant_private"

#: precision bars by risk. Truth-serving rules need a near-perfect bar; routing rules a looser one.
TRUTH_SERVING_PRECISION_BAR = 1.0     # near-zero false positives → 100% precision on the replay corpus
ROUTING_PRECISION_BAR = 0.95          # a misroute is recoverable via fallback → looser bar

#: a candidate id must have this prefix to be schema-shaped (produced by the candidate generator).
_CANDIDATE_ID_PREFIX = "rulecand-"


def _canon(body: Any) -> bytes:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


@dataclass
class GateCheck:
    name: str
    ok: bool
    detail: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


@dataclass
class RulePromotionReceipt:
    """The receipt of a promotion DECISION. ``promoted`` may be False (a blocked candidate still gets a
    receipt recording WHY it was blocked). On a promotion, ``distilled_from_trace_ids`` is preserved — the
    promoted rule links back to the VERIFIED traces it was distilled from (lossless)."""
    receipt_id: str
    rule_candidate_id: str
    promoted: bool
    decision: str                   # "promote" | "block"
    truth_serving: bool
    precision_bar: float
    checks: list
    blocked_reasons: list
    replay_report_id: str
    shadow_report_id: str
    distilled_from_trace_ids: list  # PRESERVED — promotion never deletes the traces (lossless)
    pattern_candidate_id: str
    human_review_signed: bool
    created_at: str = EPOCH
    schema_version: str = "RulePromotionReceipt.v1"

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "receipt_id": self.receipt_id,
                "rule_candidate_id": self.rule_candidate_id, "promoted": self.promoted,
                "decision": self.decision, "truth_serving": self.truth_serving,
                "precision_bar": round(self.precision_bar, 4), "checks": [c.to_dict() for c in self.checks],
                "blocked_reasons": list(self.blocked_reasons), "replay_report_id": self.replay_report_id,
                "shadow_report_id": self.shadow_report_id,
                "distilled_from_trace_ids": list(self.distilled_from_trace_ids),
                "pattern_candidate_id": self.pattern_candidate_id,
                "human_review_signed": self.human_review_signed, "created_at": self.created_at}


def _is_schema_valid(rule: RuleCandidate) -> tuple[bool, str]:
    """Structural validity of a candidate (id shape, required fields present, declarative logic present)."""
    if not isinstance(rule, RuleCandidate):
        return (False, "not a RuleCandidate")
    if not rule.rule_candidate_id.startswith(_CANDIDATE_ID_PREFIX):
        return (False, f"id missing {_CANDIDATE_ID_PREFIX!r} prefix")
    if not rule.decision_logic or "then" not in rule.decision_logic:
        return (False, "decision_logic missing a 'then' clause")
    if not rule.output_decision:
        return (False, "no output_decision")
    return (True, "")


def _handles_preserved(rule: RuleCandidate) -> tuple[bool, str]:
    """A truth-serving rule must NOT drop the source handles its decision rests on. Every verified example /
    counterexample feeding a truth-serving rule must carry ≥1 source handle, and the rule must surface them."""
    if not rule.truth_serving:
        return (True, "")  # routing rules do not serve a fact, so they carry no source-handle obligation
    missing = []
    for ex in (*rule.examples, *rule.counterexamples):
        handles = ex.get("source_handles") or ([ex["source_handle"]] if ex.get("source_handle") else [])
        if not handles:
            missing.append(ex.get("trace_id") or ex.get("id") or "<example>")
    if missing:
        return (False, f"examples missing source handles: {sorted(set(missing))}")
    return (True, "")


def evaluate(rule: RuleCandidate, *, replay_report: RuleReplayReport,
             shadow_report: ShadowRunReport | None = None, first_promotion: bool = True,
             human_review_signed: bool = False, source_traces_scope: str | None = None,
             now: str = EPOCH) -> RulePromotionReceipt:
    """Decide whether ``rule`` may be promoted. Returns a RulePromotionReceipt (promote OR block + reasons).

    ``source_traces_scope`` is the scope of the traces the candidate was mined from — a ``global_public`` rule
    minted from ``tenant_private`` traces is BLOCKED (tenant_private cannot create global rules unless
    anonymized + approved, which would carry ``global_public`` source scope).
    """
    checks: list[GateCheck] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append(GateCheck(name, bool(ok), "" if ok else detail))

    # 1) the candidate is structurally schema-valid.
    sv_ok, sv_detail = _is_schema_valid(rule)
    add("schema_valid", sv_ok, sv_detail)

    # 2) a replay report EXISTS and was run against THIS candidate.
    has_replay = replay_report is not None and replay_report.rule_candidate_id == rule.rule_candidate_id
    add("replay_report_present", has_replay,
        "no replay report for this candidate" if not has_replay else "")

    # 3) a fallback policy EXISTS (an active rule must always have a recorded non-fabricating fallback).
    add("fallback_present", rule.fallback is not None, "no fallback policy")

    # 4) source handles preserved (truth-serving rules must not drop the handles their decision rests on).
    h_ok, h_detail = _handles_preserved(rule)
    add("source_handles_preserved", h_ok, h_detail)

    # 5) precision meets the risk-scaled bar.
    bar = TRUTH_SERVING_PRECISION_BAR if rule.truth_serving else ROUTING_PRECISION_BAR
    prec_ok = has_replay and replay_report.precision >= bar
    add("precision_meets_bar", prec_ok,
        f"precision {getattr(replay_report, 'precision', 'n/a')} < bar {bar}" if not prec_ok else "")

    # 6) ZERO unsafe false positives on a TRUTH-serving rule (the dangerous error class).
    if rule.truth_serving:
        unsafe_ok = has_replay and replay_report.unsafe_count == 0
        add("zero_unsafe_false_positives", unsafe_ok,
            f"unsafe_count={getattr(replay_report, 'unsafe_count', 'n/a')}" if not unsafe_ok else "")

    # 7) tenant-safe: no tenant-leak in the replay; a global rule may not be minted from tenant_private traces.
    leak_ok = has_replay and replay_report.tenant_leak_count == 0
    add("no_tenant_leak", leak_ok,
        f"tenant_leak_count={getattr(replay_report, 'tenant_leak_count', 'n/a')}" if not leak_ok else "")
    scope_ok = not (rule.scope == GLOBAL_PUBLIC and source_traces_scope == TENANT_PRIVATE)
    add("global_rule_not_from_private_traces", scope_ok,
        "global rule minted from tenant_private traces (needs anonymization + approval)" if not scope_ok else "")

    # 8) shadow had no unsafe mismatch (if a shadow report was supplied).
    if shadow_report is not None:
        shadow_ok = shadow_report.unsafe_mismatch_count == 0 and shadow_report.live_authoritative
        add("shadow_no_unsafe_mismatch", shadow_ok,
            f"unsafe_mismatch_count={shadow_report.unsafe_mismatch_count}" if not shadow_ok else "")

    # 9) lossless: the candidate carries the VERIFIED traces it was distilled from.
    add("distilled_from_traces_present", bool(rule.distilled_from_trace_ids),
        "candidate has no distilled_from_trace_ids" if not rule.distilled_from_trace_ids else "")

    # 10) first promotion of a TRUTH-serving rule requires a human-review sign-off.
    if rule.truth_serving and first_promotion:
        add("human_review_signed_for_first_truth_promotion", human_review_signed,
            "first promotion of a truth-serving rule requires human review sign-off" if not human_review_signed else "")

    blocked = [c.name for c in checks if not c.ok]
    promoted = not blocked
    decision = "promote" if promoted else "block"
    body = {"rule": rule.rule_candidate_id, "decision": decision, "blocked": sorted(blocked),
            "replay": getattr(replay_report, "report_id", "")}
    rid = "promorcpt-" + hashlib.sha256(_canon(body)).hexdigest()[:16]
    return RulePromotionReceipt(
        receipt_id=rid, rule_candidate_id=rule.rule_candidate_id, promoted=promoted, decision=decision,
        truth_serving=rule.truth_serving, precision_bar=bar, checks=checks, blocked_reasons=sorted(blocked),
        replay_report_id=getattr(replay_report, "report_id", ""),
        shadow_report_id=getattr(shadow_report, "report_id", "") if shadow_report else "",
        distilled_from_trace_ids=list(rule.distilled_from_trace_ids),
        pattern_candidate_id=rule.pattern_candidate_id, human_review_signed=human_review_signed, created_at=now)
