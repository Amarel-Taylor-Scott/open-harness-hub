"""scripts.eval.lift_producer — PRODUCE a measured-lift result per capability, then DECIDE.

The gap (rubric + promotion_bridge's own critique + the self-improving-runtime vision): the bridge
CONSUMES a measured-lift result and gates promotion on lift + durability — but nothing PRODUCED one
per capability. This closes the loop, as a THIN orchestrator over the proven protocol (it does NOT
reimplement it):

    capability examples + a model route + the capability's impl
        → run_headtohead (paired, separately-judged, held-out: bare-model arm A vs pipeline arm B)
        → a measured-lift result (lift = pipeline − bare, durability_class, separate judge)
        → promotion_bridge.promotion_decision → promote / candidate / reject.

The bare-model arm is the model route answering the example ALONE (what you'd get without the
capability); the pipeline arm is the capability's deterministic impl. A positive measured lift means
the capability genuinely beats the raw model; a deterministic capability's lift is STRUCTURAL
(`deterministic_guarantee` — it won't close when the next model ships).

HONEST: with no reachable route the bare baseline is UNMEASURABLE → an `unmeasured` result (never a
fabricated positive lift) → the bridge rejects (unmeasured → reject), which is correct. The judge is
a SEPARATE object from both scorers by construction (run_headtohead raises on self-grading).

Reuses scripts.eval.measured_lift_headtohead (the protocol) + promotion_bridge (the gate) +
reason_codes (the taxonomy — never redefined). Deterministic self-test with an injected FakeRoute.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from scripts.eval.measured_lift_headtohead import run_headtohead, AbstainAwareEvaluator
from scripts.eval.promotion_bridge import promotion_decision

#: a deterministic capability's lift is STRUCTURAL — it is the deterministic guarantee itself
#: (reason_codes.LIFT_REASONS; durability_class('deterministic_guarantee') == 'structural').
DETERMINISTIC_LIFT_REASON = "deterministic_guarantee"


def capability_items(examples: Iterable[tuple], *, lift_reason: str = DETERMINISTIC_LIFT_REASON) -> list[dict]:
    """Build held-out head-to-head items from a capability's (input, expected) eval pairs."""
    return [{"prompt": inp, "correct_answer": expected, "lift_reason": lift_reason}
            for inp, expected in examples]


def _coerce_answer(out: Any) -> str | None:
    if out is None:
        return None
    if isinstance(out, str):
        return out
    if isinstance(out, dict):  # a RunnerResult-shaped impl output
        return str(out.get("output", ""))
    return str(out)


def _route_scorer(route: Any, instruction: str) -> Callable[[dict], str | None]:
    """Arm A: the BARE model answering the prompt alone (no capability)."""
    def score(item: dict) -> str | None:
        try:
            return _coerce_answer(route.complete(instruction, str(item["prompt"]),
                                                 max_tokens=200, temperature=0.0))
        except Exception:  # an arm failure is a None score (the harness handles it), never a fake answer
            return None
    return score


def _impl_scorer(impl: Callable[[Any], Any]) -> Callable[[dict], str | None]:
    """Arm B: the capability's IMPL (the governed pipeline) answering the prompt."""
    def score(item: dict) -> str | None:
        try:
            return _coerce_answer(impl(item["prompt"]))
        except Exception:
            return None
    return score


def _route_reachable(route: Any) -> bool:
    if route is None:
        return False
    health = getattr(route, "health", None)
    return bool(health()) if callable(health) else True


def produce_lift(examples: Iterable[tuple], *, route: Any, impl: Callable[[Any], Any],
                 instruction: str = "", lift_reason: str = DETERMINISTIC_LIFT_REASON) -> dict:
    """Measure the capability's lift over the bare model on its examples. Returns a head-to-head
    result (the shape promotion_bridge consumes), or an honest `unmeasured` result with no route."""
    items = capability_items(examples, lift_reason=lift_reason)
    if not _route_reachable(route):
        return {"measurement_kind": "unmeasured", "lift": None, "n": len(items),
                "reason": "no reachable model route — the bare-model baseline is unmeasurable (honest, "
                          "not a fabricated lift)"}
    return run_headtohead(items, bare_model_scorer=_route_scorer(route, instruction),
                          pipeline_scorer=_impl_scorer(impl), evaluator=AbstainAwareEvaluator(),
                          lift_reason=lift_reason)


