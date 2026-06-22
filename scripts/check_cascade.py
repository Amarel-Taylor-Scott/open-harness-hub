#!/usr/bin/env python3
"""check_cascade — the LLM cascade's escalate-or-stop judge (FrugalGPT's scorer + stop-judger, training-free).

Proves: agreement_score reports the majority + its fraction; high ensemble agreement → STOP with the cheap answer; low
agreement → ESCALATE; run_cascade walks cheapest→strongest and stops at the first confident stage (counting escalations),
falling back honestly to the last stage when nothing clears the bar. serves_truth=false.

  python3 scripts/check_cascade.py --self-test
"""
from __future__ import annotations

from src.teleon.synthesis import cascade as C


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck("agreement_score = majority answer + its fraction", C.agreement_score(["A", "A", "A", "B"]) == {"majority": "A", "agreement": 0.75, "n": 4})
    ck("unanimous cheap ensemble -> STOP with that answer", C.should_escalate(["A", "A", "A"])["decision"] == "stop")
    split = C.should_escalate(["A", "B", "C"], threshold=0.7)
    ck("a split cheap ensemble -> ESCALATE (low agreement)", split["decision"] == "escalate" and split["answer"] is None)
    ck("agreement is the training-free confidence signal (2/3 majority clears a 0.6 bar, escalates at 0.7)",
       C.should_escalate(["A", "A", "B"], threshold=0.6)["decision"] == "stop" and C.should_escalate(["A", "A", "B"], threshold=0.7)["decision"] == "escalate")

    # full cascade: cheap stage is split (escalate) -> strong stage agrees (stop), counting one escalation
    res = C.run_cascade([
        {"name": "cheap_7b", "responses": ["A", "B", "C"]},      # split -> escalate
        {"name": "frontier", "responses": ["X", "X", "X"]},      # agrees -> stop
    ], threshold=0.7)
    ck("cascade escalates past a split cheap stage and STOPS at the confident strong stage",
       res["answer"] == "X" and res["stopped_at"] == "frontier" and res["escalations"] == 1)
    ck("cascade stops EARLY (no escalation) when the cheap stage is already confident",
       C.run_cascade([{"name": "cheap", "responses": ["A", "A", "A"]}, {"name": "frontier", "responses": ["Z"]}])["escalations"] == 0)

    # honest exhaustion: nothing clears the bar -> last stage's majority, flagged exhausted
    ex = C.run_cascade([{"name": "a", "responses": ["A", "B"]}, {"name": "b", "responses": ["C", "D"]}], threshold=0.9)
    ck("honest fallback to the last stage when nothing clears the bar (exhausted flag)", ex.get("exhausted") is True)
    ck("serves_truth=false", res["serves_truth"] is False)

    print("\n" + ("PASS - check_cascade: agreement-based stop/escalate (FrugalGPT scorer + stop-judger, training-free) — "
                  "cheap-first, escalate only on disagreement." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
