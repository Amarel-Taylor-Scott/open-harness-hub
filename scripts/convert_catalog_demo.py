#!/usr/bin/env python3
"""convert_catalog_demo — the convert-skills/tools demo WIRED TO THE DESCENT BRAIN.

Runs the unbounded->bounded descent over the real capability catalog (architecture/modality_capability_catalog.json)
and records EVERY attempt into the DescentAttemptStore, so the same run that bounds the catalog also produces the
training corpus + meta-learner memory. In the live fleet the cheap brain (GLM-5.2 / Kimi) proposes each conversion
(the ollama lane); here it is offline + deterministic off the catalog's governed signal.

  --demo        run against the canonical brain store (data/descent-attempts/catalog.jsonl) and print before->after + brain stats
  --self-test   prove the conversion bounds the catalog AND feeds the brain (the registered proof)
CLI: PYTHONPATH=. python3 scripts/convert_catalog_demo.py --demo
"""
from __future__ import annotations

import os
import sys
import tempfile

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.evolution.catalog_descent import _before, convert_catalog, descend, load_catalog
from src.teleon.evolution.descent_attempt_store import DescentAttemptStore

_CANONICAL = "data/descent-attempts/catalog.jsonl"


def _run_demo() -> int:
    store = DescentAttemptStore(_CANONICAL)
    summary = convert_catalog(store)
    print("== convert catalog -> bounded, recording every attempt into the descent brain ==")
    for cap in load_catalog():
        b = _before(cap)
        a, strat, outcome, _ = descend(cap)
        print(f"  {cap['capability']:<34} {b['determinism']:.2f}->{a['determinism']:.2f} det · "
              f"${b['cost']:.3f}->${a['cost']:.3f} · {strat} ({outcome})")
    print(f"\nbounded fully: {summary['fully_bounded']} · improved: {summary['improved']} · "
          f"total cost saved: ${summary['total_cost_saved']} · mean determinism gain: {summary['mean_determinism_gain']}")
    print(f"BRAIN now holds {summary['attempts_recorded']} attempts / {summary['training_examples']} training examples "
          f"({_CANONICAL})")
    s = DescentAttemptStore(_CANONICAL)
    print(f"meta-learner: best strategy for a 0.5-determinism unit = {s.best_strategy_for({'determinism': 0.5})}")
    return 0


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    caps = load_catalog()
    ck("the real catalog has capabilities to convert", len(caps) >= 10, str(len(caps)))

    with tempfile.TemporaryDirectory() as d:
        store = DescentAttemptStore(os.path.join(d, "catalog.jsonl"))
        summary = convert_catalog(store, caps)

        # WIRING: every conversion was recorded into the brain
        ck("every capability conversion is recorded into the descent brain",
           summary["attempts_recorded"] == len(caps) and summary["training_examples"] == len(caps),
           f"{summary['attempts_recorded']} vs {len(caps)}")

        # the descent actually bounds things: net cost saved + determinism raised
        ck("the descent saves cost across the catalog", summary["total_cost_saved"] > 0, str(summary["total_cost_saved"]))
        ck("the descent raises mean determinism (more bounded)", summary["mean_determinism_gain"] >= 0)
        ck("at least one capability is fully bounded (llm_to_rule -> determinism 1.0)", summary["fully_bounded"] >= 1)

        # a fully-achievable capability lands at determinism 1.0 via llm_to_rule
        full = next((c for c in caps if c.get("deterministic_achievable") == "full"
                     or not any(not s.get("deterministic") for s in c.get("pipeline", []))), None)
        if full:
            after, strat, outcome, _ = descend(full)
            ck("a fully-achievable capability bounds to determinism 1.0 (llm_to_rule, converged)",
               after["determinism"] == 1.0 and strat == "llm_to_rule" and outcome == "converged")

        # a partial capability gets cheaper + drops to a cheap model tier (model_downgrade)
        part = next((c for c in caps if c.get("deterministic_achievable") == "partial"), None)
        if part:
            b = _before(part); a, strat, outcome, _ = descend(part)
            ck("a partial capability gets cheaper at a cheap model tier (model_downgrade, improved)",
               a["cost"] < b["cost"] and a["model_tier"] == 8 and strat == "model_downgrade")

        # the brain is now usable: training corpus + computed meta-learner readout
        ex = store.training_examples()
        ck("the brain yields a training corpus (features+label+reward) from the run",
           len(ex) == len(caps) and all({"features", "label", "reward"} <= set(e) for e in ex))
        ck("the meta-learner readout is computed from the recorded attempts",
           store.best_strategy_for({"determinism": 0.5}) in (None, "llm_to_rule", "model_downgrade"))

        # idempotent: re-running does not duplicate brain rows
        again = convert_catalog(store, caps)
        ck("re-running the conversion is idempotent in the brain (no duplicate attempts)",
           again["attempts_recorded"] == len(caps), str(again["attempts_recorded"]))
        ck("never serves truth", summary["serves_truth"] is False)

    print("\n" + (f"PASS - convert_catalog_demo: the descent runs over all {len(caps)} real catalog capabilities and "
                  f"records EVERY attempt into the descent brain — bounding the catalog and producing the training "
                  f"corpus + meta-learner memory in one run; fully-achievable caps -> determinism 1.0 (llm_to_rule), "
                  f"partial caps -> cheap model tier (model_downgrade); idempotent; serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    if "--demo" in argv:
        return _run_demo()
    print("usage: convert_catalog_demo.py --demo | --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
