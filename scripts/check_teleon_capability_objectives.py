#!/usr/bin/env python3
"""check_teleon_capability_objectives — proof for Teleon's capability-OBJECTIVE flexibility layer.

Teleon is the logic; THIS lets a tenant/task prioritize what matters and have selection + the descent follow it:
  * MEASUREMENT — a MetricVector per implementation (cost / latency / llm_usage / determinism / accuracy).
  * FLEXIBILITY — a CapabilityObjective (presets + arbitrary weights) so the SAME candidates select DIFFERENT
    implementations under different priorities.
  * TRACEABILITY — select() returns a SelectionTrace (every candidate's score + weights + rationale); deterministic.
  * SAFETY > objective — a forbidden implementation is never selected, even if it scores best.
  * IT DRIVES THE DESCENT — for a model-vs-distilled-rule pair, cost/latency/llm/determinism objectives pick the
    cheap deterministic rule; an accuracy objective keeps the model. (The cost self-improvement, made tunable.)

CLI: python3 scripts/check_teleon_capability_objectives.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.objectives import PRESETS, MetricVector, ObjectiveError, select


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # A four-impl candidate set spanning the spectrum (cost · latency_ms · llm_calls · determinism · accuracy).
    candidates = [
        ("template",      MetricVector(cost=0.0,  latency=5,     llm_usage=0, determinism=1.0, accuracy=0.90)),
        ("deterministic", MetricVector(cost=0.0,  latency=20,    llm_usage=0, determinism=1.0, accuracy=0.95)),
        ("model",         MetricVector(cost=0.07, latency=800,   llm_usage=1, determinism=0.2, accuracy=0.98)),
        ("open_ended",    MetricVector(cost=0.5,  latency=30000, llm_usage=5, determinism=0.0, accuracy=0.99)),
    ]
    pick = lambda obj, **kw: select(candidates, PRESETS[obj], **kw)["chosen"]

    ck("minimize_cost selects a zero-cost (deterministic-tier) impl", pick("minimize_cost") in {"template", "deterministic"})
    ck("minimize_latency selects a low-latency impl (template/deterministic, never the 800ms model)",
       pick("minimize_latency") in {"template", "deterministic"})
    ck("minimize_llm selects a NO-LLM impl", pick("minimize_llm") in {"template", "deterministic"})
    ck("maximize_determinism selects a fully-deterministic impl", pick("maximize_determinism") in {"template", "deterministic"})
    ck("maximize_accuracy selects the MOST-ACCURATE impl (model/open-ended)", pick("maximize_accuracy") in {"model", "open_ended"})

    # FLEXIBILITY: the SAME candidates, different objectives -> different implementations.
    chosen = {obj: pick(obj) for obj in PRESETS}
    ck("the SAME capability selects DIFFERENT impls under different objectives (>=2 distinct)",
       len(set(chosen.values())) >= 2, str(chosen))

    # TRACEABILITY + DETERMINISM
    trace = select(candidates, PRESETS["minimize_cost"])
    ck("the selection trace scores EVERY candidate + carries weights + rationale (traceable)",
       len(trace["ranked"]) == 4 and all("score" in r and "metrics" in r for r in trace["ranked"])
       and bool(trace["rationale"]) and set(trace["weights"]) >= {"cost", "latency", "determinism"})
    ck("selection never serves truth", trace["serves_truth"] is False)
    ck("selection is deterministic (same inputs -> same chosen + scores)",
       select(candidates, PRESETS["minimize_cost"]) == trace)

    # SAFETY > objective: forbidding the would-be WINNER excludes it; a different allowed impl wins instead.
    winner = select(candidates, PRESETS["maximize_accuracy"])["chosen"]
    safe = select(candidates, PRESETS["maximize_accuracy"], forbidden={winner})
    ck("a forbidden impl is EXCLUDED even when it would score best (safety beats the objective)",
       safe["chosen"] != winner and winner in safe["excluded_forbidden"])

    # empty / all-forbidden fails loud
    raised = False
    try:
        select(candidates, PRESETS["balanced"], forbidden={c for c, _ in candidates})
    except ObjectiveError:
        raised = True
    ck("an empty allowed set fails loud (never a silent pick)", raised)

    # IT DRIVES THE DESCENT: a model vs its distilled deterministic rule (slightly lower accuracy on novel inputs).
    descent = [
        ("model.extraction",         MetricVector(cost=0.07, latency=800, llm_usage=1, determinism=0.2, accuracy=0.98)),
        ("distilled_rule.extraction", MetricVector(cost=0.0,  latency=20,  llm_usage=0, determinism=1.0, accuracy=0.93)),
    ]
    dpick = lambda obj: select(descent, PRESETS[obj])["chosen"]
    ck("descent tuning: minimize_cost -> the distilled deterministic rule", dpick("minimize_cost") == "distilled_rule.extraction")
    ck("descent tuning: maximize_determinism -> the distilled deterministic rule", dpick("maximize_determinism") == "distilled_rule.extraction")
    ck("descent tuning: minimize_llm -> the distilled deterministic rule (0 model calls)", dpick("minimize_llm") == "distilled_rule.extraction")
    ck("descent tuning: maximize_accuracy -> KEEPS the model (the objective can also hold the descent back)",
       dpick("maximize_accuracy") == "model.extraction")

    print("\n" + ("PASS - check_teleon_capability_objectives: a capability is MEASURED on cost/latency/llm_usage/"
                  "determinism/accuracy; a CapabilityObjective (preset or weights) selects the best-fit impl with a "
                  "deterministic, traceable SelectionTrace; the SAME capability picks DIFFERENT impls under different "
                  "priorities; safety beats the objective (forbidden impls excluded); and the objective DRIVES the "
                  "descent — cost/latency/llm/determinism pick the distilled rule, accuracy keeps the model."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
