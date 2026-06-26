#!/usr/bin/env python3
"""scripts.check_purpose_task_poc — PROOF: the PurposeTask motion works on the built Parallel-Path Engine.

Demonstrates "provisioned by Purpose/Capability, not by code" + governed self-adaptation:
  A. PROVISION BY CAPABILITY — a PurposeTaskSpec declared by intent (purpose + capability_slot) binds an
     implementation from a registry by NUMERIC priority; no per-task wiring code. Re-prioritizing rebinds it
     (non-fragile — selection is by number, not a hard-coded choice).
  B. SELF-MONITOR — the cheap deterministic hot path is checked against success_criteria; a cost breach is
     detected as drift.
  C. SELF-ADAPT — on drift, a candidate implementation runs SIDE-BY-SIDE vs the current one through the real
     Parallel-Path Engine; an equivalent, cheaper candidate is PROMOTED; the prior impl is kept as a fallback
     (rollback_target); after promotion the task is back within criteria.
  D. GOVERNANCE — a candidate that drops a source handle, or leaks the held-out FAQ "30 days", is REJECTED
     (baseline preserved). A candidate is NEVER served before promotion (served_path_id == baseline).

Deterministic + offline: injected registry/input/now; no LLM in the hot path; reuses src/baltor/experiments/*.
Exit 0/1.
"""
from __future__ import annotations

import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from src.baltor import purpose_tasks as ct

_NOW = "2026-06-06T00:00:00Z"
_OC = "DeadlineRecord"
_INPUT = {"query": "card dispute error-resolution deadline"}


def _result(answer_obj, *, cost, handles, latency=10.0):
    return {"output": answer_obj, "output_contract": _OC, "cost": float(cost),
            "latency_ms": float(latency), "source_handles": list(handles), "contract_validation": "pass"}


# Implementations for the capability slot — the "templates/skills" a PurposeTask draws on. Selection is by
# numeric priority, not by code. (Same answer "10 business days"; they differ in cost / handles / leakage.)
def _v1_expensive(_inp):  # correct but expensive → will breach the cost ceiling
    return _result({"answer": "10 business days"}, cost=10.0, handles=["ctx://reg-e#deadline"])


def _v2_cheap(_inp):      # correct + cheaper + same handles → should be PROMOTED
    return _result({"answer": "10 business days"}, cost=2.0, handles=["ctx://reg-e#deadline"])


def _v3_drops_handle(_inp):  # cheap but DROPS the source handle → must be REJECTED
    return _result({"answer": "10 business days"}, cost=1.0, handles=[])


def _v4_leaks(_inp):      # cheap but LEAKS the held-out FAQ "30 days" → must be REJECTED
    return _result({"answer": "10 business days", "note": "the FAQ says 30 days"}, cost=1.0,
                   handles=["ctx://reg-e#deadline"])


def _registry(priorities=None):
    p = priorities or {"impl_expensive": 70, "impl_cheap": 65, "impl_drops_handle": 60, "impl_leaks": 55}
    return {"fetch_card_deadline": [
        {"impl_id": "impl_expensive", "priority": p["impl_expensive"], "handler": _v1_expensive},
        {"impl_id": "impl_cheap", "priority": p["impl_cheap"], "handler": _v2_cheap},
        {"impl_id": "impl_drops_handle", "priority": p["impl_drops_handle"], "handler": _v3_drops_handle},
        {"impl_id": "impl_leaks", "priority": p["impl_leaks"], "handler": _v4_leaks},
    ]}


