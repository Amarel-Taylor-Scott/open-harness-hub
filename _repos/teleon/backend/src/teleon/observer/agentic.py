"""observer.agentic — AIDevObserver for AUTONOMOUS agent loops (not just human sessions).

A human session is a person prompting an AI; an AGENTIC session is an autonomous loop that decides + acts on its
own (the repo's own flywheel / worker fleet, or any agent runner). It fails in ways a human session does not -
it can THRASH (repeat a failing action), STALL (spin with no progress), LOOP toward a runaway COST, repeat the
same FAILURE, or DRIFT off its stated goal. This module supervises that loop on two timelines:

  - intra-run:  monitor_step(steps_so_far, ...) -> alerts + a recommend_halt flag, called after each iteration so
                an orchestrator can pause/redirect a runaway loop BEFORE it burns the budget.
  - post-run:   review_agentic_run(steps, ...) -> the full governed report + an efficiency verdict.

It REUSES the engine: router.route_session catches the per-step content risks (reinvention / footgun / waste),
and this module ADDS the loop-shape signals over the step SEQUENCE (stall / thrash / repeated-failure / budget /
goal-drift), which are deterministic (computed from the steps, not a model opinion).

LAW (mirrors the product): it NEVER kills a process. `recommend_halt` is a RECOMMENDATION a supervising
orchestrator acts on; the observer is read-only and stores nothing. serves_truth=false; every signal is a
governed candidate a human (or the orchestrator's policy) triages.

  python3 -m src.teleon.observer.agentic --self-test
"""
from __future__ import annotations

import argparse
import os
import sys

from .router import route_session

# --- thresholds (single source; env-overridable so an orchestrator can tune restraint, no magic literals) -------
_LOOP_REPEAT = int(os.environ.get("OBSERVER_AGENTIC_LOOP_REPEAT", "3"))      # same action N+ times in a row -> thrash
_STALL_WINDOW = int(os.environ.get("OBSERVER_AGENTIC_STALL_WINDOW", "4"))    # N steps with no new state -> stall
_FAILURE_REPEAT = int(os.environ.get("OBSERVER_AGENTIC_FAILURE_REPEAT", "3"))  # same error N+ times -> stuck
_DRIFT_WINDOW = int(os.environ.get("OBSERVER_AGENTIC_DRIFT_WINDOW", "5"))    # last-N steps scored for goal overlap
_DRIFT_MIN_OVERLAP = float(os.environ.get("OBSERVER_AGENTIC_DRIFT_OVERLAP", "0.12"))  # below this -> drift
# signal types that, when present, set recommend_halt (hard, protective — a runaway loop should stop)
_HALT_SIGNALS = {"agentic_budget_overrun", "agentic_loop", "agentic_stall", "agentic_repeated_failure"}


def _norm(action: str) -> str:
    """Normalize an action for repeat/loop comparison (whitespace-collapsed, lowercased)."""
    return " ".join(str(action or "").split()).lower()


def _step_events(steps: list[dict]) -> list[dict]:
    """Project agentic steps onto the engine's message shape so route_session can spot content risks per step."""
    out: list[dict] = []
    for s in steps:
        action = s.get("action") or s.get("command") or s.get("content") or ""
        out.append({"role": "assistant", "content": str(action)})
    return out


def _finding(kind: str, step_index: int, confidence: float, message: str, suggestion: str) -> dict:
    """An agentic loop-shape finding, in the engine's governed-candidate shape (composes with route_session)."""
    return {"type": kind, "message_index": step_index, "confidence": round(confidence, 3),
            "message": message, "suggestion": suggestion, "evidence": message,
            "source_ref": {}, "candidate": True, "serves_truth": False}


