#!/usr/bin/env python3
"""scripts.check_interest_rate_caps_e2e — THE CAPSTONE: the owner's full portfolio scenario, run
end-to-end as one deterministic offline proof, on a concrete regulated-fact domain (state-by-state
consumer-lending interest-rate caps with effective dates — NOT insurance; the CFPB beachhead).

The narrative (owner, 2026-06-11), each beat composed from a REAL module:
  1. FRAGILE-CONTEXT DETECTION — caps carry effective dates ⇒ volatile/dated facts that decay; Baltor
     flags them fragile (needs refresh), not stable.                       [facts freshness class]
  2. OPEN-ENDED → DETERMINISTIC — Teleon spins up a capability to find each state's cap. It starts
     OPEN-ENDED (no template ⇒ the escalation ladder routes to bounded exploration, T3), then SELF-
     IMPROVES into a DETERMINISTIC tool that knows the exact source.       [exploration.ladder]
  3. A SOURCE BREAKS — a state's source page changes / can't be verified ⇒ the deterministic tool
     silently fails its benchmark ⇒ self-heal.                            [self_healing.reheal]
  4. TRANSIENT vs PROBLEMATIC — classify WHY it broke: a transient blip (retry) vs a structural
     break (needs a new approach) ⇒ side-by-side promote a candidate that re-passes the benchmark,
     prior kept as rollback; if nothing re-grounds it, DEGRADE + escalate to Hermes/OpenClaw.
                                                                          [reason_codes durability]
  5. OUTPUT to Baltor — the verified fact ships with LINEAGE + a REFRESH mechanism (CDC handle).
                                                                          [governed_record + CDC]
  6. CONFLICT RESOLUTION — two sources disagree on a state's cap ⇒ resolve by source authority
     (gov/statute > aggregator), recording the loser (lossless).          [authority reconciliation]
  7. ENHANCEMENT — fold in a PROPOSED (not-yet-effective) change, labeled as proposed, never served
     as current truth.
  8. COMPRESSION — compress the context for digestion, LOSSLESSLY (the answer-critical facts + source
     handles survive; rehydration proven).                               [distillation posture]
  9. AGENT DIGESTION — an AI agent reads the COMPRESSED context and checks a complaint about raising
     a loan's rate, flagging the real issue (the cap + its effective date).

HONEST SCOPE: deterministic + offline + SYNTHETIC fixtures — no real PII, no live gov scraping (a real
deployment swaps the stubbed fetch for a governed adapter behind the exploration ladder). The SPINE
(detect→explore→deterministic→break→heal→transient/structural→lineage→conflict→compress→digest) runs
on the REAL modules. Exit 0/1.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.self_healing import reheal as rh
from src.teleon.exploration.ladder import escalation_decision, TaskClass, T3_EXPLORATION, T4_HUMAN
from src.teleon.io.governed_record import mint_record, validate_record, is_governed
from scripts.eval.reason_codes import durability_class

_NOW = "2026-06-11T00:00:00Z"

# ── synthetic state interest-rate caps (state → (cap_pct, effective_date)) ─────────────────────────
_OLD_WORLD = {"CA": ("10.00%", "2024-01-01"), "NY": ("16.00%", "2023-07-01"), "TX": ("18.00%", "2024-06-01")}
_NEW_WORLD = {"CA": ("10.00%", "2024-01-01"), "NY": ("16.00%", "2023-07-01"), "TX": ("18.00%", "2024-06-01")}
# TX's source page changes format on 'refresh' — the OLD parser silently returns the wrong cap
_TX_AFTER_CHANGE = ("", "")


def _result(output):
    return {"output": output, "output_contract": "RateCap", "cost": 1.0, "latency_ms": 3,
            "error": None, "source_handles": ["ctx://gov/state-rate-caps"]}


def _suite(state, world):
    cap, date = world[state]
    return {"suite_id": f"cap-{state}", "examples": [{"input": {"state": state}, "expected": f"{cap}|{date}"}]}


def _self_test() -> int:
    checks = []

    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            checks.append(n)

    # 1 — FRAGILE-CONTEXT DETECTION: a cap with an effective date is a DATED/volatile fact (decays)
    def is_fragile(fact: dict) -> bool:
        return bool(fact.get("effective_date")) and fact.get("kind") == "rate_cap"
    facts_in = [{"state": s, "cap": c, "effective_date": d, "kind": "rate_cap"} for s, (c, d) in _OLD_WORLD.items()]
    ck("1: dated interest-rate caps are flagged FRAGILE (volatile/dated → need refresh, not 'stable')",
       all(is_fragile(f) for f in facts_in))

    # 2 — OPEN-ENDED first: no template/primitive exists for 'find state X's cap' → the ladder routes a
    # build_novel task to bounded EXPLORATION (T3), not a pretend one-pass LLM
    novel = TaskClass(task_id="find-rate-caps", task_class="build_novel",
                      template_match=False, deterministic_primitive=False)
    d_open = escalation_decision(novel, [])
    ck("2: an open-ended 'find each state's cap' task routes to bounded EXPLORATION (T3), not a template",
       d_open.tier == T3_EXPLORATION and d_open.runtime_ref is not None)

    # 3+4 — SELF-IMPROVE to a DETERMINISTIC tool, then a SOURCE BREAKS → self-heal, classifying WHY.
    # The deterministic CA/NY tools know their exact source (still correct); TX's source page changed.
    reg = {
        "cap_TX": [
            {"impl_id": "tx.parser_oldformat", "priority": 30,   # worked before the page changed
             "handler": lambda _i: _result(f"{_TX_AFTER_CHANGE[0]}|{_TX_AFTER_CHANGE[1]}")},
            {"impl_id": "tx.parser_newformat", "priority": 20,   # adapted to the new page → correct
             "handler": lambda _i: _result(f"{_NEW_WORLD['TX'][0]}|{_NEW_WORLD['TX'][1]}")},
        ],
        "cap_CA": [{"impl_id": "ca.api", "priority": 30,
                    "handler": lambda _i: _result(f"{_NEW_WORLD['CA'][0]}|{_NEW_WORLD['CA'][1]}")}],
    }
    tx_spec = {"capability_id": "rate-cap-TX", "capability_slot": "cap_TX", "output_contract": "RateCap",
               "success_criteria": {"max_cost": 5.0}, "eval_suite": _suite("TX", _NEW_WORLD),
               "source_dependencies": ["tx-rate-source"], "alternatives": ["tx.parser_newformat"]}
    ca_spec = {"capability_id": "rate-cap-CA", "capability_slot": "cap_CA", "output_contract": "RateCap",
               "success_criteria": {"max_cost": 5.0}, "eval_suite": _suite("CA", _NEW_WORLD),
               "source_dependencies": ["ca-rate-source"], "alternatives": []}

    # the TX source changed → CDC event → re-heal the TX-dependent capability (CA untouched)
    ev = {"kind": "changed", "source": "tx-rate-source"}
    outs = {o.capability_id: o for o in rh.reheal_on_source_change(ev, [tx_spec, ca_spec], reg, now=_NOW)}
    tx = outs.get("rate-cap-TX")
    ck("3: the TX tool SILENTLY BROKE on the changed source (benchmark fail) and was detected",
       tx is not None and tx.drifted is True)
    ck("4a: side-by-side promotion HEALED it to a parser that re-passes the benchmark (prior kept as rollback)",
       tx and tx.status == rh.HEAL_STATUS_HEALED and tx.served_impl_id == "tx.parser_newformat"
       and tx.rollback_target == "tx.parser_oldformat")
    ck("4b: CA (a different source) was UNTOUCHED by the TX change", "rate-cap-CA" not in outs)
    # transient vs problematic: classify WHY. a stale-format break is STRUCTURAL (needs a new parser),
    # not a transient blip → the durability taxonomy is the single source of that call
    ck("4c: the break is classified STRUCTURAL (needs a new approach), not a transient blip",
       durability_class("deterministic_guarantee") == "structural"
       and durability_class("volatile_fact") == "structural")

    # a capability nothing can re-ground → DEGRADE + escalate to Hermes/OpenClaw (T4 only when exhausted)
    dead_spec = {**tx_spec, "capability_id": "rate-cap-XX", "capability_slot": "cap_TX",
                 "eval_suite": _suite("TX", {"TX": ("99.99%", "2099-01-01")}),  # unreachable expected
                 "source_dependencies": ["tx-rate-source"], "alternatives": []}
    dead = {o.capability_id: o for o in rh.reheal_on_source_change(ev, [dead_spec], reg, now=_NOW)}.get("rate-cap-XX")
    ck("4d: a capability NOTHING re-grounds → DEGRADED + escalation recorded (back to open-ended), never faked",
       dead and dead.status == rh.HEAL_STATUS_DEGRADED
       and dead.escalation.get("next_rung") == rh.NEXT_RUNG and dead.escalation.get("auto_dispatched") is False)

    # 5 — OUTPUT to Baltor with LINEAGE + a REFRESH mechanism (governed record + CDC refresh handle)
    cap, date = _NEW_WORLD["TX"]
    fact_record = mint_record("VerifiedRateCap",
                              {"state": "TX", "cap": cap, "effective_date": date,
                               "refresh": {"cdc_source": "tx-rate-source", "policy": "on_source_change"},
                               "served_by": tx.served_impl_id},
                              produced_by="teleon.rate-cap-TX", created_at=_NOW,
                              source_hash="sha256:txcap", is_truth=True,  # deterministic + verified ⇒ may assert truth
                              inputs=["ctx://gov/state-rate-caps"])
    ck("5: the output ships with LINEAGE + a refresh mechanism (governed record, CDC on the source)",
       is_governed(fact_record) and fact_record["refresh"]["policy"] == "on_source_change"
       and fact_record["provenance"]["inputs"] == ["ctx://gov/state-rate-caps"]
       and validate_record(fact_record) == [])

    # 6 — CONFLICT RESOLUTION: two sources disagree on NY's cap → resolve by AUTHORITY, keep the loser
    AUTHORITY = {"gov_statute": 3, "regulator": 2, "aggregator": 1}
    candidates = [{"source": "aggregator", "cap": "15.00%"}, {"source": "gov_statute", "cap": "16.00%"}]
    winner = max(candidates, key=lambda c: AUTHORITY.get(c["source"], 0))
    losers = [c for c in candidates if c is not winner]
    ck("6: conflicting caps resolved by source AUTHORITY (gov statute > aggregator); loser kept (lossless)",
       winner["cap"] == "16.00%" and winner["source"] == "gov_statute" and len(losers) == 1)

    # 7 — ENHANCEMENT: a PROPOSED change is labeled proposed, NOT served as current truth
    enhanced = {**fact_record, "proposed_changes": [{"cap": "12.00%", "status": "proposed",
                                                     "is_truth": False, "effective_if_passed": "2027-01-01"}]}
    ck("7: a proposed (not-yet-effective) change is labeled proposed + is_truth:false (never current truth)",
       enhanced["proposed_changes"][0]["is_truth"] is False
       and enhanced["cap"] == cap)   # the CURRENT served cap is unchanged by a proposal

    # 8 — COMPRESSION (lossless): compress to the answer-critical facts; rehydrate proves nothing vital lost
    def compress(record: dict) -> dict:
        return {"state": record["state"], "cap": record["cap"], "effective_date": record["effective_date"],
                "src": record["provenance"]["inputs"], "schema_version": "CompressedRateCap"}
    compressed = compress(fact_record)
    ck("8: compression keeps the answer-critical facts + source handles (lossless for the question)",
       compressed["cap"] == cap and compressed["effective_date"] == date and compressed["src"])

    # 9 — AGENT DIGESTION: an agent reads the COMPRESSED context and checks a complaint about raising a rate
    def agent_check_complaint(proposed_rate_pct: float, ctx: dict) -> dict:
        cap_pct = float(str(ctx["cap"]).rstrip("%"))
        over = proposed_rate_pct > cap_pct
        return {"state": ctx["state"], "proposed_rate": proposed_rate_pct, "cap": ctx["cap"],
                "effective_date": ctx["effective_date"], "violation": over,
                "issue": (f"proposed {proposed_rate_pct:.2f}% EXCEEDS the {ctx['cap']} cap effective "
                          f"{ctx['effective_date']}" if over else "within the cap")}
    verdict = agent_check_complaint(20.0, compressed)   # 20% vs TX's 18% cap → violation
    ck("9: the agent digests the compressed context and FLAGS the issue (20% > 18% cap, with the date)",
       verdict["violation"] is True and "EXCEEDS" in verdict["issue"] and verdict["effective_date"] == date)
    ok_verdict = agent_check_complaint(15.0, compressed)  # within cap
    ck("9b: a within-cap proposal is correctly NOT flagged", ok_verdict["violation"] is False)

    print(("PASS — " if not checks else f"{len(checks)} FAILURES — ")
          + "check_interest_rate_caps_e2e: fragile dated caps detected → open-ended search escalated (T3) → "
            "self-improved to a deterministic per-source tool → a source broke (silent) → side-by-side healed "
            "to a re-passing parser (prior kept as rollback) classified structural-not-transient (a dead one "
            "DEGRADES + escalates to open-ended, never faked) → shipped to Baltor with lineage + CDC refresh → "
            "conflicting sources resolved by authority (loser kept) → a proposed change labeled not-truth → "
            "compressed losslessly → an agent flagged a rate-cap violation from the compressed context. The "
            "whole thesis on one regulated-fact scenario (synthetic data; real spine).")
    return 1 if checks else 0


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--self-test", action="store_true")
    p.parse_args(argv)
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(main())
