#!/usr/bin/env python3
"""scripts.check_purpose_task_hot_path_guard — PROOF (P4 / Teleon PurposeTask runtime hardening): the guarded hot path
never crashes the controller and never fabricates a success when a bound implementation misbehaves.

run_current assumes a well-behaved handler (returns a RunnerResult); a real implementation can RAISE (bug, timeout,
resource error) or return garbage. run_current_guarded converts that into a structured DRIFT result so the existing
evaluate_health -> adapt/rollback machinery can respond — output stays empty, error is set, the controller stays up.

Asserts:
  A. HAPPY PATH UNCHANGED: a well-behaved handler → run_current_guarded returns the handler's result verbatim
     (same as run_current) — the guard only shapes failure, the hot path stays cheap.
  B. RAISE → NO CRASH: a handler that raises does NOT propagate; run_current_guarded returns a result with
     error set, output '', crashed=True (and never raises).
  C. RAISE → DRIFT, NEVER FABRICATED SUCCESS: evaluate_health on the guarded error result is meets=False with
     'error' in drift; the output is empty so it can never read as a served answer.
  D. NON-RUNNERRESULT → CONTRACT DRIFT: a handler returning a non-dict is converted to a ContractError drift
     result (no crash, output '').
  E. ADAPT CRASH-SAFE + RECOVERY: the side-by-side adapt runner is guarded by the SAME _guarded_call — a crashing
     CANDIDATE is scored failed and never promoted (E1); a crashing BASELINE never crashes adapt and is not
     promoted-over on a meaningless comparison (E2); recovery from a crashing baseline is via rollback() (E3).
  F. DETERMINISTIC: identical inputs → identical guarded result.

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
_OC = "ReconcileResult.v1"
_INPUT = {"query": "error-resolution deadline"}
_NOW = "2026-06-06T00:00:00Z"


def _good(_):
    return {"output": "10 business days", "output_contract": _OC, "cost": 2.0, "latency_ms": 3,
            "error": None, "source_handles": ["ctx://acme/source/REG-E"]}


def _boom(_):
    raise RuntimeError("simulated handler crash (timeout/OOM/bug)")


def _noncompliant(_):
    return "not a RunnerResult"


def _registry() -> dict:
    return {_SLOT: [
        {"impl_id": "impl.crashes", "priority": 30, "handler": _boom, "error_cost": 0.0},
        {"impl_id": "impl.healthy", "priority": 20, "handler": _good},
        {"impl_id": "impl.noncompliant", "priority": 10, "handler": _noncompliant},
    ]}


def _spec(current: str) -> dict:
    return {"task_id": "pt_guard_001", "capability_slot": _SLOT, "output_contract": _OC,
            "current_impl_id": current, "alternatives": [], "rollback_target": "",
            "success_criteria": {"max_cost": 5.0, "min_source_handles": 1},
            "promotion_criteria": {"cost_tolerance": 0.0}}


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    reg = _registry()

    # A — happy path unchanged
    g_ok = ct.run_current_guarded(_spec("impl.healthy"), reg, _INPUT)
    check("A: happy path — guarded result equals the handler's result (guard only shapes failure)",
          g_ok == ct.run_current(_spec("impl.healthy"), reg, _INPUT) and g_ok["output"] == "10 business days"
          and not g_ok.get("error"))

    # B — raise → no crash
    raised = False
    try:
        g_boom = ct.run_current_guarded(_spec("impl.crashes"), reg, _INPUT)
    except Exception:
        raised = True
        g_boom = {}
    check("B: a raising handler does NOT crash the hot path (no exception propagates)", not raised)
    check("B: raise → structured error result (error set, output '', crashed=True)",
          bool(g_boom.get("error")) and g_boom.get("output") == "" and g_boom.get("crashed") is True, str(g_boom)[:160])

    # C — drift, never fabricated success
    h = ct.evaluate_health(g_boom, _spec("impl.crashes")["success_criteria"])
    check("C: guarded crash → evaluate_health drift (meets=False, 'error' in drift); empty output ≠ served answer",
          h["meets"] is False and "error" in h["drift"] and g_boom.get("output") == "", str(h))

    # D — non-RunnerResult → contract drift
    g_nc = ct.run_current_guarded(_spec("impl.noncompliant"), reg, _INPUT)
    check("D: non-RunnerResult return → ContractError drift result (no crash, output '')",
          g_nc.get("error", {}).get("type") == "ContractError" and g_nc.get("output") == "" and g_nc.get("crashed") is True,
          str(g_nc)[:160])

    # ADAPT is now crash-SAFE too (slice 5): the side-by-side runner is guarded, so a crashing baseline OR candidate
    # becomes a scored failure instead of aborting adapt. A crashing candidate is never promoted; a crashing baseline
    # does not crash adapt and is NOT promoted-over on a meaningless comparison; recovery from a crashing baseline is
    # via rollback() (slice 1) — adapt never crashes and never fabricates a promotion.
    def _no_raise(fn):
        try:
            return fn(), True
        except Exception:
            return None, False

    # E1 — crashing CANDIDATE: adapt completes (no crash) and the crashing candidate is NOT promoted (baseline kept)
    out_bc, ok1 = _no_raise(lambda: ct.adapt(_spec("impl.healthy"), reg, _INPUT, now=_NOW,
                                             promotion_criteria={"cost_tolerance": 0.0}, candidate_impl_id="impl.crashes"))
    check("E1: adapt does NOT crash on a crashing CANDIDATE + the candidate is NOT promoted (baseline preserved)",
          ok1 and out_bc["promoted"] is False and out_bc["spec"]["current_impl_id"] == "impl.healthy",
          str({"ok": ok1, "promoted": (out_bc or {}).get("promoted")}))

    # E2 — crashing BASELINE: adapt completes (no exception); it does NOT fabricate a promotion off a crashed baseline
    out_bb, ok2 = _no_raise(lambda: ct.adapt(_spec("impl.crashes"), reg, _INPUT, now=_NOW,
                                             promotion_criteria={"cost_tolerance": 0.0}, candidate_impl_id="impl.healthy"))
    check("E2: adapt does NOT crash on a crashing BASELINE (no exception) + no promotion fabricated off a crashed comparison",
          ok2 and out_bb["promoted"] is False, str({"ok": ok2, "promoted": (out_bb or {}).get("promoted")}))

    # E3 — recovery from a crashing baseline: rollback() to a healthy impl, then the guarded hot path serves it
    recovered = ct.rollback(_spec("impl.crashes"), reg, to="impl.healthy")["spec"]
    healed = ct.run_current_guarded(recovered, reg, _INPUT)
    check("E3: recovery — rollback to a healthy impl → guarded hot path serves a healthy result (self-heal)",
          recovered["current_impl_id"] == "impl.healthy" and healed["output"] == "10 business days"
          and ct.evaluate_health(healed, _spec("impl.crashes")["success_criteria"])["meets"] is True)

    # F — deterministic
    check("F: deterministic — identical guarded result on repeat for the crash case",
          ct.run_current_guarded(_spec("impl.crashes"), reg, _INPUT) == ct.run_current_guarded(_spec("impl.crashes"), reg, _INPUT))

    print("\n" + ("PASS — check_purpose_task_hot_path_guard: a raising / non-compliant implementation is contained as a "
                  "structured drift signal (output empty, error set, never a crash, never a fabricated success) on BOTH "
                  "the guarded hot path AND the side-by-side adapt runner — a crashing candidate/baseline never crashes "
                  "adapt or fabricates a promotion; recovery is via rollback to a healthy impl." if not fails
                  else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_purpose_task_hot_path_guard.py --self-test")
    raise SystemExit(0)
