#!/usr/bin/env python3
"""scripts.check_purpose_task_rollback — PROOF (P4 / Teleon PurposeTask runtime hardening): a promoted PurposeTask
implementation is ALWAYS reversible to its preserved rollback target, losslessly and fail-closed.

`adapt` promotes a candidate and RECORDS rollback_target + keeps the prior impl as a fallback — but until now nothing
acted on it. `purpose_task.rollback(spec, registry, to=None)` performs the reversal. This proof pins its contract:

  A. REVERTS: rollback uses the recorded rollback_target — current_impl_id returns to the prior impl (from/to reported).
  B. LOSSLESS: the regressed impl is DEMOTED into alternatives (not deleted) and is still a registered implementation;
     the target is removed from alternatives (it is current now); the pending rollback_target is consumed ('').
  C. EXPLICIT TARGET: `to=` rolls back to any earlier registered impl, not just the last.
  D. FAIL-CLOSED (no target): no rollback_target and no `to` -> rolled_back=False, spec UNCHANGED (current never blanked).
  E. FAIL-CLOSED (unregistered): a target that is not a registered impl -> rolled_back=False, spec UNCHANGED.
  F. NO-OP: target already current -> rolled_back=False, spec UNCHANGED.
  G. REVERSIBLE/RE-PROMOTABLE: after rollback the regressed impl is the FRONT alternative — `adapt` would re-try it
     first, so promotion<->rollback is a closed, lossless loop (never a one-way door, no winner without the loser kept).
  H. DETERMINISTIC: same inputs -> identical result (pure; no now/IO).

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.purpose_tasks.purpose_task import rollback

_SLOT = "reconcile_dates"


def _registry() -> dict:
    def _h(impl):
        return lambda x: {"output": f"{impl}:{x}", "output_contract": "ReconcileResult.v1", "cost": 1.0,
                          "source_handles": ["ctx://acme/source/BILL-782"]}
    return {_SLOT: [{"impl_id": i, "priority": p, "handler": _h(i)} for i, p in (("v1", 30), ("v2", 20), ("v3", 10))]}


def _post_promotion_spec() -> dict:
    # exactly the shape `adapt` produces after promoting v2 over v1 (prior kept as fallback + rollback_target).
    return {"task_id": "pt_reconcile_001", "capability_slot": _SLOT, "output_contract": "ReconcileResult.v1",
            "current_impl_id": "v2", "alternatives": ["v1", "v3"], "rollback_target": "v1"}


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    reg = _registry()
    registered = {i["impl_id"] for i in reg[_SLOT]}

    # A + B — recorded-target rollback, lossless
    r = rollback(_post_promotion_spec(), reg)
    s = r.get("spec", {})
    check("A: reverts to the recorded rollback_target (current_impl_id v2 -> v1; from/to reported)",
          r.get("rolled_back") is True and r.get("from") == "v2" and r.get("to") == "v1"
          and s.get("current_impl_id") == "v1", str({k: r.get(k) for k in ("rolled_back", "from", "to")}))
    check("B: LOSSLESS — regressed v2 demoted into alternatives (not deleted) + still registered; target dropped from alts; pending target consumed",
          "v2" in s.get("alternatives", []) and "v2" in registered and "v1" not in s.get("alternatives", [])
          and "v3" in s.get("alternatives", []) and s.get("rollback_target") == "",
          str(s.get("alternatives")))

    # C — explicit target overrides the recorded one
    r3 = rollback(_post_promotion_spec(), reg, to="v3")
    check("C: explicit `to` rolls back to any earlier registered impl (v3); regressed v2 demoted",
          r3.get("rolled_back") is True and r3["spec"]["current_impl_id"] == "v3"
          and "v2" in r3["spec"]["alternatives"] and "v3" not in r3["spec"]["alternatives"],
          str(r3.get("spec")))

    # D — fail-closed: no target → unchanged
    no_target = {**_post_promotion_spec(), "rollback_target": ""}
    rd = rollback(no_target, reg)
    check("D: FAIL-CLOSED no target — rolled_back=False + current_impl_id unchanged (never blanked)",
          rd.get("rolled_back") is False and rd["spec"]["current_impl_id"] == "v2"
          and rd["spec"] == no_target, str(rd))

    # E — fail-closed: unregistered target → unchanged
    re_ = rollback(_post_promotion_spec(), reg, to="ghost_impl")
    check("E: FAIL-CLOSED unregistered target — rolled_back=False + current unchanged (no fabricated impl)",
          re_.get("rolled_back") is False and re_["spec"]["current_impl_id"] == "v2", str(re_))

    # F — no-op: target already current
    on_target = {**_post_promotion_spec(), "current_impl_id": "v1", "alternatives": ["v2", "v3"], "rollback_target": "v1"}
    rf = rollback(on_target, reg)
    check("F: NO-OP when target is already current — rolled_back=False + spec unchanged",
          rf.get("rolled_back") is False and rf["spec"] == on_target and "already serving" in rf.get("reason", ""),
          str(rf))

    # G — reversible / re-promotable: the regressed impl is the FRONT alternative after rollback
    check("G: REVERSIBLE — regressed impl is the front alternative (adapt re-tries it first; promotion<->rollback closed loop)",
          s.get("alternatives", [None])[0] == "v2")

    # H — determinism
    check("H: deterministic (pure) — identical result on repeat",
          rollback(_post_promotion_spec(), reg) == rollback(_post_promotion_spec(), reg))

    print("\n" + ("PASS — check_purpose_task_rollback: PurposeTask promotion is always reversible — rollback reverts to "
                  "the preserved target, demotes the regressed impl into alternatives (lossless, re-promotable), consumes "
                  "the pending rollback_target, and fails closed (never blanks current / never invents an impl) when there "
                  "is no valid target." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_purpose_task_rollback.py --self-test")
    raise SystemExit(0)
