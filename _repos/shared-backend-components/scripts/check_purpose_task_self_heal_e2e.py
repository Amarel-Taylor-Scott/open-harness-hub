#!/usr/bin/env python3
"""scripts.check_purpose_task_self_heal_e2e — PROOF (P4 CAPSTONE): the Teleon PurposeTask runtime self-heals
END-TO-END in one deterministic offline scenario, composing the unit-proven pieces (provision / run_current_guarded /
evaluate_health / adapt / rollback). This is the INTEGRATION proof — it asserts the cross-cutting invariants that only
show up when the whole motion runs, not the unit behaviours (those have their own proofs).

The motion (a PurposeTask declared by intent, no per-task code):
  provision-by-capability → run the cheap guarded hot path → self-monitor → on drift, self-adapt — TWO ways:

  Scenario A (COST drift → promote):
    the bound impl is over the cost ceiling → adapt runs a cheaper EQUIVALENT candidate side-by-side and PROMOTES it
    on a passing gate; the candidate is NEVER served before promotion; the prior impl is kept as rollback_target
    (lossless); post-heal the hot path meets success_criteria again.

  Scenario B (CRASH → recover):
    the bound impl RAISES → run_current_guarded contains it as a drift signal (no crash, no fabricated success);
    adapt does not crash and does NOT fabricate a promotion off the crashed baseline; rollback() recovers to the
    preserved healthy impl; the crashed impl is kept (lossless, re-promotable); post-heal the hot path is healthy.

Cross-cutting invariants asserted: candidate NEVER served before promotion · promotion ALWAYS reversible to a
preserved target · the superseded/regressed impl is never deleted (winner never without the loser) · a crash or a
bad candidate never becomes a served answer.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.purpose_tasks import purpose_task as ct

_SLOT = "reconcile_dates"
_OC = "ReconcileResult"
_INPUT = {"query": "Reg E error-resolution deadline"}
_NOW = "2026-06-06T00:00:00Z"
_HANDLE = "ctx://acme/source/REG-E"
_SUCCESS = {"max_cost": 5.0, "min_source_handles": 1}


def _healthy(cost: float):
    def h(_):
        return {"output": "10 business days", "output_contract": _OC, "cost": cost, "latency_ms": 1,
                "error": None, "source_handles": [_HANDLE]}
    return h


def _crashes(_):
    raise RuntimeError("simulated impl crash (timeout/OOM/bug)")


def _registry() -> dict:
    return {_SLOT: [
        {"impl_id": "impl_baseline", "priority": 30, "handler": _healthy(10.0)},   # healthy but OVER the cost ceiling
        {"impl_id": "impl_cheap", "priority": 20, "handler": _healthy(2.0)},        # healthy + cheaper (promotable)
        {"impl_id": "impl.crashes", "priority": 10, "handler": _crashes, "error_cost": 0.0},
    ]}


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    reg = _registry()

    # ── Scenario A — COST drift → adapt promotes a cheaper equivalent ────────────────────────────────────────
    spec = ct.provision({"capability_slot": _SLOT, "output_contract": _OC, "success_criteria": _SUCCESS}, reg)
    check("A: provisioned by capability → highest-priority impl bound (no per-task code)",
          spec["current_impl_id"] == "impl_baseline")
    hot = ct.run_current_guarded(spec, reg, _INPUT)
    health = ct.evaluate_health(hot, _SUCCESS)
    check("A: guarded hot path runs the bound impl; self-monitor detects COST drift",
          hot["cost"] == 10.0 and health["meets"] is False and "cost" in health["drift"], str(health))
    outA = ct.adapt(spec, reg, _INPUT, now=_NOW, promotion_criteria={"cost_tolerance": 0.0},
                    candidate_impl_id="impl_cheap")
    check("A: adapt PROMOTES the cheaper equivalent candidate (gate authorized)", outA["promoted"] is True,
          str(outA.get("decision", {}).get("reason")))
    check("A: candidate NEVER served before promotion (served = the baseline during the side-by-side run)",
          outA["served_path_id"] == "impl_baseline", outA["served_path_id"])
    healed = outA["spec"]
    check("A: post-promotion the candidate is current; prior impl kept as rollback_target (LOSSLESS, reversible)",
          healed["current_impl_id"] == "impl_cheap" and healed["rollback_target"] == "impl_baseline"
          and "impl_baseline" in healed["alternatives"], str(healed))
    hot2 = ct.run_current_guarded(healed, reg, _INPUT)
    check("A: post-heal the hot path meets success_criteria again (cheap + healthy)",
          ct.evaluate_health(hot2, _SUCCESS)["meets"] is True and hot2["cost"] == 2.0, str(hot2.get("cost")))

    # ── Scenario B — CRASH → contained as drift → adapt no-crash → rollback recovery ─────────────────────────
    spec_b = {"task_id": "pt_e2e_b", "capability_slot": _SLOT, "output_contract": _OC,
              "current_impl_id": "impl.crashes", "alternatives": ["impl_cheap"],
              "rollback_target": "impl_cheap", "success_criteria": _SUCCESS}
    hot_b = ct.run_current_guarded(spec_b, reg, _INPUT)
    health_b = ct.evaluate_health(hot_b, _SUCCESS)
    check("B: a crashing bound impl is CONTAINED as drift (output '', error set) — never a crash, never a served answer",
          hot_b["output"] == "" and bool(hot_b.get("error")) and health_b["meets"] is False and "error" in health_b["drift"],
          str(hot_b)[:140])
    try:
        outB = ct.adapt(spec_b, reg, _INPUT, now=_NOW, promotion_criteria={"cost_tolerance": 0.0},
                        candidate_impl_id="impl_cheap")
        b_crashed = False
    except Exception:
        outB, b_crashed = {}, True
    check("B: adapt does NOT crash on a crashed baseline + does NOT fabricate a promotion off it",
          not b_crashed and outB.get("promoted") is False, str({"crashed": b_crashed, "promoted": outB.get("promoted")}))
    rb = ct.rollback(spec_b, reg, to=None)   # uses the preserved rollback_target
    recovered = rb["spec"]
    check("B: rollback RECOVERS to the preserved healthy impl; the crashed impl is kept (LOSSLESS, re-promotable)",
          rb["rolled_back"] is True and recovered["current_impl_id"] == "impl_cheap"
          and "impl.crashes" in recovered["alternatives"], str(recovered))
    hot_b2 = ct.run_current_guarded(recovered, reg, _INPUT)
    check("B: post-recovery the hot path is healthy again (meets success_criteria)",
          ct.evaluate_health(hot_b2, _SUCCESS)["meets"] is True and hot_b2["output"] == "10 business days", str(hot_b2.get("cost")))

    # ── Cross-cutting invariant: registry is never mutated (impls are never deleted — lossless across the motion)
    check("X: the implementation registry is intact after both heals (no impl deleted — winner never without the loser)",
          {i["impl_id"] for i in reg[_SLOT]} == {"impl_baseline", "impl_cheap", "impl.crashes"})

    print("\n" + ("PASS — check_purpose_task_self_heal_e2e: the PurposeTask runtime self-heals end-to-end — provision → "
                  "guarded hot path → drift → (cost) promote a cheaper equivalent OR (crash) contain + rollback-recover — "
                  "never serving a candidate before promotion, never fabricating a promotion off a crash, always keeping "
                  "the predecessor as a reversible/lossless rollback target, and returning to health." if not fails
                  else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_purpose_task_self_heal_e2e.py --self-test")
    raise SystemExit(0)
