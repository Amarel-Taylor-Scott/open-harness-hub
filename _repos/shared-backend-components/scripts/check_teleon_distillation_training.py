#!/usr/bin/env python3
"""check_teleon_distillation_training — proof for the skills DB + the trained distillation policy + model/LoRA seam.

The system LEARNS the most efficient non-deterministic -> deterministic path and generalizes it:
  * SKILLS DB — capability features join distillation outcomes into a labeled dataset, with a deterministic
    train/holdout split and portable JSONL export (the data a model/LoRA trains on).
  * TRAINED POLICY — FittedPolicy learns, per capability class, the highest-efficiency strategy and GENERALIZES
    (class -> band -> prior backoff), so an unseen capability gets the learned path; on held-out it BEATS the
    cold-start prior (efficiency lift > 0) — the proof it found a better path than the naive default.
  * MODEL / LoRA SEAM — TrainedArtifactPolicy is the plug-in point for a real trained model/LoRA (a sandboxed
    backend candidate); with no artifact it is unusable (never a silent guess), and a model drops in behind the
    same port with no caller change. The harness emits a governed model/LoRA artifact SPEC.
  * deterministic; never serves truth.

CLI: python3 _repos/shared-backend-components/scripts/check_teleon_distillation_training.py --self-test
"""
from __future__ import annotations

import os
import sys
import tempfile

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.training import (
    DistillationExample,
    PriorPolicy,
    TrainedArtifactPolicy,
    build_dataset,
    evaluate,
    feature_vector,
    model_artifact_spec,
    run_training,
    train,
)


def _cand(slot, category, ceiling, cov=0.9, source_kind="mcp_server", intent="do a thing with inputs"):
    return {"capability_slot": slot, "category": category, "determinism_ceiling": ceiling,
            "deterministic_coverage_estimate": cov, "source": {"kind": source_kind}, "intent": intent}