def loop_signals(steps: list[dict], *, goal: str = "", budget: dict | None = None) -> list[dict]:
    """The deterministic loop-shape signals over the step SEQUENCE. budget: {max_steps?, max_cost?}.

    Each step: {action|command, ok?:bool, error?:str, cost?:float, output?:str}. Returns governed candidate
    findings (serves_truth=false), ranked by confidence desc. Pure + deterministic."""
    findings: list[dict] = []
    n = len(steps)
    budget = budget or {}

    # 1) THRASH — the same action repeated _LOOP_REPEAT+ times in a row
    run_start, run_len = 0, 1
    for i in range(1, n + 1):
        same = i < n and _norm(steps[i].get("action") or steps[i].get("command")) == \
            _norm(steps[i - 1].get("action") or steps[i - 1].get("command")) and _norm(steps[i].get("action") or steps[i].get("command"))
        if same:
            run_len += 1
        else:
            if run_len >= _LOOP_REPEAT:
                findings.append(_finding("agentic_loop", run_start, min(0.99, 0.6 + 0.1 * run_len),
                    f"the same action ran {run_len} times in a row (thrash) starting at step {run_start}",
                    "break the loop: change the approach, or stop and surface the blocker"))
            run_start, run_len = i, 1

    # 2) REPEATED FAILURE — the same error recurs _FAILURE_REPEAT+ times (not necessarily consecutive)
    errs: dict[str, list[int]] = {}
    for i, s in enumerate(steps):
        if s.get("ok") is False or s.get("error"):
            errs.setdefault(_norm(s.get("error") or "failed"), []).append(i)
    for err, idxs in errs.items():
        if len(idxs) >= _FAILURE_REPEAT:
            findings.append(_finding("agentic_repeated_failure", idxs[0], min(0.97, 0.55 + 0.1 * len(idxs)),
                f"the same failure recurred {len(idxs)} times: {err[:80]}",
                "stop retrying the same failing path; escalate or change strategy"))

    # 3) STALL — _STALL_WINDOW consecutive steps with no NEW state (no file/output change, no success)
    if n >= _STALL_WINDOW:
        tail = steps[-_STALL_WINDOW:]
        states = {(_norm(s.get("output") or ""), bool(s.get("ok"))) for s in tail}
        progressed = any(s.get("ok") and (s.get("output") or s.get("changed")) for s in tail)
        if len(states) <= 1 and not progressed:
            findings.append(_finding("agentic_stall", n - _STALL_WINDOW, 0.8,
                f"{_STALL_WINDOW} steps with no new state (stalled)",
                "no progress is being made; pause and re-plan or surface the blocker"))

    # 4) BUDGET OVERRUN — cumulative steps / cost over the ceiling
    max_steps = budget.get("max_steps")
    if max_steps and n > max_steps:
        findings.append(_finding("agentic_budget_overrun", max_steps, 0.95,
            f"step budget exceeded: {n} steps > max_steps {max_steps}", "halt; the loop is over its iteration budget"))
    max_cost = budget.get("max_cost")
    if max_cost:
        total = sum(float(s.get("cost") or 0) for s in steps)
        if total > max_cost:
            findings.append(_finding("agentic_budget_overrun", n - 1, 0.96,
                f"cost budget exceeded: {total:.4f} > max_cost {max_cost}", "halt; the loop is over its cost budget"))

    # 5) GOAL DRIFT — the recent window's actions barely overlap the stated goal's terms
    goal_terms = {w for w in _norm(goal).split() if len(w) > 3}
    if goal_terms and n >= _DRIFT_WINDOW:
        recent = " ".join(_norm(s.get("action") or s.get("command")) for s in steps[-_DRIFT_WINDOW:])
        recent_terms = {w for w in recent.split() if len(w) > 3}
        overlap = len(goal_terms & recent_terms) / max(1, len(goal_terms))
        if overlap < _DRIFT_MIN_OVERLAP:
            findings.append(_finding("agentic_goal_drift", n - _DRIFT_WINDOW, round(0.6 + (1 - overlap) * 0.2, 3),
                f"the last {_DRIFT_WINDOW} steps barely overlap the goal (overlap {overlap:.0%})",
                "the loop may be drifting off-goal; re-anchor to the objective"))

    findings.sort(key=lambda f: f["confidence"], reverse=True)
    return findings


def monitor_step(steps_so_far: list[dict], *, goal: str = "", budget: dict | None = None,
                 mode: str = "advisory") -> dict:
    """INTRA-RUN: call after each iteration. Returns {alerts, recommend_halt, mode, serves_truth}. recommend_halt
    is True when a protective loop-signal trips (runaway cost / thrash / stall / stuck) - a RECOMMENDATION the
    orchestrator acts on (this never kills the process)."""
    signals = loop_signals(steps_so_far, goal=goal, budget=budget)
    recommend_halt = mode in ("active", "enforcing") and any(s["type"] in _HALT_SIGNALS for s in signals)
    return {"alerts": signals, "recommend_halt": recommend_halt, "mode": mode,
            "step": len(steps_so_far), "serves_truth": False, "governed": True}


