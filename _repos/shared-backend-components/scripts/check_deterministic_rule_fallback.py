#!/usr/bin/env python3
"""scripts.check_deterministic_rule_fallback — proof (Determinism Factory PART 9 / ladder M7 serving): an
ACTIVE rule serves deterministically-first; a low-confidence / unknown / out-of-distribution input falls back
to gateway / human / hold-out; every decision is RECORDED; and a fallback NEVER fabricates a fact.

Cases proven:
  * an active rule firing confidently on an in-distribution input serves DETERMINISTICALLY (authoritative);
  * an INACTIVE (un-promoted) rule never serves — straight to fallback;
  * an OUT-OF-DISTRIBUTION input (missing a required field) falls back;
  * a BELOW-min-confidence input falls back;
  * an input the rule ABSTAINS on (preconditions don't fire) falls back;
  * every routing event is recorded with a reason, and NO fallback ever fabricates a fact.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_deterministic_rule_fallback.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.determinism.fallback_router import (  # noqa: E402
    REASON_ABSTAINED,
    REASON_INACTIVE,
    REASON_LOW_CONFIDENCE,
    REASON_OOD,
    REASON_RULE_FIRED,
    SERVED_BY_GATEWAY,
    SERVED_BY_HUMAN,
    SERVED_BY_RULE,
    RoutingEvent,
    activate,
    route,
)
from src.baltor.determinism.rule_candidate_generator import FallbackPolicy, from_pattern  # noqa: E402
from src.baltor.determinism.rule_promotion_gate import RulePromotionReceipt  # noqa: E402

NOW = "2026-06-05T00:00:00Z"


def _candidate(route_to="human", min_conf=1.0):
    pattern = {
        "pattern_candidate_id": "patcand-cfpb-deadline", "scope": "global_public", "tenant_id": "acme",
        "input_fields": ("conflict_type", "authority_a", "authority_b", "source_a", "source_b"),
        "label_source": "authority_or_policy", "distilled_from_trace_ids": ["trace-rege-1"],
        "examples": [{"trace_id": "trace-rege-1", "source_handle": "ctx://cfpb/reg-e#deadline"}],
        "counterexamples": [],
    }
    return from_pattern(
        pattern, decision_kind="reconciliation_policy_rule",
        asserts_equivalence_to="scripts/artifact_graph/reconciliation.py::reconcile",
        output_decision="winner=higher_authority_source",
        decision_logic={"if": {"conflict_type": "deadline_mismatch", "higher_authority_wins": True},
                        "then": "higher_authority_source"},
        fallback=FallbackPolicy(route=route_to, min_confidence=min_conf), now=NOW)


_IN_DIST = {"conflict_type": "deadline_mismatch", "authority_a": 3, "authority_b": 1,
            "source_a": "reg-e", "source_b": "faq"}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    cand = _candidate()

    # an un-promoted candidate is NOT active → activation requires a promoted receipt.
    raised = False
    try:
        activate(cand, RulePromotionReceipt(receipt_id="x", rule_candidate_id=cand.rule_candidate_id,
                                            promoted=False, decision="block", truth_serving=True, precision_bar=1.0,
                                            checks=[], blocked_reasons=["x"], replay_report_id="", shadow_report_id="",
                                            distilled_from_trace_ids=[], pattern_candidate_id="", human_review_signed=False))
    except ValueError:
        raised = True
    check("activation REQUIRES a promoted receipt (a blocked receipt cannot activate)", raised)

    # ── INACTIVE rule: never serves, straight to fallback ─────────────────────────────────────────
    ev_inactive = route(cand, _IN_DIST, confidence=1.0, now=NOW)
    check("an INACTIVE rule never serves — it falls back", ev_inactive.fell_back is True)
    check("inactive fallback reason is rule_inactive", ev_inactive.reason == REASON_INACTIVE)
    check("inactive fallback is NOT authoritative", ev_inactive.is_authoritative is False)

    # promote → activate the rule for serving.
    promoted = RulePromotionReceipt(receipt_id="promorcpt-ok", rule_candidate_id=cand.rule_candidate_id,
                                    promoted=True, decision="promote", truth_serving=True, precision_bar=1.0,
                                    checks=[], blocked_reasons=[], replay_report_id="r", shadow_report_id="s",
                                    distilled_from_trace_ids=["trace-rege-1"], pattern_candidate_id="patcand-cfpb-deadline",
                                    human_review_signed=True)
    active = activate(cand, promoted)
    check("activate returns an ACTIVE rule after a promoted receipt", active.active is True and active.status == "active")

    # ── DETERMINISTIC-FIRST: an active rule firing confidently on an in-distribution input serves the rule ──
    ev_rule = route(active, _IN_DIST, confidence=1.0, now=NOW)
    check("active rule serves DETERMINISTICALLY on an in-distribution input", ev_rule.served_by == SERVED_BY_RULE)
    check("the deterministic serve IS authoritative", ev_rule.is_authoritative is True)
    check("the deterministic serve did NOT fall back", ev_rule.fell_back is False and ev_rule.reason == REASON_RULE_FIRED)
    check("the deterministic serve picked the higher-authority source (reg-e)", ev_rule.decision == "reg-e")

    # ── OUT-OF-DISTRIBUTION: a required field is missing → fallback ────────────────────────────────
    ood_input = {"conflict_type": "deadline_mismatch", "authority_a": 3}  # missing authority_b/source_a/source_b
    ev_ood = route(active, ood_input, confidence=1.0, now=NOW)
    check("an OOD input (missing required field) falls back", ev_ood.fell_back is True and ev_ood.reason == REASON_OOD)
    check("the OOD fallback routes to the policy route (human)", ev_ood.served_by == SERVED_BY_HUMAN)
    check("the OOD fallback is NOT authoritative and serves NO decision",
          ev_ood.is_authoritative is False and ev_ood.decision is None)

    # ── LOW CONFIDENCE: below min_confidence → fallback ───────────────────────────────────────────
    ev_low = route(active, _IN_DIST, confidence=0.5, now=NOW)  # policy min_confidence is 1.0
    check("a below-min-confidence input falls back", ev_low.fell_back is True and ev_low.reason == REASON_LOW_CONFIDENCE)

    # ── ABSTAIN: equal authority → rule preconditions don't fire → fallback ────────────────────────
    abst_input = {"conflict_type": "deadline_mismatch", "authority_a": 2, "authority_b": 2,
                  "source_a": "faq", "source_b": "blog"}
    ev_abst = route(active, abst_input, confidence=1.0, now=NOW)
    check("an input the rule abstains on falls back", ev_abst.fell_back is True and ev_abst.reason == REASON_ABSTAINED)

    # ── a gateway-routed fallback re-proposes (proposal, not authoritative) ────────────────────────
    cand_gw = _candidate(route_to="gateway", min_conf=0.9)
    active_gw = activate(cand_gw, promoted)
    ev_gw = route(active_gw, _IN_DIST, confidence=0.5, now=NOW)
    check("a gateway fallback routes to the LLM gateway", ev_gw.served_by == SERVED_BY_GATEWAY)
    check("the gateway fallback is a PROPOSAL — not authoritative", ev_gw.is_authoritative is False)

    # ── INVARIANT: NO fallback EVER fabricates a fact ─────────────────────────────────────────────
    all_events = [ev_inactive, ev_rule, ev_ood, ev_low, ev_abst, ev_gw]
    check("EVERY routing event is a RoutingEvent", all(isinstance(e, RoutingEvent) for e in all_events))
    check("NO event ever fabricates a fact (fabricated is always False)",
          all(e.fabricated is False for e in all_events))
    check("every FALLBACK serves NO authoritative decision (no invented fact)",
          all(e.decision is None and not e.is_authoritative for e in all_events if e.fell_back))
    check("ONLY the deterministic rule serve is authoritative",
          sum(1 for e in all_events if e.is_authoritative) == 1 and ev_rule.is_authoritative)

    # determinism: same input → same event id.
    check("deterministic: same input → same event id",
          ev_rule.event_id == route(active, _IN_DIST, confidence=1.0, now=NOW).event_id)
    check("event id has the route- prefix", ev_rule.event_id.startswith("route-"))

    ok = not fails
    print("\n" + ("PASS — check_deterministic_rule_fallback: an active rule serves deterministically-first on an "
                  "in-distribution input; inactive / OOD / low-confidence / abstaining inputs fall back to "
                  "gateway/human/hold-out; every decision is recorded; only the deterministic serve is "
                  "authoritative; NO fallback ever fabricates a fact; routing is deterministic."
                  if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: deterministic rule fallback (rule-first, recorded, never fabricates).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