def _spec():
    return {
        "schema_version": "PurposeTaskSpec",
        "task_id": "purpose_tasks.fetch_card_deadline@v1",
        "purpose": "Pull the Reg-E error-resolution deadline for a card dispute.",
        "capability_slot": "fetch_card_deadline",
        "input_contract": "DeadlineQuery",
        "output_contract": _OC,
        "success_criteria": {"max_cost": 5.0, "min_source_handles": 1},
        "promotion_criteria": {"cost_tolerance": 0.0},
        "connected_to": ["demo.consumer"],
        "defined_at": _NOW,
    }


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    reg = _registry()
    held = ("30 days",)

    # A. PROVISION BY CAPABILITY (by number, not code)
    spec = ct.provision(_spec(), reg)
    check("A: provisioned by capability → highest-priority impl bound (no per-task code)",
          spec["current_impl_id"] == "impl_expensive", spec.get("current_impl_id"))
    check("A: alternatives recorded in priority order", spec["alternatives"][0] == "impl_cheap", str(spec["alternatives"]))
    # re-prioritize → rebinds (selection is numeric/non-fragile, not a hard-coded choice)
    reg2 = _registry({"impl_expensive": 50, "impl_cheap": 90, "impl_drops_handle": 60, "impl_leaks": 55})
    spec2 = ct.provision(_spec(), reg2)
    check("A: re-prioritizing rebinds the impl (numeric, non-fragile)", spec2["current_impl_id"] == "impl_cheap", spec2["current_impl_id"])

    # B. SELF-MONITOR detects drift (cost breach)
    res = ct.run_current(spec, reg, _INPUT)
    h = ct.evaluate_health(res, spec["success_criteria"], held_out_strings=held)
    check("B: hot path runs the bound impl (cost 10)", res["cost"] == 10.0, str(res["cost"]))
    check("B: self-monitor detects drift (cost over ceiling)", (not h["meets"]) and "cost" in h["drift"], str(h))

    # C. SELF-ADAPT — equivalent + cheaper candidate is PROMOTED; prior kept as fallback; never served early
    out = ct.adapt(spec, reg, _INPUT, now=_NOW, promotion_criteria=spec["promotion_criteria"],
                   candidate_impl_id="impl_cheap", held_out_strings=held)
    check("C: equivalent cheaper candidate PROMOTED", out["promoted"] is True, str(out.get("decision", {}).get("reason")))
    check("C: candidate became current after promotion", out["spec"]["current_impl_id"] == "impl_cheap")
    check("C: prior impl kept as fallback alternative", "impl_expensive" in out["spec"]["alternatives"])
    check("C: rollback_target = prior baseline", out["spec"]["rollback_target"] == "impl_expensive", str(out["spec"].get("rollback_target")))
    check("C: candidate NEVER served before promotion (served = baseline)", out["served_path_id"] == "impl_expensive", out["served_path_id"])
    # after adaptation the task is back within criteria
    res2 = ct.run_current(out["spec"], reg, _INPUT)
    h2 = ct.evaluate_health(res2, spec["success_criteria"], held_out_strings=held)
    check("C: post-adaptation the task meets success_criteria again", h2["meets"] is True and res2["cost"] == 2.0, str(h2))

    # D. GOVERNANCE — unsafe candidates REJECTED, baseline preserved
    bad_handle = ct.adapt(spec, reg, _INPUT, now=_NOW, promotion_criteria=spec["promotion_criteria"],
                          candidate_impl_id="impl_drops_handle", held_out_strings=held)
    check("D: candidate that DROPS a source handle is REJECTED", bad_handle["promoted"] is False)
    check("D: baseline preserved after rejection", bad_handle["spec"]["current_impl_id"] == "impl_expensive")
    bad_leak = ct.adapt(spec, reg, _INPUT, now=_NOW, promotion_criteria=spec["promotion_criteria"],
                        candidate_impl_id="impl_leaks", held_out_strings=held)
    check("D: candidate that LEAKS the held-out FAQ '30 days' is REJECTED", bad_leak["promoted"] is False)

    # determinism
    out_b = ct.adapt(ct.provision(_spec(), reg), reg, _INPUT, now=_NOW,
                     promotion_criteria=_spec()["promotion_criteria"], candidate_impl_id="impl_cheap",
                     held_out_strings=held)
    check("determinism: adapt is repeatable", out_b["promoted"] is True and out_b["served_path_id"] == "impl_expensive")

    print("\n" + ("PASS — check_purpose_task_poc: a PurposeTask is provisioned BY CAPABILITY (numeric, not code), "
                  "self-monitors vs success_criteria, and self-adapts via the governed Parallel-Path Engine — "
                  "promoting an equivalent cheaper candidate while keeping the prior impl as a fallback, never "
                  "serving a candidate before promotion, and rejecting handle-dropping / held-out-leaking "
                  "candidates." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_purpose_task_poc.py --self-test")
    raise SystemExit(0)