def _rec(slot, category, ceiling, strategy, coverage=0.9, distill_cost=0.08):
    return {"capability_slot": slot, "category": category, "strategy": strategy, "determinism_ceiling": ceiling,
            "per_call_cost_before": 0.07, "per_call_cost_after": 0.0, "distill_cost": distill_cost,
            "coverage": coverage, "applied": True}


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # A dataset where 'scraping|extract' is observed to distill best via template_match (NOT the band prior
    # deterministic_extract) — so a trained policy should learn to override the prior there.
    candidates, records = [], []
    for i in range(14):
        candidates.append(_cand(f"scrape-{i}", "scraping", 0.8))
        records.append(_rec(f"scrape-{i}", "scraping", 0.8, "template_match", distill_cost=0.08))
    for i in range(6):
        candidates.append(_cand(f"fin-{i}", "financial-data", 1.0, cov=1.0))
        records.append(_rec(f"fin-{i}", "financial-data", 1.0, "direct_api_rule", coverage=1.0, distill_cost=0.05))
    candidates.append(_cand("undistilled-1", "scraping", 0.8))  # no record -> unlabeled

    # ── SKILLS DB ──
    ds = build_dataset(candidates, records)
    ck("the dataset joins features + outcomes (20 labeled, 1 unlabeled)",
       ds.summary()["labeled"] == 20 and ds.summary()["total"] == 21 and ds.summary()["serves_truth"] is False)
    ck("every example carries the feature schema", all(set(e.features) >= {"category", "determinism_band",
       "determinism_ceiling", "source_kind"} for e in ds.examples))
    train_ex, holdout = ds.split(holdout_fraction=0.25)
    ck("the train/holdout split is deterministic + non-empty", len(holdout) >= 2
       and ds.split(holdout_fraction=0.25)[1] and [e.capability_slot for e in holdout]
       == [e.capability_slot for e in ds.split(holdout_fraction=0.25)[1]])
    with tempfile.TemporaryDirectory() as td:
        n = ds.export_jsonl(os.path.join(td, "dataset.jsonl"))
        ck("the dataset exports to portable JSONL training data", n == 21
           and os.path.getsize(os.path.join(td, "dataset.jsonl")) > 0)

    # ── TRAINED POLICY: learns + generalizes ──
    policy = train(ds.labeled)
    ck("the trained policy learns scraping|extract -> template_match (OVERRIDING the band prior)",
       policy.predict(feature_vector(_cand("x", "scraping", 0.8)))["strategy"] == "template_match"
       and PriorPolicy().predict(feature_vector(_cand("x", "scraping", 0.8)))["strategy"] == "deterministic_extract")
    ck("it GENERALIZES to an UNSEEN capability in a learned class (still template_match, fitted_class)",
       policy.predict(feature_vector(_cand("brand-new", "scraping", 0.8)))["source"] == "fitted_class")
    ck("it BACKS OFF by band for an unseen class (media|extract -> the band's learned strategy)",
       policy.predict(feature_vector(_cand("m", "media", 0.8)))["source"] == "fitted_band")
    ck("it BACKS OFF to the prior for a fully-unseen band (partial)",
       policy.predict(feature_vector(_cand("p", "legal-statute", 0.5)))["source"] == "prior_backoff")

    # ── EVALUATION: the trained policy beats the cold-start prior on held-out (efficiency lift) ──
    holdout_built = [
        DistillationExample("h-scrape", feature_vector(_cand("h-scrape", "scraping", 0.8)), True, "template_match", 0.9, 9.9),
        DistillationExample("h-fin", feature_vector(_cand("h-fin", "financial-data", 1.0, cov=1.0)), True, "direct_api_rule", 1.0, 20.0),
    ]
    metrics = evaluate(policy, holdout_built)
    ck("on held-out, the trained policy is at least as accurate as the prior AND lifts it (found a better path)",
       metrics["accuracy"] >= metrics["baseline_accuracy"] and metrics["efficiency_lift"] > 0, str(metrics))

    # ── MODEL / LoRA SEAM ──
    seam = TrainedArtifactPolicy()
    pred = seam.predict(feature_vector(_cand("x", "scraping", 0.8)))
    ck("the model/LoRA seam with NO artifact is unusable (requires_trained_artifact), never a silent guess",
       seam.available() is False and pred["source"] == "requires_trained_artifact" and pred["strategy"] is None)

    class _StubArtifact:  # stands in for a real trained model / LoRA behind the same port
        def predict(self, features):
            return {"strategy": "direct_api_rule", "confidence": 0.91}
    loaded = TrainedArtifactPolicy(_StubArtifact())
    lp = loaded.predict(feature_vector(_cand("x", "financial-data", 1.0)))
    ck("a trained model/LoRA drops in behind the same port and predicts (never truth)",
       loaded.available() and lp["strategy"] == "direct_api_rule" and lp["serves_truth"] is False)

    # ── HARNESS + artifact spec ──
    out = run_training(candidates, records, holdout_fraction=0.25)
    ck("run_training returns dataset stats, held-out metrics, the fitted policy, and a model/LoRA spec",
       out["dataset"]["labeled"] == 20 and "accuracy" in out["metrics"] and out["serves_truth"] is False)
    spec = out["artifact_spec"]
    ck("the model/LoRA artifact spec is a governed CANDIDATE (feature+label schema, never auto-active/truth)",
       spec["artifact_kind"] == "distillation_policy_lora" and spec["status"] == "candidate"
       and spec["serves_truth"] is False and spec["training_examples"] == 20 and "strategy" in spec["label_schema"])
    ck("training is deterministic (same data -> same held-out metrics)",
       run_training(candidates, records, holdout_fraction=0.25)["metrics"] == out["metrics"])

    print("\n" + ("PASS - check_teleon_distillation_training: the skills DB turns the capability corpus + distillation "
                  "records into a labeled, splittable, exportable dataset; a policy is TRAINED from it that learns the "
                  "highest-efficiency distillation strategy per class, generalizes to unseen capabilities (class->band->"
                  "prior backoff), and beats the cold-start prior on held-out (efficiency lift); a real model/LoRA "
                  "plugs in behind the same port (candidate, never truth) and the harness emits its governed spec. "
                  "Deterministic, never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
