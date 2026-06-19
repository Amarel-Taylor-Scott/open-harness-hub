"""src.teleon.training.policy — the DISTILLATION POLICY: learn the most efficient non-deterministic -> deterministic
path for a capability, and the harness that trains + evaluates it.

A policy predicts, for a capability's features, the distillation STRATEGY to use (and the expected coverage/cost).
Three implementations behind ONE port:
  * PriorPolicy — the cold-start baseline (strategy from the determinism band). No training.
  * FittedPolicy — TRAINED from the skills-DB dataset: per capability class it learns the strategy with the
    highest observed efficiency, backing off (class -> band -> prior) for unseen inputs so it GENERALIZES. This is
    the deterministic, evaluatable 'trained model' — fit from data, scored on held-out.
  * TrainedArtifactPolicy — the SEAM for a real trained model / LoRA: it wraps a trained-artifact handle (produced
    by an external, sandboxed training backend — a candidate capability, never auto-active). Without an artifact it
    is unusable (requires_trained_artifact), so a model/LoRA can plug in here without changing any caller.

run_training() is the harness: build dataset -> split -> train FittedPolicy -> evaluate held-out vs the prior ->
emit a model/LoRA artifact SPEC. The held-out lift is the proof the system learns more efficient paths; doing it
cheaper/faster than anyone is the moat. Pure + deterministic; Teleon-layer — never imports src.baltor; never truth.
"""
from __future__ import annotations

from src.teleon.evolution.distiller import choose_strategy

#: a class needs at least this many labeled examples before the fitted policy trusts it over the band backoff.
_MIN_CLASS_OBS = 2


def _class_of(features: dict) -> str:
    return f"{features.get('category', 'other')}|{features.get('determinism_band', 'template')}"


def _prior_strategy(features: dict) -> str:
    return choose_strategy(features.get("determinism_ceiling", 0.0))


class PriorPolicy:
    """Cold-start baseline: the strategy implied by the determinism band, no learning."""

    source = "prior"

    def predict(self, features: dict) -> dict:
        return {"strategy": _prior_strategy(features), "source": "prior", "confidence": 0.0}


class FittedPolicy:
    """Trained from a dataset: per class, the highest-mean-efficiency strategy; backs off class -> band -> prior."""

    source = "fitted"

    def __init__(self, by_class_best: dict, by_band_best: dict) -> None:
        self._class = by_class_best  # class_key -> {strategy, mean_efficiency, n}
        self._band = by_band_best    # band -> {strategy, mean_efficiency, n}

    def predict(self, features: dict) -> dict:
        ck = _class_of(features)
        if ck in self._class:
            best = self._class[ck]
            return {"strategy": best["strategy"], "source": "fitted_class", "confidence": min(1.0, best["n"] / 5.0),
                    "expected_efficiency": best["mean_efficiency"]}
        band = features.get("determinism_band", "template")
        if band in self._band:
            best = self._band[band]
            return {"strategy": best["strategy"], "source": "fitted_band", "confidence": min(0.5, best["n"] / 10.0),
                    "expected_efficiency": best["mean_efficiency"]}
        return {"strategy": _prior_strategy(features), "source": "prior_backoff", "confidence": 0.0}


class TrainedArtifactPolicy:
    """The SEAM for a real trained model / LoRA. ``artifact`` is a handle produced by an external sandboxed
    training backend (a candidate capability). With no artifact loaded it is unusable — so a model/LoRA can be
    dropped in behind this exact port later without touching callers. A prediction is never truth."""

    source = "trained_artifact"

    def __init__(self, artifact=None) -> None:
        self.artifact = artifact

    def available(self) -> bool:
        return self.artifact is not None

    def predict(self, features: dict) -> dict:
        if not self.available():
            return {"strategy": None, "source": "requires_trained_artifact", "confidence": 0.0,
                    "detail": "no trained model/LoRA artifact loaded; train one via the sandboxed backend (candidate)"}
        out = self.artifact.predict(features)  # the real model/LoRA implements predict()
        return {"strategy": out.get("strategy"), "source": "trained_artifact",
                "confidence": float(out.get("confidence", 0.0)), "serves_truth": False}


