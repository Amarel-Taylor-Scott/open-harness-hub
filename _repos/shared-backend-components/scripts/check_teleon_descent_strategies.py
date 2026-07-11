#!/usr/bin/env python3
"""check_teleon_descent_strategies — proof for the descent-strategy registry + the generic descender.

Descent is a MENU of axes, extensible by config. This proves the registry + generic descender cover the
trust/robustness/openness axes uniformly:
  * the canonical axis set spans efficiency (determinism/cost/latency/llm_usage/freshness) AND trust/robustness/
    openness (verifiability/reliability/locality/specialization/privacy/reproducibility/portability/resilience/
    energy/safety) — 15 axes, single source.
  * the registry declares one strategy per trust/robustness axis (fork mechanism + what it BINDS + the machinery it
    REUSES + how it is GOVERNED + how it is MEASURED); every `improves` axis is a real DESCENT_AXES entry.
  * descend(capability, axis) builds a valid fork for ANY registered axis (parent preserved, lossless), records
    improvement_axes, is policy-checked, and never serves truth — adding an axis is a registry entry, not new code.
  * specialization co-improves cost+latency; an unknown axis fails loud; measure_descent counts all axes.

CLI: python3 _repos/shared-backend-components/scripts/check_teleon_descent_strategies.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.evolution import (
    DESCENT_AXES,
    descend,
    descent_strategies,
    descent_strategy,
    measure_descent,
    strategies_for_axis,
)
from src.teleon.governance import load_policy

_NEW_AXES = ("verifiability", "reliability", "locality", "specialization", "privacy",
             "reproducibility", "portability", "resilience", "energy", "safety")


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except (KeyError, ValueError):
        return True


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # FULL MENU: efficiency + trust/robustness/openness axes (15), single source.
    ck("the canonical axis set spans efficiency + trust/robustness/openness (>=15 axes, extensible)",
       len(DESCENT_AXES) >= 15 and set(_NEW_AXES) <= set(DESCENT_AXES)
       and {"determinism", "cost", "latency", "llm_usage", "freshness"} <= set(DESCENT_AXES))

    # REGISTRY: a strategy per new axis; every 'improves' is a real axis; required metadata present.
    strats = descent_strategies()
    ck("the registry has a strategy for every trust/robustness/openness axis", set(_NEW_AXES) <= set(strats))
    ck("every strategy's improves[] axes are real DESCENT_AXES, with binding/reuses/governance/measurement metadata",
       all(all(a in DESCENT_AXES for a in s["improves"]) and s.get("binds") and s.get("reuses")
           and s.get("governed_by") and s.get("measurement") for s in strats.values()))

    # GENERIC DESCEND along every new axis -> a valid fork + record.
    records = []
    for axis in _NEW_AXES:
        r = descend(f"cap-{axis}", axis, category="other")
        records.append(r["record"])
        graph_kinds = {n["kind"] for n in r["graph"]["runners"]}
        ck(f"descend('{axis}') builds a valid fork that improves {axis}, preserves the parent, never truth",
           axis in r["improves"] and axis in r["record"]["improvement_axes"]
           and r["fork_kind"] in graph_kinds and "model" in graph_kinds
           and r["record"]["lossless"] is True and r["serves_truth"] is False and r["graph"]["serves_truth"] is False,
           str(r["fork_kind"]))

    # specialization co-improves cost + latency (a narrow small model is cheaper + faster).
    spec = descend("cap-spec", "specialization")
    ck("specialization co-improves cost + latency (small specialized model)",
       {"cost", "latency"} <= set(spec["improves"]) and spec["record"]["per_call_cost_after"] < spec["record"]["per_call_cost_before"])

    # GOVERNANCE: a trust-axis fork on a non-deterministic runner is HELD by a deterministic-only org (adding a
    # receipt/redundancy does not make it deterministic); a permissive org accepts it.
    held = descend("cap-v", "verifiability", parent_determinism=0.2, policy=load_policy("deterministic-audit"))
    ck("a verifiability fork on a model runner is HELD by a deterministic-only org (not deterministic)",
       held["applied"] is False)
    ok_perm = descend("cap-v2", "verifiability", parent_determinism=0.2, policy=load_policy("default-permissive"))
    ck("a permissive org accepts the verifiability fork", ok_perm["applied"] is True)
    # a verifiability fork on an ALREADY-deterministic runner is accepted even by the strict org.
    det_ok = descend("cap-v3", "verifiability", parent_determinism=1.0, policy=load_policy("deterministic-audit"))
    ck("a verifiability fork on a deterministic runner is accepted by a deterministic-only org", det_ok["applied"] is True)

    # FORMAL-PROOF verifiability strategy (vs Pramaana): an axis can have MULTIPLE strategies; descend by id.
    vstrats = strategies_for_axis("verifiability")
    ck("verifiability has MULTIPLE strategies (receipt_binding + formal_proof_verification)",
       {s["strategy_id"] for s in vstrats} >= {"receipt_binding", "formal_proof_verification"})
    fp = descend("reg-tax-deduction", "verifiability", strategy_id="formal_proof_verification")
    ck("descend(strategy_id='formal_proof_verification') builds a formally_verified fork improving verifiability+determinism",
       fp["fork_kind"] == "formally_verified" and {"verifiability", "determinism"} <= set(fp["improves"])
       and any(r["kind"] == "formally_verified" for r in fp["graph"]["runners"]))
    ck("the formal-proof strategy COMPOSES with freshness + source-authority (strictly broader than a static prover)",
       "freshness" in descent_strategy("formal_proof_verification")["reuses"]
       and "authorit" in descent_strategy("formal_proof_verification")["reuses"].lower())
    ck("descend by an unknown strategy_id fails loud",
       _raises(lambda: descend("c", "verifiability", strategy_id="vibes_based_proof")))

    # unknown axis fails loud.
    raised = False
    try:
        descend("cap-x", "telepathy")
    except KeyError:
        raised = True
    ck("descending an unregistered axis fails loud", raised)

    # MEASUREMENT: the harness counts improvements across ALL the new axes.
    m = measure_descent(records)
    ck("measure_descent counts an improvement on every new axis",
       all(m["improved_by_axis"].get(a, 0) >= 1 for a in _NEW_AXES) and m["capabilities_descended"] == len(_NEW_AXES))

    # deterministic
    ck("generic descent is deterministic", descend("cap-r", "reliability") == descend("cap-r", "reliability"))

    print("\n" + ("PASS - check_teleon_descent_strategies: descent is an extensible MENU — 15 canonical axes "
                  "(efficiency + trust/robustness/openness) with a config-driven strategy registry + a generic "
                  "descender that builds a valid, lossless, policy-checked, never-truth fork for ANY registered "
                  "axis (verifiability/reliability/locality/specialization/privacy/reproducibility/portability/"
                  "resilience/energy/safety); adding an axis is a registry entry, not new code; measured per axis."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