def produce_and_decide(examples: Iterable[tuple], *, route: Any, impl: Callable[[Any], Any],
                       instruction: str = "", lift_reason: str = DETERMINISTIC_LIFT_REASON,
                       policy: Any = None, gate_evidence: dict | None = None) -> dict:
    """The closed loop: produce a measured lift, then gate promotion on it. Returns
    {lift_result, decision} — `decision` is the bridge's promote/candidate/reject verdict.
    `policy` is a promotion_bridge.PromotionPolicy (None ⇒ the bridge's DEFAULT_POLICY)."""
    result = produce_lift(examples, route=route, impl=impl, instruction=instruction, lift_reason=lift_reason)
    decision = (promotion_decision(result, gate_evidence or {}) if policy is None
                else promotion_decision(result, gate_evidence or {}, policy=policy))
    return {"lift_result": result, "decision": decision}


# ---------------------------------------------------------------- self-test (offline, deterministic)

def _self_test() -> int:
    checks = []

    def ck(n, ok):
        checks.append((n, ok))

    # a deterministic date-normalizer capability: the IMPL is right; a bare model gets it WRONG
    import re

    def date_impl(text: str) -> str:
        return re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
                      lambda m: f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}", str(text))

    examples = [("Filed 3/14/2026", "Filed 2026-03-14"), ("Due 12/1/2025", "Due 2025-12-01"),
                ("Set 7/4/1999", "Set 1999-07-04"), ("On 1/2/2030", "On 2030-01-02")]

    class FakeRoute:           # the BARE model — answers WRONG (returns the input unchanged)
        def health(self):
            return True
        def complete(self, system, user, **kw):
            return str(user)   # never normalizes → fails every example

    class FakePerfectRoute:    # the bare model is ALREADY as good as the impl → NO lift
        def health(self):
            return True
        def complete(self, system, user, **kw):
            return date_impl(user)

    out = produce_and_decide(examples, route=FakeRoute(), impl=date_impl,
                             lift_reason=DETERMINISTIC_LIFT_REASON, gate_evidence={})
    lift = out["lift_result"].get("lift")
    ck("produced a REAL positive lift (the deterministic impl beats the bare model)",
       lift is not None and lift > 0)
    ck("durability is structural (a deterministic guarantee won't close when the next model ships)",
       out["lift_result"].get("durability_class") == "structural")
    ck("the closed loop PROMOTES on a real durable positive lift",
       out["decision"]["decision"] == "promote")

    out_nolift = produce_and_decide(examples, route=FakePerfectRoute(), impl=date_impl, gate_evidence={})
    ck("a bare model already as good → ZERO lift (no fabricated positive)",
       (out_nolift["lift_result"].get("lift") or 0) == 0)
    ck("no measured lift → REJECT (a capability that doesn't beat the model isn't admitted)",
       out_nolift["decision"]["decision"] == "reject")

    out_offline = produce_and_decide(examples, route=None, impl=date_impl, gate_evidence={})
    ck("no route → UNMEASURED (honest, never a fabricated lift)",
       out_offline["lift_result"].get("measurement_kind") == "unmeasured")
    ck("unmeasured → REJECT (fail-closed: can't promote what we couldn't measure)",
       out_offline["decision"]["decision"] == "reject")

    ck("the judge is a SEPARATE object from the scorers (self-grading impossible by construction)",
       lift is not None)  # run_headtohead would have raised otherwise — reaching here proves it
    ck("deterministic: same inputs → identical lift",
       produce_lift(examples, route=FakeRoute(), impl=date_impl).get("lift")
       == produce_lift(examples, route=FakeRoute(), impl=date_impl).get("lift"))

    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    print(("PASS — " if not failed else "FAIL — ")
          + f"lift_producer: {len(checks) - len(failed)}/{len(checks)} — produces a REAL measured lift "
            "(bare model vs the capability's impl, separately judged) and closes the loop to the promotion "
            "gate; unmeasured offline is honest, never faked.")
    return 1 if failed else 0


if __name__ == "__main__":
    import sys
    sys.exit(_self_test() if "--self-test" in sys.argv else _self_test())
