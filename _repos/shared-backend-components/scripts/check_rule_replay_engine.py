#!/usr/bin/env python3
"""scripts.check_rule_replay_engine — proof (Determinism Factory PART 6): replay a RuleCandidate against a
corpus of historical VERIFIED traces and compute precision / recall / FP / FN / abstention / unsafe / tenant-
leak against the verified final decisions.

The corpus is the CFPB deadline shape: VERIFIED traces where the existing authority ruled "reg-e" (the 10-day
reference), an equal-authority trace where a correct rule MUST abstain, a tenant_private trace (a global rule
applied to it is a LEAK), and a WRONG-winner case used to prove the unsafe-FP counter actually fires.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_rule_replay_engine.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.determinism.replay_engine import RuleReplayReport, replay  # noqa: E402
from src.baltor.determinism.rule_candidate_generator import FallbackPolicy, from_pattern  # noqa: E402

NOW = "2026-06-05T00:00:00Z"


def _candidate():
    pattern = {
        "pattern_candidate_id": "patcand-cfpb-deadline", "scope": "global_public", "tenant_id": "acme",
        "input_fields": ("conflict_type", "authority_a", "authority_b", "source_a", "source_b"),
        "label_source": "authority_or_policy", "distilled_from_trace_ids": ["trace-rege-1"],
        "examples": [{"trace_id": "trace-rege-1", "source_handle": "ctx://cfpb/reg-e#deadline"}],
        "counterexamples": [{"trace_id": "trace-faq-held", "source_handle": "ctx://cfpb/faq#deadline"}],
    }
    return from_pattern(
        pattern, decision_kind="reconciliation_policy_rule",
        asserts_equivalence_to="scripts/artifact_graph/reconciliation.py::reconcile",
        output_decision="winner=higher_authority_source",
        decision_logic={"if": {"conflict_type": "deadline_mismatch", "higher_authority_wins": True},
                        "then": "higher_authority_source"},
        fallback=FallbackPolicy(route="human"), now=NOW)


def _traces() -> list:
    """Historical VERIFIED traces. ``final_decision`` is the truth (produced by the EXISTING authority)."""
    return [
        # reg-e (auth 3) vs faq (auth 1): rule fires, picks reg-e → MATCHES the verified reference. TP.
        {"trace_id": "t1", "scope": "global_public", "rule_applicable": True, "final_decision": "reg-e",
         "inputs": {"conflict_type": "deadline_mismatch", "authority_a": 3, "authority_b": 1,
                    "source_a": "reg-e", "source_b": "faq"}},
        # faq (auth 1) vs reg-e (auth 3): higher authority is side b → rule picks reg-e. TP.
        {"trace_id": "t2", "scope": "global_public", "rule_applicable": True, "final_decision": "reg-e",
         "inputs": {"conflict_type": "deadline_mismatch", "authority_a": 1, "authority_b": 3,
                    "source_a": "faq", "source_b": "reg-e"}},
        # EQUAL authority: rule MUST abstain (cannot deterministically pick). rule_applicable=False → not a FN.
        {"trace_id": "t3", "scope": "global_public", "rule_applicable": False, "final_decision": "needs_human",
         "inputs": {"conflict_type": "deadline_mismatch", "authority_a": 2, "authority_b": 2,
                    "source_a": "faq", "source_b": "blog"}},
        # different conflict_type: rule does NOT fire; a correct rule should NOT fire here either → not a FN.
        {"trace_id": "t4", "scope": "global_public", "rule_applicable": False, "final_decision": "resolved",
         "inputs": {"conflict_type": "amount_mismatch", "authority_a": 3, "authority_b": 1,
                    "source_a": "x", "source_b": "y"}},
    ]


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    cand = _candidate()
    report = replay(cand, _traces(), now=NOW)

    # 1) it is a RuleReplayReport scored over the corpus.
    check("returns a RuleReplayReport", isinstance(report, RuleReplayReport))
    check("scored over the whole corpus", report.trace_count == 4)

    # 2) clean reproduction of the reference: 2 TP, 0 FP, perfect precision, no unsafe, no leak.
    check("true positives == 2 (both deadline conflicts resolved to reg-e)", report.true_positives == 2,
          str(report.true_positives))
    check("false positives == 0", report.false_positives == 0, str(report.false_positives))
    check("precision == 1.0 (clean reproduction of the reference)", report.precision == 1.0, str(report.precision))
    check("unsafe_count == 0 on a clean truth-serving replay", report.unsafe_count == 0)
    check("tenant_leak_count == 0 (no tenant_private trace in this corpus)", report.tenant_leak_count == 0)

    # 3) abstention is correct, not a false negative (rule_applicable=False on the abstained traces).
    check("abstentions == 2 (equal-authority + different conflict_type)", report.abstentions == 2,
          str(report.abstentions))
    check("false negatives == 0 (abstentions were on non-applicable traces)", report.false_negatives == 0,
          str(report.false_negatives))
    check("recall == 1.0 (caught every applicable case)", report.recall == 1.0, str(report.recall))

    # 4) UNSAFE counter actually fires: a corpus where the verified truth is reg-e but the rule's authority
    #    fields are inverted such that the rule would pick the WRONG source → a truth-serving FALSE POSITIVE.
    wrong = [{"trace_id": "tw", "scope": "global_public", "rule_applicable": True, "final_decision": "reg-e",
              "inputs": {"conflict_type": "deadline_mismatch", "authority_a": 3, "authority_b": 1,
                         "source_a": "faq", "source_b": "reg-e"}}]  # higher authority side names FAQ → wrong winner
    bad_report = replay(cand, wrong, now=NOW)
    check("unsafe_count > 0 when a truth-serving rule emits the WRONG winner", bad_report.unsafe_count == 1,
          str(bad_report.unsafe_count))
    check("the wrong winner is a false positive", bad_report.false_positives == 1)
    check("precision < 1.0 when the rule is wrong", bad_report.precision < 1.0)

    # 5) TENANT-LEAK counter fires: a global rule replayed over a tenant_private trace is a leak.
    private = [{"trace_id": "tp", "scope": "tenant_private", "rule_applicable": True, "final_decision": "reg-e",
                "inputs": {"conflict_type": "deadline_mismatch", "authority_a": 3, "authority_b": 1,
                           "source_a": "reg-e", "source_b": "faq"}}]
    leak_report = replay(cand, private, now=NOW)
    check("tenant_leak_count > 0 when a global rule touches tenant_private data", leak_report.tenant_leak_count == 1,
          str(leak_report.tenant_leak_count))

    # 6) FALSE-NEGATIVE counter fires: an applicable trace the rule misses.
    miss = [{"trace_id": "tm", "scope": "global_public", "rule_applicable": True, "final_decision": "reg-e",
             "inputs": {"conflict_type": "deadline_mismatch", "authority_a": 2, "authority_b": 2,
                        "source_a": "reg-e", "source_b": "faq"}}]  # equal authority → rule abstains, but it WAS applicable
    miss_report = replay(cand, miss, now=NOW)
    check("false negatives > 0 when the rule misses an applicable trace", miss_report.false_negatives == 1,
          str(miss_report.false_negatives))

    # 7) determinism: same inputs → same report id.
    check("deterministic: same corpus → same report id", report.report_id == replay(cand, _traces(), now=NOW).report_id)
    check("report id has the replay- prefix", report.report_id.startswith("replay-"))

    ok = not fails
    print("\n" + ("PASS — check_rule_replay_engine: replaying a candidate over historical VERIFIED traces cleanly "
                  "reproduces the reference (precision/recall 1.0, 0 unsafe, 0 leak); the unsafe-FP, tenant-leak and "
                  "false-negative counters all fire on the adversarial corpora; replay is deterministic."
                  if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: rule replay engine (precision/recall/unsafe/tenant-leak).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
