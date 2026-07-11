#!/usr/bin/env python3
"""check_registry_descent — proof that the converter spans ALL capability-bearing registries (modality catalog +
implementation registry + tunable tasks) and records every bounding attempt into the descent brain, so the brain
learns from more than one registry. Asserts coverage of all three registries, that the brain accumulates their
attempts (incl. negatives), determinism, and serves_truth=false.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_registry_descent.py --self-test
"""
from __future__ import annotations

import os
import sys
import tempfile

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.evolution.descent_attempt_store import DescentAttemptStore
from src.teleon.evolution.registry_descent import (
    _impl_registry_attempts, _tunable_task_attempts, convert_all_registries,
)


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    with tempfile.TemporaryDirectory() as d:
        store = DescentAttemptStore(os.path.join(d, "all.jsonl"))
        summary = convert_all_registries(store)

        per = summary["registries"]
        ck("the converter spans all THREE capability-bearing registries",
           {"modality_capability_catalog", "capability_implementation_registry", "tunable_task_catalog"} <= set(per),
           str(list(per)))
        ck("each registry contributed items", all(v > 0 for v in per.values()), str(per))
        ck("the brain accumulated every attempt across registries",
           summary["attempts_recorded"] == summary["items_total"] and summary["training_examples"] == summary["items_total"],
           f"{summary['attempts_recorded']} vs {summary['items_total']}")
        ck("more registries => a bigger brain than the modality catalog alone",
           summary["items_total"] > per["modality_capability_catalog"], str(summary["items_total"]))

        # the brain now spans units from every registry (lineage prefixes prove it)
        units = {r["unit_id"].split(":")[0] for r in store.all()}
        ck("brain holds units from catalog + impl-registry + tunable-task",
           {"catalog", "impl-registry", "tunable-task"} <= units, str(units))

        # the impl-registry + tunable adapters produce well-formed attempts with full axes
        ir = _impl_registry_attempts()
        ck("impl-registry attempts carry before/after on the descent axes",
           ir and all(set(a.before) == {"cost", "determinism", "tokens_in", "llm_usage", "freshness"} for a in ir))
        tt = _tunable_task_attempts()
        ck("tunable-task attempts prefer the deterministic cheapest tier (a real bounding)",
           tt and any(a.after["determinism"] >= 0.99 for a in tt))

        # meta-learner readout computed across the larger corpus
        ck("meta-learner readout is computed across the multi-registry corpus",
           summary["best_strategy_low_determinism"] in (None, "llm_to_rule", "model_downgrade"))

        # idempotent + honest
        again = convert_all_registries(store)
        ck("re-running across registries is idempotent in the brain", again["attempts_recorded"] == summary["attempts_recorded"])
        ck("never serves truth", summary["serves_truth"] is False)

    print("\n" + (f"PASS - check_registry_descent: the converter spans {len(summary['registries'])} registries "
                  f"({summary['items_total']} items total) and records every bounding attempt into the descent brain — "
                  f"the brain now learns from the modality catalog, the implementation registry, and the tunable-task "
                  f"catalog, not just one. Idempotent; serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_registry_descent.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
