#!/usr/bin/env python3
"""scripts.check_rule_shadow_mode — proof (Determinism Factory PART 7 / ladder M6): a candidate runs in SHADOW
alongside the live authority. The shadow output is RECORDED but the live/authoritative decision is returned
UNCHANGED — shadow never serves a fact. An unsafe mismatch (a truth-serving rule that fires with the WRONG
fact) is counted and BLOCKS promotion downstream.

The live path is the EXISTING authority (injected here as a callable that returns the trace's verified
``final_decision``) — the shadow runner does NOT run reconciliation itself.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_rule_shadow_mode.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.determinism.rule_candidate_generator import FallbackPolicy, from_pattern  # noqa: E402
from src.baltor.determinism.shadow_runner import ShadowRunReport, run_shadow  # noqa: E402

NOW = "2026-06-05T00:00:00Z"


def _candidate():
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
        fallback=FallbackPolicy(route="human"), now=NOW)


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    cand = _candidate()

    # The LIVE authority callable — this is what actually serves; the shadow rule must not change it.
    def live_authority(trace):
        return trace["final_decision"]

    # AGREEING corpus: live = reg-e, shadow rule also picks reg-e → agreement, no unsafe mismatch.
    agree_traces = [
        {"trace_id": "a1", "scope": "global_public", "final_decision": "reg-e", "served_authority": "reconciliation",
         "inputs": {"conflict_type": "deadline_mismatch", "authority_a": 3, "authority_b": 1,
                    "source_a": "reg-e", "source_b": "faq"}},
        {"trace_id": "a2", "scope": "global_public", "final_decision": "reg-e", "served_authority": "reconciliation",
         "inputs": {"conflict_type": "deadline_mismatch", "authority_a": 1, "authority_b": 3,
                    "source_a": "faq", "source_b": "reg-e"}},
    ]
    rep = run_shadow(cand, agree_traces, live_decider=live_authority, now=NOW)
    check("returns a ShadowRunReport", isinstance(rep, ShadowRunReport))
    check("the live path stayed AUTHORITATIVE throughout", rep.live_authoritative is True)

    # the live decision recorded in every tick is exactly what the live authority returned (UNCHANGED).
    live_unchanged = all(t.live_decision == "reg-e" for t in rep.ticks)
    check("the LIVE decision is returned unchanged in every tick (shadow never serves)", live_unchanged)
    check("shadow agreed on both ticks", rep.agreement_count == 2 and rep.disagreement_count == 0)
    check("no unsafe mismatch on the agreeing corpus", rep.unsafe_mismatch_count == 0)
    check("agreement_rate == 1.0", rep.agreement_rate == 1.0)

    # UNSAFE-MISMATCH corpus: the live authority serves reg-e, but the rule's authority fields are inverted so
    # the shadow picks the WRONG source (faq) → a truth-serving disagreement = an unsafe mismatch.
    bad_traces = [
        {"trace_id": "b1", "scope": "global_public", "final_decision": "reg-e", "served_authority": "reconciliation",
         "inputs": {"conflict_type": "deadline_mismatch", "authority_a": 3, "authority_b": 1,
                    "source_a": "faq", "source_b": "reg-e"}},  # higher-auth side names faq → shadow picks faq (wrong)
    ]
    bad = run_shadow(cand, bad_traces, live_decider=live_authority, now=NOW)
    check("a truth-serving disagreement IS an unsafe mismatch", bad.unsafe_mismatch_count == 1,
          str(bad.unsafe_mismatch_count))
    check("the LIVE decision is STILL unchanged on an unsafe-mismatch tick (shadow never overrode it)",
          bad.ticks[0].live_decision == "reg-e")
    check("the disagreement is recorded but the rule did NOT serve",
          bad.disagreement_count == 1 and bad.ticks[0].shadow_decision == "faq" and bad.live_authoritative)

    # ABSTAIN corpus: equal authority → shadow abstains; no agreement, no disagreement, no unsafe.
    abst_traces = [
        {"trace_id": "c1", "scope": "global_public", "final_decision": "needs_human", "served_authority": "reconciliation",
         "inputs": {"conflict_type": "deadline_mismatch", "authority_a": 2, "authority_b": 2,
                    "source_a": "faq", "source_b": "blog"}},
    ]
    abst = run_shadow(cand, abst_traces, live_decider=live_authority, now=NOW)
    check("shadow abstains on equal authority (no unsafe mismatch)",
          abst.abstain_count == 1 and abst.unsafe_mismatch_count == 0 and abst.shadow_fired_count == 0)

    # the runner can also read final_decision directly when no live_decider is injected (still non-authoritative).
    rep_no_decider = run_shadow(cand, agree_traces, now=NOW)
    check("works without an injected decider (reads the already-served final_decision)",
          rep_no_decider.agreement_count == 2 and rep_no_decider.live_authoritative)

    # determinism: same inputs → same report id.
    check("deterministic: same corpus → same report id",
          rep.report_id == run_shadow(cand, agree_traces, live_decider=live_authority, now=NOW).report_id)
    check("report id has the shadow- prefix", rep.report_id.startswith("shadow-"))

    ok = not fails
    print("\n" + ("PASS — check_rule_shadow_mode: a candidate runs in shadow next to the live authority; the live "
                  "decision is returned unchanged in every tick (shadow never serves); agreement/disagreement/"
                  "abstention are recorded; a truth-serving disagreement is an unsafe mismatch that will block "
                  "promotion; shadow is deterministic."
                  if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: rule shadow mode (recorded, non-authoritative; unsafe blocks).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
