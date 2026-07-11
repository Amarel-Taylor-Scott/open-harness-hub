#!/usr/bin/env python3
"""scripts.check_adaptation_ladder — PROOF: the CapabilityTask adaptation ladder enforces the CORE INVARIANT
("adapt MEANS, never autonomously change ENDS") with risk-tiered gates + deny-by-default.

Asserts:
  A. Ladder well-formed: levels 0..5 present; each has gate + requires_human + change_types; risk is monotone
     (L0-L3 not human-gated = MEANS; L4-L5 human-gated).
  B. MEANS auto-promote: L0-L3 change types (timeout/runtime.rebind/selector/implementation.generate_candidate)
     may_auto_promote == True (when their gate passes).
  C. ENDS are NEVER auto: every ends_change_type (purpose/permission/connected_system/external_domain/secret/
     data_class/risk/approval/success_criteria.weaken) → may_auto_promote == False AND human-gated-or-forbidden.
  D. FORBIDDEN-autonomous: weakening criteria / removing evals / disabling observability / dropping source
     handles → may_auto_promote == False, required_gate == 'forbidden_autonomous'.
  E. DENY-BY-DEFAULT: an UNKNOWN change type → level 5, requires_human, may_auto_promote == False.
  F. REDTEAM: an ends change can NOT be routed through an L0/auto gate (its required_gate is human_approval,
     never auto_on_metrics); a forbidden change can't be promoted at all.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from src.baltor.purpose_tasks import adaptation_ladder as al

_AUTO_GATES = {"auto_on_metrics", "cost_latency_reliability_evals", "regression_plus_shadow",
               "full_eval_provenance_canary_rollback"}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    ladder = json.loads((Path(_REPO) / "architecture" / "capability_adaptation_ladder.json").read_text())
    levels = {lv["level"]: lv for lv in ladder["levels"]}

    # A. well-formed + monotone
    check("A: levels 0..5 present", set(levels) == {0, 1, 2, 3, 4, 5}, str(sorted(levels)))
    check("A: each level has gate + requires_human + change_types",
          all(("gate" in lv and "requires_human" in lv and lv.get("change_types") is not None) for lv in levels.values()))
    check("A: L0-L3 are MEANS (not human-gated)", not any(levels[i]["requires_human"] for i in (0, 1, 2, 3)))
    check("A: L4-L5 require a human", levels[4]["requires_human"] and levels[5]["requires_human"])

    # B. MEANS auto-promote
    for ct in ("timeout.patch", "runtime.rebind", "selector.patch", "implementation.generate_candidate"):
        check(f"B: MEANS change auto-promotable: {ct}", al.may_auto_promote(ct) is True, str(al.classify(ct)))

    # C. ENDS never auto
    for ct in ladder["ends_change_types"]:
        c = al.classify(ct)
        check(f"C: ENDS change never auto-promotes: {ct}",
              al.may_auto_promote(ct) is False and (c["requires_human"] or al.is_forbidden_autonomous(ct)),
              str(c))

    # D. forbidden-autonomous
    for ct in ("success_criteria.weaken", "eval_suite.remove", "observability.disable", "source_handle.drop"):
        check(f"D: forbidden-autonomous blocked: {ct}",
              al.may_auto_promote(ct) is False and al.required_gate(ct) == "forbidden_autonomous", al.required_gate(ct))

    # E. deny-by-default
    unk = al.classify("totally.made.up.change")
    check("E: unknown change → L5 + requires_human + not auto",
          unk["level"] == 5 and unk["requires_human"] and al.may_auto_promote("totally.made.up.change") is False, str(unk))

    # F. redteam — an ends change can't be routed through an auto gate
    check("F: permission.expand required_gate is human_approval (not an auto gate)",
          al.required_gate("permission.expand") == "human_approval" and al.required_gate("permission.expand") not in _AUTO_GATES)
    check("F: a MEANS change's gate IS an auto gate (sanity)", al.required_gate("timeout.patch") in _AUTO_GATES)
    check("F: no ENDS change has an auto gate",
          not any(al.required_gate(ct) in _AUTO_GATES for ct in ladder["ends_change_types"]))

    print("\n" + ("PASS — check_adaptation_ladder: L0-L5 risk-tiered gates enforce the core invariant — MEANS "
                  "(L0-L3) auto-promote on passing gates; ENDS + forbidden + unknown changes never auto-promote "
                  "(human-gated or forbidden); deny-by-default holds." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_adaptation_ladder.py --self-test")
    raise SystemExit(0)
