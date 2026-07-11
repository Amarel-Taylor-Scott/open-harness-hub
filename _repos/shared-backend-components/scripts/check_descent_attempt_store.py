#!/usr/bin/env python3
"""check_descent_attempt_store — proof of the descent BRAIN + data store: the canonical, append-only, lossless record
of EVERY unbounded->bounded attempt, doubling as (1) the meta-learner's memory and (2) the training corpus for a model
that learns to pick the best descent move. Asserts idempotent append, that FAILURES/losers are RETAINED (negatives for
training), that the training corpus carries features+label+reward, that best_strategy_for is COMPUTED from records, and
that nothing serves truth. Internal infra now; OpenDistillationHub public-revenue candidate later.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_descent_attempt_store.py --self-test
"""
from __future__ import annotations

import os
import sys
import tempfile

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.evolution.descent_attempt_store import AXES, DescentAttempt, DescentAttemptStore
from src.teleon.evolution.descent_axes import is_axis
from src.teleon.evolution.meta_learner import from_brain


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    with tempfile.TemporaryDirectory() as d:
        store = DescentAttemptStore(os.path.join(d, "attempts.jsonl"))

        # a WIN: an LLM step turned into a deterministic rule — cost->0, determinism->1 (canonical axes)
        win = DescentAttempt("employment-agency-extract", "llm_to_rule",
                             before={"cost": 0.30, "determinism": 0.2, "tokens_in": 800, "llm_usage": 75, "freshness": 0.0},
                             after={"cost": 0.0, "determinism": 1.0, "tokens_in": 0, "llm_usage": 0, "freshness": 1.0},
                             outcome="converged", losers=("model_downgrade",), rollback_target="v1", raw_ref="raw#1")
        # a partial win via a different strategy on a similar unit
        win2 = DescentAttempt("invoice-extract", "model_downgrade",
                              before={"cost": 0.30, "determinism": 0.2, "tokens_in": 800, "llm_usage": 75, "freshness": 0.5},
                              after={"cost": 0.03, "determinism": 0.2, "tokens_in": 600, "llm_usage": 8, "freshness": 0.5},
                              outcome="improved")
        # a FAILURE (must be retained as a training NEGATIVE)
        fail = DescentAttempt("legal-clause-extract", "llm_to_rule",
                              before={"cost": 0.30, "determinism": 0.2, "tokens_in": 900, "llm_usage": 75, "freshness": 0.0},
                              after={"cost": 0.30, "determinism": 0.2, "tokens_in": 900, "llm_usage": 75, "freshness": 0.0},
                              outcome="failed")
        store.append(win); store.append(win2); store.append(fail)

        ck("every descent axis is recorded in before/after", set(win.before) == set(AXES) and set(win.after) == set(AXES))
        ck("the brain's axes are CANONICAL descent_axes (single-sourced, no drift)", all(is_axis(a) for a in AXES))

        # idempotent: re-appending the same attempt does not duplicate
        store.append(win)
        ck("append is idempotent (content-hash dedupe)", len(store.all()) == 3, str(len(store.all())))

        # lossless: the failure is RETAINED (training needs negatives)
        recs = store.all()
        ck("FAILED attempts are retained (lossless — negatives kept for training)",
           any(r["outcome"] == "failed" for r in recs) and any(not r["success"] for r in recs))
        ck("losers + rollback_target + raw_ref are preserved (lineage)",
           any(r["losers"] == ["model_downgrade"] and r["rollback_target"] == "v1" and r["raw_ref"] == "raw#1" for r in recs))

        # the reward signal is computed (the training label's value)
        wrec = next(r for r in recs if r["unit_id"] == "employment-agency-extract")
        ck("reward deltas are computed (cost_saved/determinism_gain/tokens_in_saved)",
           wrec["reward"]["cost_saved"] == 0.3 and wrec["reward"]["determinism_gain"] == 0.8 and wrec["reward"]["tokens_in_saved"] == 800)

        # the training corpus carries features + label + reward + success, INCLUDING the negative
        ex = store.training_examples()
        ck("training corpus = features(before) + label(strategy) + reward + success, for EVERY attempt incl. negatives",
           len(ex) == 3 and all({"features", "label", "reward", "success"} <= set(e) for e in ex)
           and any(e["success"] is False for e in ex))

        # the meta-learner readout is COMPUTED from records (not a hardcoded table)
        best = store.best_strategy_for({"determinism": 0.2})
        ck("best_strategy_for is computed from records (llm_to_rule wins for the 0.2-determinism bucket: bigger cost saved)",
           best == "llm_to_rule", str(best))
        ck("best_strategy_for returns None when no record matches the profile", store.best_strategy_for({"determinism": 0.9}) is None)

        st = store.stats()
        ck("stats give per-strategy success rate (llm_to_rule: 1 win / 1 fail = 0.5)",
           st["llm_to_rule"]["success_rate"] == 0.5 and st["llm_to_rule"]["n"] == 2)
        ck("nothing serves truth", all(r["serves_truth"] is False for r in recs))

        # CANONICAL BRAIN: the meta_learner READS this store (no parallel storage) and recommends from it
        ml = from_brain(store.all())
        rec = ml.recommend_strategy("employment-agency-extract", 1.0)
        ck("meta_learner reads the canonical brain and returns a recommendation (brain is the single store)",
           isinstance(rec, dict) and rec.get("strategy") and ml.count("employment-agency-extract", 1.0) >= 1, str(rec))

        # deterministic
        store2 = DescentAttemptStore(os.path.join(d, "a2.jsonl"))
        store2.append(win)
        ck("deterministic attempt_id (same content -> same id across stores)",
           store2.all()[0]["attempt_id"] == wrec["attempt_id"])

    print("\n" + ("PASS - check_descent_attempt_store: the canonical BRAIN + store for every unbounded->bounded attempt — "
                  "append-only + idempotent, LOSSLESS (failures + losers retained as training negatives), reward deltas "
                  "computed, a training corpus (features+label+reward) and a computed meta-learner readout "
                  "(best_strategy_for) so the system gets smarter at the descent over time. serves_truth=false. "
                  "Internal infra now; OpenDistillationHub public-revenue candidate later."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_descent_attempt_store.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