def review_agentic_run(steps: list[dict], *, goal: str = "", budget: dict | None = None) -> dict:
    """POST-RUN: the full governed report over a finished agentic loop = per-step content risks (route_session)
    + the loop-shape signals + an efficiency VERDICT. serves_truth=false."""
    content = route_session(_step_events(steps), mode="review_only")
    loop = loop_signals(steps, goal=goal, budget=budget)
    report = sorted(content["report"] + loop, key=lambda f: f["confidence"], reverse=True)
    by_type: dict[str, int] = {}
    for f in report:
        by_type[f["type"]] = by_type.get(f["type"], 0) + 1
    savings = content.get("savings") if isinstance(content.get("savings"), dict) else {
        "tokens_avoided_estimate": 0,
        "model_calls_avoided_estimate": 0,
        "basis_counts": {},
        "serves_truth": False,
    }
    failures = sum(1 for s in steps if s.get("ok") is False or s.get("error"))
    halting = [f for f in loop if f["type"] in _HALT_SIGNALS]
    verdict = ("stalled_or_runaway" if halting else
               "wasteful" if (failures > max(1, len(steps) // 3) or len(loop) >= 2) else
               "clean")
    return {
        "report": report,
        "loop_signals": loop,
        "summary": {"steps": len(steps), "failures": failures, "findings": len(report),
                    "loop_findings": len(loop), "by_type": by_type, "verdict": verdict,
                    "tokens_avoided_estimate": savings.get("tokens_avoided_estimate", 0),
                    "model_calls_avoided_estimate": savings.get("model_calls_avoided_estimate", 0)},
        "savings": savings,
        "serves_truth": False, "governed": content.get("governed", True),
    }


def _self_test() -> int:
    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(name)
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    # thrash: same failing command repeated
    thrash = [{"action": "pytest tests/", "ok": False, "error": "ImportError: no module x"} for _ in range(4)]
    fl = loop_signals(thrash)
    ck("thrash (repeated action) detected", any(f["type"] == "agentic_loop" for f in fl))
    ck("repeated failure detected", any(f["type"] == "agentic_repeated_failure" for f in fl))

    # budget overrun (steps + cost)
    over = [{"action": f"step {i}", "cost": 1.0} for i in range(10)]
    ck("step-budget overrun detected", any(f["type"] == "agentic_budget_overrun"
        for f in loop_signals(over, budget={"max_steps": 5})))
    ck("cost-budget overrun detected", any(f["type"] == "agentic_budget_overrun"
        for f in loop_signals(over, budget={"max_cost": 3.0})))

    # stall: no new state across the window
    stall = [{"action": f"think {i}", "ok": False, "output": ""} for i in range(5)]
    ck("stall (no progress) detected", any(f["type"] == "agentic_stall" for f in loop_signals(stall)))

    # goal drift: actions unrelated to the goal
    drift = [{"action": "refactor unrelated billing widget color"} for _ in range(6)]
    ck("goal drift detected", any(f["type"] == "agentic_goal_drift"
        for f in loop_signals(drift, goal="extract tables from scanned invoice pdfs")))

    # CLEAN run: varied, succeeding, on-goal, in budget -> no loop signals (precision)
    clean = [
        {"action": "parse invoice pdf page 1", "ok": True, "output": "12 rows"},
        {"action": "validate invoice totals", "ok": True, "output": "ok"},
        {"action": "extract invoice line items", "ok": True, "output": "done"},
    ]
    ck("a clean on-goal run stays quiet (precision)",
       loop_signals(clean, goal="extract invoice line items", budget={"max_steps": 50}) == [])

    # intra-run: recommend_halt only in active/enforcing on a protective signal, never below
    mon_adv = monitor_step(over, budget={"max_steps": 5}, mode="advisory")
    mon_act = monitor_step(over, budget={"max_steps": 5}, mode="active")
    ck("intra-run never halts in advisory mode", mon_adv["recommend_halt"] is False and len(mon_adv["alerts"]) >= 1)
    ck("intra-run recommends halt in active mode on a runaway", mon_act["recommend_halt"] is True)
    ck("monitor is governed + read-only", mon_act["serves_truth"] is False and mon_act["governed"] is True)

    # post-run: report + verdict; a footgun in a step still surfaces via route_session
    run = review_agentic_run(thrash + [{"action": "git push --force origin main", "ok": True}], goal="run tests")
    ck("post-run yields a governed report + verdict", run["serves_truth"] is False and "verdict" in run["summary"])
    ck("post-run verdict flags the runaway", run["summary"]["verdict"] == "stalled_or_runaway")
    ck("post-run still catches a per-step footgun (route_session reuse)",
       any("footgun" in t for t in run["summary"]["by_type"]))
    ck("deterministic (same steps -> same signals)", loop_signals(thrash) == fl)

    if fails:
        print(f"\nFAIL - observer.agentic: {len(fails)} of {checks} assertions failed")
        return 1
    print(f"PASS - observer.agentic: supervises autonomous agent loops (intra-run monitor_step + post-run "
          f"review_agentic_run) over the router engine — detects thrash / repeated-failure / stall / budget-overrun "
          f"/ goal-drift, recommends (never forces) halt, stays quiet on a clean run; {checks} assertions; "
          f"serves_truth=false, read-only, governed candidates.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AIDevObserver supervision of autonomous agent loops.")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
