#!/usr/bin/env python3
"""scripts.stall_breaker — break a LOGJAM when the loop stalls: deliberate (Claude/Kimi/GLM), then FORK options.

A stall = no forward progress (proof gates stuck red across runs, a flywheel failing repeatedly, no new findings for a
while). When detected the loop must NOT churn — it leverages best judgment (Kimi + GLM via the loop's ask_models; Claude
in /loop mode) for DIVERGENT ways forward, and FORKS each as a scored PROPOSAL/PLAN in the backlog so the owner/agent
picks a path. If no clean option emerges, the forks themselves ARE the prioritized decision (the stall is never lost).
Deliberation favors DESIGN BEST PRACTICES — thin high-level wrappers + clean abstractions for maximum flexibility.

Thin wrapper that COMPOSES existing pieces (multi_model_improvement_loop.ask_models + proposal_backlog) — no new engine.
DEVELOPMENT plane; serves_truth=false.

  --self-test   offline: stall detection signals + fork-without-models fallback
  --break       detect a stall from the flywheel state and break it (forks options into the backlog)
CLI: PYTHONPATH=. python3 scripts/stall_breaker.py --break
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

_ERROR_THRESHOLD = 3        # a flywheel failing this many times = stuck
_NO_PROGRESS = 3            # this many cycles with no new findings = stalled
_HEALTH_RED_RUNS = 3        # proof gates still red after this many health runs = a real logjam


def detect_stall(state: dict) -> list[str]:
    """Stall signals from the flywheel state (pure). Empty list = healthy forward motion."""
    reasons = []
    if state.get("health_red_streak", 0) >= _HEALTH_RED_RUNS:
        reasons.append(f"proof gates RED across {state['health_red_streak']} health runs")
    for fw, errs in (state.get("errors", {}) or {}).items():
        if errs >= _ERROR_THRESHOLD:
            reasons.append(f"flywheel '{fw}' failing repeatedly ({errs}x)")
    if state.get("no_progress", 0) >= _NO_PROGRESS:
        reasons.append(f"no new findings for {state['no_progress']} cycles")
    return reasons


#: reasoning-model preamble / chain-of-thought openers + generic section headers to skip when titling a fork.
_PREAMBLE = ("my read", "we need", "the problem", "let me", "here is", "here are", "as an", "as a", "i'll", "i will",
             "okay", "first,", "the user", "they ask", "analysis", "read of the problem", "problem", "thinking",
             "step 1", "to solve", "let's", "sure", "great")
#: action verbs that mark a concrete recommendation (vs narration) — prefer a line that starts with one.
_ACTION = ("split", "extract", "add", "wrap", "build", "switch", "introduce", "refactor", "adopt", "use", "create",
           "replace", "defer", "fork", "abstract", "port", "decouple", "cache", "move", "make", "expose", "define",
           "compose", "isolate", "gate", "promote", "stage", "decompose", "consolidate", "unify", "thin")


def _first_line(text: str) -> str:
    """Title a fork with its actual recommendation — skip reasoning-model preamble/CoT + generic headers, prefer a line
    that starts with an action verb; fall back to the first substantive line."""
    cands = []
    for ln in (text or "").splitlines():
        s = ln.strip("#*->•0123456789. ").strip()    # strip markdown + list markers
        low = s.lower()
        if len(s) <= 14 or any(low.startswith(p) for p in _PREAMBLE):
            continue
        cands.append(s)
        if len(cands) >= 12:
            break
    for s in cands:                                    # prefer a concrete, action-led recommendation
        if s.lower().split()[0] in _ACTION:
            return s[:110]
    return (cands[0] if cands else (text or "stalled").strip())[:110]


def break_logjam(reasons: list[str], *, context: str = "", model_options: bool = True) -> dict:
    """Break the logjam: ask Kimi + GLM for DIVERGENT options, fork each as a backlog proposal; if none, fork a single
    owner-decision proposal so the stall is captured + prioritized. Returns {reasons, forked, proposals}."""
    from scripts.proposal_backlog import Proposal, propose, prioritize, assess_comfort
    reason_str = "; ".join(reasons) or "the loop stalled"
    prompt = (f"The improvement loop is STALLED: {reason_str}. Give 3 DIVERGENT ways forward (genuinely different "
              f"approaches), each with the first concrete step. Favor DESIGN BEST PRACTICES — thin high-level wrappers "
              f"+ clean abstractions for maximum future flexibility; avoid monoliths + lock-in.")
    forks = []
    if model_options:
        try:
            from scripts.multi_model_improvement_loop import ask_models
            for r in ask_models(prompt, context=context):
                ins = r.get("insight")
                if not ins or r.get("error"):
                    continue
                a = assess_comfort(ins)
                rec = propose(Proposal(title=f"[logjam fork · {r['model']}] {_first_line(ins)}", kind="plan",
                                       source=f"stall-break:{r['model']}", comfort=a["comfort"], risk=a["risk"],
                                       reversibility=a["reversibility"], confidence=a["confidence"],
                                       rationale=f"logjam: {reason_str}", next_steps=ins[:1200], refs=("stall",)))
                forks.append(rec["pid"])
        except Exception:  # noqa: BLE001 — deliberation is best-effort; fall through to the decision fork
            pass
    if not forks:
        # no clean option (models offline / nothing emerged) -> capture the stall as a prioritized owner decision
        rec = propose(Proposal(title=f"[logjam] decide a way forward — {reasons[0] if reasons else 'loop stalled'}",
                               kind="proposal", source="stall-break", comfort="owner_gated",
                               rationale=f"logjam, no auto-resolvable option: {reason_str}",
                               next_steps="owner/agent: pick or design a path forward (favor thin wrappers + flexibility)."))
        forks.append(rec["pid"])
    prioritize()
    return {"reasons": reasons, "forked": len(forks), "proposals": forks, "serves_truth": False}


def _self_test() -> int:
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)
    ck("no stall on a healthy state", detect_stall({"errors": {}, "no_progress": 0, "health_red_streak": 0}) == [])
    ck("stall: proof gates red across runs", any("RED" in r for r in detect_stall({"health_red_streak": 3, "errors": {}})))
    ck("stall: a flywheel failing repeatedly", any("failing" in r for r in detect_stall({"errors": {"sweep": 3}})))
    ck("stall: no new findings for a while", any("no new findings" in r for r in detect_stall({"errors": {}, "no_progress": 4})))
    # fork-without-models fallback (model_options=False) still captures the stall as a prioritized proposal
    import tempfile
    import scripts.proposal_backlog as pb
    _L, _P = pb.LEDGER, pb.PRIORITIZED
    with tempfile.TemporaryDirectory() as d:
        try:
            pb.LEDGER = Path(d) / "p.jsonl"; pb.PRIORITIZED = Path(d) / "pr.md"
            res = break_logjam(["proof gates RED across 3 health runs"], model_options=False)
            ck("with no models, the logjam is STILL captured as a forked owner-decision proposal", res["forked"] >= 1)
            ck("the fork is a governed candidate in the backlog", len(pb.load()) >= 1 and pb.load()[0]["serves_truth"] is False)
            ck("a prioritized backlog is (re)written", pb.PRIORITIZED.exists())
        finally:
            pb.LEDGER, pb.PRIORITIZED = _L, _P
    print("\n" + ("PASS - stall_breaker: detects stalls (gates red / repeated failure / no progress), breaks them by "
                  "deliberating (Kimi+GLM, Claude in /loop) for DIVERGENT options forked into the scored backlog, and — "
                  "if no clean option — captures the stall as a prioritized owner decision. Thin wrapper; serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    if "--break" in argv:
        try:
            from scripts.flywheel_orchestrator import load_state
            reasons = detect_stall(load_state())
        except Exception:
            reasons = []
        res = break_logjam(reasons or ["manual --break invoked"])
        print(json.dumps(res, indent=1))
        return 0
    print("usage: stall_breaker.py --self-test | --break")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
