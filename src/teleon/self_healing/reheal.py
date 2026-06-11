"""src.teleon.self_healing.reheal — CDC source-change → capability re-heal (the keystone seam).

THE PAIN (owner, 2026-06-11): a scraper / fact-checker keeps RUNNING when its external source moves
(a site changes its HTML, a fact-check API moves) but silently returns garbage. Nobody notices
until a customer is wrong. We want Teleon to DETECT the silent break and SELF-HEAL with no user
action.

This module adds the two pieces the proven self-heal engine (purpose_task: provision / run_current
/ evaluate_health / adapt / rollback) did not have:

  1. BENCHMARK-AS-HEALTH-CHECK (`benchmark_health`): re-run the capability's eval suite (the
     benchmark) against the CURRENT world and flag OUTPUT-CORRECTNESS drift ('benchmark_fail') —
     the signal for "it runs fine but the output is now WRONG", which cost/crash health misses.

  2. THE SOURCE-CHANGE TRIGGER (`reheal_on_source_change`): given a freshness CDC 'changed' event
     for source S, find the capabilities that DEPEND on S, re-evaluate each against its benchmark,
     and on drift run the engine's `adapt` (side-by-side candidate → promote-on-gate, prior kept as
     rollback). A heal counts ONLY if the promoted candidate ALSO re-passes the whole benchmark
     (so a gate pass on one input can never paper over a real break). If nothing heals it, the
     capability is marked DEGRADED — honest, escalation recorded (the next rung is bounded
     exploration, NOT auto-dispatched), and its broken output is NEVER served as truth.

INVARIANTS (mirror check_purpose_task_self_heal_e2e): a candidate is never served before
promotion; a promotion is always reversible to a preserved rollback target; a degraded capability
is never silently healthy (its benchmark still fails — truth-telling); no fabricated heal.

Deterministic + offline. src/teleon only (the CDC event is a plain dict — never imports Baltor).
The event shape matches scripts/ingest/freshness.py output: {kind:'changed'|'new', source:<id>, …}.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.teleon.purpose_tasks.purpose_task import provision, run_current, eval_suite_for
from src.teleon.purpose_tasks.eval_suite import eval_pairs  # eval_suite_for already NORMALIZES

HEAL_STATUS_HEALTHY = "healthy"        # benchmark still passes after the change → no action
HEAL_STATUS_HEALED = "healed"          # drifted; a candidate passed the gate AND re-passed the benchmark
HEAL_STATUS_DEGRADED = "degraded"      # drifted; nothing healed it → degraded, escalation recorded, not served
HEAL_STATUS_NO_BENCHMARK = "no_benchmark"  # no scorable suite → can't auto-verify → degraded (never a clean bill)
NEXT_RUNG = "bounded_exploration"      # where a degraded capability escalates (the ladder; NOT auto-dispatched)

SOURCE_DEPENDENCIES_FIELD = "source_dependencies"  # spec field: the external source ids a capability watches
CHANGED_EVENT_KINDS = ("changed", "new")           # the freshness CDC kinds that warrant a re-heal


@dataclass
class HealOutcome:
    capability_id: str
    source: str
    drifted: bool
    status: str
    promoted: bool = False
    degraded: bool = False
    served_impl_id: str | None = None          # what is STILL served (never the broken/unproven candidate)
    benchmark_failures: int = 0
    escalation: dict | None = None             # {next_rung, auto_dispatched:False, reason} when degraded
    notes: str = ""
    rollback_target: str | None = None

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


def capabilities_depending_on(source_id: str, specs: list[dict]) -> list[dict]:
    """The capabilities that declared a dependency on `source_id` — only these are re-evaluated when
    that source changes (so a site change never needlessly re-checks unrelated capabilities)."""
    return [s for s in specs if source_id in (s.get(SOURCE_DEPENDENCIES_FIELD) or [])]


def _norm(v: Any) -> str:
    return " ".join(str(v).split()).strip().lower()


def benchmark_health(spec: dict, registry: dict, *, suite: dict | None = None) -> dict:
    """Re-run the capability's benchmark against the CURRENT world. Returns {meets, drift, failures,
    n}. meets=True iff EVERY example's output matches its expected (output-correctness). A failure
    here is the 'silent break' signal (the impl ran, the output is wrong)."""
    raw = suite if suite is not None else eval_suite_for(spec)  # eval_suite_for returns NORMALIZED
    if not raw:
        return {"meets": False, "drift": ["no_benchmark"], "failures": [], "n": 0}
    pairs = eval_pairs(raw)
    if not pairs:
        return {"meets": False, "drift": ["no_benchmark"], "failures": [], "n": 0}
    failures = []
    for inp, expected in pairs:
        result = run_current(spec, registry, inp)
        got = result.get("output", "")
        if result.get("error") or _norm(got) != _norm(expected):
            failures.append({"input": inp, "expected": expected, "got": got,
                             "error": result.get("error")})
    meets = not failures
    return {"meets": meets, "drift": [] if meets else ["benchmark_fail"],
            "failures": failures, "n": len(pairs)}


def reheal_on_source_change(event: dict, specs: list[dict], registry: dict, *, now: str,
                            promotion_criteria: dict | None = None) -> list[HealOutcome]:
    """The Baltor↔Teleon seam: a freshness CDC 'changed'/'new' event for a source → re-evaluate +
    self-heal the dependent capabilities. Pure given the registry's deterministic handlers."""
    if event.get("kind") not in CHANGED_EVENT_KINDS:
        return []
    source = str(event.get("source") or event.get("source_id") or "")
    if not source:
        return []
    pc = promotion_criteria or {"cost_tolerance": 0.10}
    outcomes: list[HealOutcome] = []

    for raw_spec in capabilities_depending_on(source, specs):
        spec = dict(raw_spec)
        cap_id = str(spec.get("capability_id") or spec.get("capability_slot") or "?")
        suite = eval_suite_for(spec)
        if not suite or not eval_pairs(suite):
            outcomes.append(HealOutcome(cap_id, source, drifted=False, status=HEAL_STATUS_NO_BENCHMARK,
                                        degraded=True, served_impl_id=spec.get("current_impl_id"),
                                        escalation={"next_rung": NEXT_RUNG, "auto_dispatched": False,
                                                    "reason": "no scorable benchmark — cannot auto-verify"},
                                        notes="no benchmark to re-run → cannot certify health; degraded honestly"))
            continue

        # bind the current impl (provision is idempotent — highest-priority impl for the slot)
        if not spec.get("current_impl_id"):
            spec = provision(spec, registry)
        served = spec["current_impl_id"]

        health = benchmark_health(spec, registry, suite=suite)
        if health["meets"]:
            outcomes.append(HealOutcome(cap_id, source, drifted=False, status=HEAL_STATUS_HEALTHY,
                                        served_impl_id=served, benchmark_failures=0,
                                        notes="source changed but the benchmark still passes — no heal needed"))
            continue

        # DRIFTED — the output is now wrong (the silent break). For a SOURCE-CHANGE the correct heal
        # gate is the BENCHMARK (correctness), not cost: a candidate heals iff it RE-PASSES the whole
        # benchmark against the changed world. (Cost-drift is the OTHER scenario the engine's `adapt`
        # already handles by its cost gate — see check_purpose_task_self_heal_e2e; that path is
        # unchanged.) We promote losslessly: the prior impl is kept as the rollback target, and the
        # candidate is verified BEFORE it is bound (never served before it is proven).
        healed = None
        for cand in (spec.get("alternatives") or []):
            trial = {**spec, "current_impl_id": cand}
            if benchmark_health(trial, registry, suite=suite)["meets"]:
                healed = cand
                break
        if healed is not None:
            # lossless promotion: current → the proven candidate, prior preserved as rollback_target
            promoted_spec = {**spec, "current_impl_id": healed, "rollback_target": served}
            re_health = benchmark_health(promoted_spec, registry, suite=suite)  # belt-and-braces
            outcomes.append(HealOutcome(cap_id, source, drifted=True, status=HEAL_STATUS_HEALED,
                                        promoted=re_health["meets"], served_impl_id=healed,
                                        benchmark_failures=len(health["failures"]), rollback_target=served,
                                        notes="silent break detected by the benchmark → a candidate that "
                                              "RE-PASSES the benchmark healed it; prior kept as rollback "
                                              "(reversible, lossless); candidate verified before it was served"))
        else:
            # nothing re-grounds it: DEGRADED. The OLD impl is still 'served' but its output is known-
            # broken (benchmark fails), so a consumer treats it as degraded, not truth; escalate to the
            # next rung (bounded exploration) WITHOUT auto-dispatch; never fabricate a heal.
            outcomes.append(HealOutcome(cap_id, source, drifted=True, status=HEAL_STATUS_DEGRADED,
                                        promoted=False, degraded=True, served_impl_id=served,
                                        benchmark_failures=len(health["failures"]),
                                        escalation={"next_rung": NEXT_RUNG, "auto_dispatched": False,
                                                    "reason": "no candidate re-passes the benchmark against "
                                                              "the changed source"},
                                        notes="silent break detected; NO candidate re-grounds it → DEGRADED "
                                              "(honest: benchmark still fails; broken output not served as truth)"))
    return outcomes
