#!/usr/bin/env python3
"""scripts.check_rule_candidate_generation — proof (Determinism Factory PART 5): a mined VERIFIED pattern
becomes a PROPOSED (never active) RuleCandidate that carries scope / examples / counterexamples / fallback /
distilled_from_trace_ids — and a pattern whose label came from consensus ALONE (or that has no verified
traces) CANNOT mint a rule.

The pattern fixture is the canonical CFPB reconciliation shape (Reg-E "10 business days" beats FAQ "30 days"),
labelled by the EXISTING deterministic authority (NOT by consensus). The generated candidate asserts-
equivalence to that existing reconciliation reference — it reproduces, never replaces.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_rule_candidate_generation.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.determinism.rule_candidate_generator import (  # noqa: E402
    LABEL_AUTHORITY,
    LABEL_CONSENSUS_ONLY,
    ConsensusOnlyError,
    FallbackPolicy,
    NoVerifiedTraceError,
    RuleCandidate,
    from_pattern,
)

NOW = "2026-06-05T00:00:00Z"


def _verified_pattern(label_source: str = LABEL_AUTHORITY, trace_ids=("trace-rege-1", "trace-rege-2")) -> dict:
    """A mined PatternCandidate (duck-typed dict) for the CFPB deadline-mismatch shape, VERIFIED by the
    existing reconciliation authority. Examples carry source handles; the FAQ-30 is a held-out counterexample."""
    return {
        "pattern_candidate_id": "patcand-cfpb-deadline",
        "scope": "global_public",
        "tenant_id": "acme",
        "input_fields": ("conflict_type", "authority_a", "authority_b", "source_a", "source_b"),
        "label_source": label_source,
        "distilled_from_trace_ids": list(trace_ids),
        "examples": [
            {"trace_id": "trace-rege-1", "conflict_type": "deadline_mismatch", "authority_a": 3,
             "authority_b": 1, "source_a": "reg-e", "source_b": "faq",
             "final_decision": "reg-e", "source_handle": "ctx://cfpb/reg-e#deadline"},
        ],
        "counterexamples": [
            {"trace_id": "trace-faq-held", "conflict_type": "deadline_mismatch", "authority_a": 1,
             "authority_b": 3, "source_a": "faq", "source_b": "reg-e",
             "final_decision": "reg-e", "source_handle": "ctx://cfpb/faq#deadline"},
        ],
    }


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    pattern = _verified_pattern()
    cand = from_pattern(
        pattern, decision_kind="reconciliation_policy_rule",
        asserts_equivalence_to="scripts/artifact_graph/reconciliation.py::reconcile",
        output_decision="winner=higher_authority_source; loser=held_out",
        decision_logic={"if": {"conflict_type": "deadline_mismatch", "higher_authority_wins": True},
                        "then": "higher_authority_source"},
        fallback=FallbackPolicy(route="human", min_confidence=1.0),
        expected_failure_modes=("equal authority → abstain", "missing authority field → abstain"),
        now=NOW)

    # 1) it IS a RuleCandidate and is PROPOSED, NOT active.
    check("returns a RuleCandidate", isinstance(cand, RuleCandidate))
    check("candidate is proposed, NOT active", cand.status == "proposed" and cand.active is False)

    # 2) carries scope / examples / counterexamples / fallback / distilled_from_trace_ids.
    check("carries scope", cand.scope == "global_public")
    check("carries examples", len(cand.examples) == 1)
    check("carries counterexamples (the held-out FAQ-30 negative)", len(cand.counterexamples) == 1)
    check("carries a fallback policy", cand.fallback is not None and cand.fallback.route == "human")
    check("carries distilled_from_trace_ids (lossless link-back)",
          tuple(cand.distilled_from_trace_ids) == ("trace-rege-1", "trace-rege-2"))
    check("carries the source PatternCandidate id", cand.pattern_candidate_id == "patcand-cfpb-deadline")

    # 3) it ASSERTS-EQUIVALENCE to the EXISTING authority — it does not name a new one.
    check("asserts-equivalence to the EXISTING reconciliation authority",
          "reconciliation.py" in cand.asserts_equivalence_to)
    check("is marked truth-serving (a reconciliation rule selects a fact)", cand.truth_serving is True)
    check("label_source is a real producer (authority), not consensus", cand.label_source == LABEL_AUTHORITY)

    # 4) determinism: same pattern → same candidate id, byte-stable.
    cand2 = from_pattern(
        pattern, decision_kind="reconciliation_policy_rule",
        asserts_equivalence_to="scripts/artifact_graph/reconciliation.py::reconcile",
        output_decision="winner=higher_authority_source; loser=held_out",
        decision_logic={"if": {"conflict_type": "deadline_mismatch", "higher_authority_wins": True},
                        "then": "higher_authority_source"},
        fallback=FallbackPolicy(route="human", min_confidence=1.0), now=NOW)
    check("deterministic: same pattern → same candidate id", cand.rule_candidate_id == cand2.rule_candidate_id)
    check("candidate id has the rulecand- prefix", cand.rule_candidate_id.startswith("rulecand-"))

    # 5) SAFETY: a pattern labelled by CONSENSUS ALONE cannot mint a rule.
    consensus_only = _verified_pattern(label_source=LABEL_CONSENSUS_ONLY)
    raised = False
    try:
        from_pattern(consensus_only, decision_kind="reconciliation_policy_rule",
                     asserts_equivalence_to="x", output_decision="y",
                     decision_logic={"if": {}, "then": "z"}, now=NOW)
    except ConsensusOnlyError:
        raised = True
    check("consensus-ONLY pattern is REJECTED (consensus is evidence, not truth)", raised)

    # 6) SAFETY: a pattern with NO verified traces cannot mint a rule (nothing to link back to losslessly).
    no_traces = _verified_pattern(trace_ids=())
    raised2 = False
    try:
        from_pattern(no_traces, decision_kind="reconciliation_policy_rule",
                     asserts_equivalence_to="x", output_decision="y",
                     decision_logic={"if": {}, "then": "z"}, now=NOW)
    except NoVerifiedTraceError:
        raised2 = True
    check("pattern with NO verified traces is REJECTED (nothing lossless to link back to)", raised2)

    # 7) a routing rule is NOT truth-serving (risk axis differs).
    routing_pat = dict(pattern, pattern_candidate_id="patcand-route", input_fields=("doc_type",))
    routing = from_pattern(routing_pat, decision_kind="routing_rule",
                           asserts_equivalence_to="scripts/parser_router.py",
                           output_decision="route=ocr_worker",
                           decision_logic={"if": {"doc_type": "scanned_pdf"}, "then": "ocr_worker"},
                           fallback=FallbackPolicy(route="gateway", min_confidence=0.7), now=NOW)
    check("a routing rule is NOT truth-serving (lower-risk axis)", routing.truth_serving is False)

    # 8) to_dict round-trips the safety-critical fields.
    d = cand.to_dict()
    check("to_dict preserves distilled_from_trace_ids + status + active",
          d["distilled_from_trace_ids"] == ["trace-rege-1", "trace-rege-2"]
          and d["status"] == "proposed" and d["active"] is False)

    ok = not fails
    print("\n" + ("PASS — check_rule_candidate_generation: a VERIFIED pattern becomes a PROPOSED (never active) "
                  "RuleCandidate carrying scope/examples/counterexamples/fallback/distilled_from_trace_ids and "
                  "asserting-equivalence to the EXISTING reconciliation authority; consensus-only and trace-less "
                  "patterns are rejected; generation is deterministic."
                  if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: rule candidate generation (proposed, lossless, consensus-safe).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
