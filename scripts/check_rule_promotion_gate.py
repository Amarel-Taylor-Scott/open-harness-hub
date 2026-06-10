#!/usr/bin/env python3
"""scripts.check_rule_promotion_gate — proof (Determinism Factory PART 8 / ladder M7): the gate BLOCKS unsafe
promotions and promotes a clean candidate with a LOSSLESS receipt.

Hard cases proven:
  * a truth-serving rule with ANY unsafe false positive is BLOCKED;
  * a rule without a fallback is BLOCKED;
  * a rule whose promotion would DROP source handles (a truth-serving example with no handle) is BLOCKED;
  * a first promotion of a truth-serving rule with NO human review is BLOCKED;
  * a global rule minted from tenant_private traces is BLOCKED;
  * a clean candidate PROMOTES with a RulePromotionReceipt that PRESERVES distilled_from_trace_ids (lossless).

CLI: PYTHONPATH=. python3 scripts/check_rule_promotion_gate.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.determinism.replay_engine import replay  # noqa: E402
from src.baltor.determinism.rule_candidate_generator import FallbackPolicy, from_pattern  # noqa: E402
from src.baltor.determinism.rule_promotion_gate import RulePromotionReceipt, evaluate  # noqa: E402
from src.baltor.determinism.shadow_runner import run_shadow  # noqa: E402

NOW = "2026-06-05T00:00:00Z"

_LOGIC = {"if": {"conflict_type": "deadline_mismatch", "higher_authority_wins": True},
          "then": "higher_authority_source"}
_EQUIV = "scripts/artifact_graph/reconciliation.py::reconcile"


def _pattern(*, with_handles=True, trace_ids=("trace-rege-1",)):
    ex = {"trace_id": "trace-rege-1"}
    if with_handles:
        ex["source_handle"] = "ctx://cfpb/reg-e#deadline"
    return {
        "pattern_candidate_id": "patcand-cfpb-deadline", "scope": "global_public", "tenant_id": "acme",
        "input_fields": ("conflict_type", "authority_a", "authority_b", "source_a", "source_b"),
        "label_source": "authority_or_policy", "distilled_from_trace_ids": list(trace_ids),
        "examples": [ex], "counterexamples": [],
    }


def _clean_candidate(**pat_kwargs):
    return from_pattern(_pattern(**pat_kwargs), decision_kind="reconciliation_policy_rule",
                        asserts_equivalence_to=_EQUIV, output_decision="winner=higher_authority_source",
                        decision_logic=_LOGIC, fallback=FallbackPolicy(route="human"), now=NOW)


def _clean_traces():
    return [{"trace_id": "t1", "scope": "global_public", "rule_applicable": True, "final_decision": "reg-e",
             "inputs": {"conflict_type": "deadline_mismatch", "authority_a": 3, "authority_b": 1,
                        "source_a": "reg-e", "source_b": "faq"}}]


def _wrong_traces():
    # higher-authority side names faq → the rule picks the WRONG winner = an unsafe FP for a truth-serving rule.
    return [{"trace_id": "tw", "scope": "global_public", "rule_applicable": True, "final_decision": "reg-e",
             "inputs": {"conflict_type": "deadline_mismatch", "authority_a": 3, "authority_b": 1,
                        "source_a": "faq", "source_b": "reg-e"}}]


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── CASE 1: a truth-serving rule with an unsafe FP is BLOCKED ──────────────────────────────────
    cand = _clean_candidate()
    bad_replay = replay(cand, _wrong_traces(), now=NOW)
    r1 = evaluate(cand, replay_report=bad_replay, first_promotion=True, human_review_signed=True,
                  source_traces_scope="global_public", now=NOW)
    check("truth-serving rule with an unsafe FP is BLOCKED", r1.promoted is False)
    check("blocked reason names the unsafe-FP check", "zero_unsafe_false_positives" in r1.blocked_reasons)

    # ── CASE 2: a rule with NO fallback is BLOCKED ─────────────────────────────────────────────────
    from dataclasses import replace
    no_fallback = replace(_clean_candidate(), fallback=None)
    good_replay = replay(no_fallback, _clean_traces(), now=NOW)
    r2 = evaluate(no_fallback, replay_report=good_replay, first_promotion=True, human_review_signed=True,
                  source_traces_scope="global_public", now=NOW)
    check("rule with NO fallback is BLOCKED", r2.promoted is False)
    check("blocked reason names the fallback check", "fallback_present" in r2.blocked_reasons)

    # ── CASE 3: a promotion that would DROP source handles is BLOCKED ──────────────────────────────
    no_handle = _clean_candidate(with_handles=False)
    nh_replay = replay(no_handle, _clean_traces(), now=NOW)
    r3 = evaluate(no_handle, replay_report=nh_replay, first_promotion=True, human_review_signed=True,
                  source_traces_scope="global_public", now=NOW)
    check("rule that drops source handles is BLOCKED", r3.promoted is False)
    check("blocked reason names the source-handles check", "source_handles_preserved" in r3.blocked_reasons)

    # ── CASE 4: first promotion of a truth-serving rule with NO human review is BLOCKED ────────────
    r4 = evaluate(cand, replay_report=replay(cand, _clean_traces(), now=NOW), first_promotion=True,
                  human_review_signed=False, source_traces_scope="global_public", now=NOW)
    check("first truth-serving promotion without human review is BLOCKED", r4.promoted is False)
    check("blocked reason names the human-review check",
          "human_review_signed_for_first_truth_promotion" in r4.blocked_reasons)

    # ── CASE 5: a global rule minted from tenant_private traces is BLOCKED ─────────────────────────
    r5 = evaluate(cand, replay_report=replay(cand, _clean_traces(), now=NOW), first_promotion=True,
                  human_review_signed=True, source_traces_scope="tenant_private", now=NOW)
    check("global rule from tenant_private traces is BLOCKED", r5.promoted is False)
    check("blocked reason names the scope check", "global_rule_not_from_private_traces" in r5.blocked_reasons)

    # ── CASE 6: a CLEAN candidate PROMOTES with a lossless receipt ─────────────────────────────────
    good_replay = replay(cand, _clean_traces(), now=NOW)
    good_shadow = run_shadow(cand, [dict(t, served_authority="reconciliation") for t in _clean_traces()], now=NOW)
    r6 = evaluate(cand, replay_report=good_replay, shadow_report=good_shadow, first_promotion=True,
                  human_review_signed=True, source_traces_scope="global_public", now=NOW)
    check("a clean candidate PROMOTES", r6.promoted is True and r6.decision == "promote")
    check("the receipt is a RulePromotionReceipt", isinstance(r6, RulePromotionReceipt))
    check("no blocked reasons on a clean promotion", r6.blocked_reasons == [])

    # LOSSLESS: the receipt PRESERVES the distilled-from traces — promotion never deletes them.
    check("receipt PRESERVES distilled_from_trace_ids (lossless)",
          r6.distilled_from_trace_ids == ["trace-rege-1"])
    check("receipt links back to the source PatternCandidate", r6.pattern_candidate_id == "patcand-cfpb-deadline")
    check("receipt references the replay + shadow reports",
          r6.replay_report_id == good_replay.report_id and r6.shadow_report_id == good_shadow.report_id)

    # a ROUTING rule promotes on the looser bar without human review (risk-scaled).
    routing = from_pattern(
        {"pattern_candidate_id": "patcand-route", "scope": "global_public", "tenant_id": "acme",
         "input_fields": ("doc_type",), "label_source": "deterministic_validator",
         "distilled_from_trace_ids": ["t-route-1"], "examples": [{"trace_id": "t-route-1"}], "counterexamples": []},
        decision_kind="routing_rule", asserts_equivalence_to="scripts/parser_router.py",
        output_decision="route=ocr_worker", decision_logic={"if": {"doc_type": "scanned_pdf"}, "then": "ocr_worker"},
        fallback=FallbackPolicy(route="gateway", min_confidence=0.7), now=NOW)
    route_traces = [{"trace_id": "rt1", "scope": "global_public", "rule_applicable": True,
                     "final_decision": "ocr_worker", "inputs": {"doc_type": "scanned_pdf"}}]
    r7 = evaluate(routing, replay_report=replay(routing, route_traces, now=NOW), first_promotion=True,
                  human_review_signed=False, source_traces_scope="global_public", now=NOW)
    check("a routing rule promotes on the looser bar WITHOUT human review (risk-scaled)", r7.promoted is True)
    check("routing rule used the looser precision bar (0.95)", r7.precision_bar == 0.95)

    # determinism: same inputs → same receipt id.
    r6b = evaluate(cand, replay_report=good_replay, shadow_report=good_shadow, first_promotion=True,
                   human_review_signed=True, source_traces_scope="global_public", now=NOW)
    check("deterministic: same inputs → same receipt id", r6.receipt_id == r6b.receipt_id)
    check("receipt id has the promorcpt- prefix", r6.receipt_id.startswith("promorcpt-"))

    ok = not fails
    print("\n" + ("PASS — check_rule_promotion_gate: the gate BLOCKS a truth-serving rule with an unsafe FP, a rule "
                  "with no fallback, a rule that drops source handles, a first truth-serving promotion without human "
                  "review, and a global rule from tenant_private traces; a clean candidate promotes with a lossless "
                  "RulePromotionReceipt that preserves distilled_from_trace_ids; routing rules use a risk-scaled bar; "
                  "the gate is deterministic."
                  if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: rule promotion gate (blocks unsafe; lossless receipt).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