def _best_by(group: dict) -> dict:
    """For {key: [examples]} pick, per key, the strategy with the highest mean efficiency (ties -> lowest name)."""
    out = {}
    for key, exs in group.items():
        by_strat: dict = {}
        for e in exs:
            by_strat.setdefault(e.label_strategy, []).append(e.efficiency)
        means = {s: sum(v) / len(v) for s, v in by_strat.items()}
        counts = {s: len(v) for s, v in by_strat.items()}
        best = max(means, key=lambda s: (means[s], tuple(-ord(c) for c in s)))
        out[key] = {"strategy": best, "mean_efficiency": round(means[best], 6), "n": counts[best]}
    return out


def train(train_examples: list) -> FittedPolicy:
    """Fit a FittedPolicy from labeled examples: the best (highest-efficiency) strategy per class and per band."""
    by_class: dict = {}
    by_band: dict = {}
    for e in train_examples:
        by_class.setdefault(_class_of(e.features), []).append(e)
        by_band.setdefault(e.features.get("determinism_band", "template"), []).append(e)
    class_best = {k: v for k, v in _best_by(by_class).items() if v["n"] >= _MIN_CLASS_OBS}
    return FittedPolicy(class_best, _best_by(by_band))


def evaluate(policy, holdout: list, *, baseline=None) -> dict:
    """Score a policy on held-out examples: accuracy = fraction whose predicted strategy matches the example's
    actual (observed-best-for-its-class) strategy. Compares against a baseline (default PriorPolicy) to report the
    LIFT — the proof the trained policy finds more efficient paths than the cold-start prior."""
    baseline = baseline if baseline is not None else PriorPolicy()
    if not holdout:
        return {"n": 0, "accuracy": 0.0, "baseline_accuracy": 0.0, "efficiency_lift": 0.0}
    hit = sum(1 for e in holdout if policy.predict(e.features)["strategy"] == e.label_strategy)
    base_hit = sum(1 for e in holdout if baseline.predict(e.features)["strategy"] == e.label_strategy)
    n = len(holdout)
    return {"n": n, "accuracy": round(hit / n, 4), "baseline_accuracy": round(base_hit / n, 4),
            "efficiency_lift": round((hit - base_hit) / n, 4)}


def model_artifact_spec(dataset, fitted: FittedPolicy) -> dict:
    """The descriptor a real training backend consumes to produce a model/LoRA — the 'trained system' as a governed
    CANDIDATE spec (not a binary). Names the feature/label schema, size, a base-model hint, and the learned table."""
    from src.teleon.training.skills_db import FEATURE_KEYS
    return {
        "artifact_kind": "distillation_policy_lora",
        "status": "candidate",  # a real LoRA is trained by a sandboxed backend, then gated — never auto-active
        "feature_schema": list(FEATURE_KEYS),
        "label_schema": ["strategy", "expected_coverage", "expected_efficiency"],
        "training_examples": len(dataset.labeled),
        "classes_learned": len(fitted._class),
        "base_model_hint": "small-instruct or a classifier head; LoRA over a code-capable base",
        "objective": "predict the highest-efficiency distillation strategy (non-deterministic -> most deterministic)",
        "serves_truth": False,
    }


def run_training(candidates: list[dict], records: list[dict], *, holdout_fraction: float = 0.25) -> dict:
    """The training HARNESS: build the skills-DB dataset, split, train the FittedPolicy, evaluate held-out vs the
    prior, and emit the model/LoRA artifact spec. Returns the trained policy + the metrics that show it learns
    cheaper/more-efficient paths."""
    from src.teleon.training.skills_db import build_dataset
    dataset = build_dataset(candidates, records)
    train_ex, holdout = dataset.split(holdout_fraction=holdout_fraction)
    fitted = train(train_ex)
    metrics = evaluate(fitted, holdout)
    return {"dataset": dataset.summary(), "train_n": len(train_ex), "holdout_n": len(holdout),
            "metrics": metrics, "policy": fitted, "artifact_spec": model_artifact_spec(dataset, fitted),
            "serves_truth": False}
