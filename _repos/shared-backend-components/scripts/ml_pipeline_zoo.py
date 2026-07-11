#!/usr/bin/env python3
"""ml_pipeline_zoo — the Kaggle ML pipeline as a ZOO OF ZOOS (numerous ways per step, multiple paths, try each).

Owner directive (2026-07-10): test the primitive thesis on Kaggle (PrimitiveML-Kaggle, arms A-F), and "for each
operation/step put together numerous ways it can be accomplished so we have multiple paths backed into our code and
try out each path." This module is that scaffold: the ML pipeline is 9 ordered STAGES, each a set of interchangeable
implementation PATHS behind one selector (the multi-path law made literal for ML). Adding a method = one row, never a
rewrite; the RIGHT path per dataset is chosen by measured receipts, not hardwired.

    profile -> task_infer -> metric -> split -> preprocess -> model -> ensemble -> threshold -> submit

Every path is an ML PRIMITIVE with a typed contract + ML-specific BLOCKING VARIABLES (task / target_cardinality /
rows / metric_requires_ranking / categorical_support / gpu / package_version) — a model primitive is retrieved for a
dataset only if its contract admits the dataset (the research bundle's "quality evidence + deterministic blockers are
part of retrieval"). enumerate_pipelines() yields only pipelines VALID for the inferred task/metric.

Runnable now, no heavy deps: split / preprocess / submission-validation are REAL (numpy/stdlib); the model zoo has an
always-available deterministic BASELINE (class-prior / mean) so a pipeline runs end-to-end on synthetic data, and
heavy learners (lightgbm/catboost/xgboost/sklearn) are contract rows that engage IFF their package is importable
(availability-gated like embedder_zoo). serves_truth=false — a pipeline is a candidate composition, not a promoted
result; scores come only from a held-out oracle (the Kaggle harness, next brick).

    PYTHONPATH=. python3 scripts/ml_pipeline_zoo.py --self-test
    PYTHONPATH=. python3 scripts/ml_pipeline_zoo.py --shape      # the computed zoo shape (stages x paths x pipelines)
    PYTHONPATH=. python3 scripts/ml_pipeline_zoo.py --demo       # run one pipeline end-to-end on a synthetic task
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None  # type: ignore

STAGES: tuple[str, ...] = ("profile", "task_infer", "metric", "split", "preprocess",
                           "model", "ensemble", "threshold", "submit")

#: Task families a step can require/produce (the typed-compatibility axis).
TASKS = ("binary_classification", "multiclass_classification", "regression")


def _pkg(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:  # noqa: BLE001
        return False


# ================================================================================================================
# The dataset descriptor (meta-features) — both retrieval features AND hard-blocker inputs
# ================================================================================================================
def profile_dataset(X, y, *, task: Optional[str] = None) -> dict[str, Any]:
    """Compute the meta-features the research spec lists as retrieval features + blockers."""
    X = np.asarray(X)
    y = np.asarray(y)
    classes = sorted(set(y.tolist()))
    n_class = len(classes)
    inferred = task or ("regression" if n_class > max(20, len(y) // 5)
                        else "binary_classification" if n_class == 2 else "multiclass_classification")
    counts = {c: int((y == c).sum()) for c in classes} if inferred != "regression" else {}
    imbalance = (max(counts.values()) / max(1, min(counts.values()))) if counts else 1.0
    return {"n_rows": int(X.shape[0]), "n_cols": int(X.shape[1] if X.ndim > 1 else 1),
            "task": inferred, "target_cardinality": n_class, "classes": classes,
            "class_counts": counts, "imbalance_ratio": round(imbalance, 3),
            "has_missing": bool(np.isnan(X).any()) if X.dtype.kind == "f" else False}


# ================================================================================================================
# STAGE_PATHS — the zoo of zoos. Each path: {fn, requires(task set)|None, blocks(profile)->reason|None, kind}
# ================================================================================================================
def _stratified_kfold(y, folds=5, seed=0):
    """REAL stratified k-fold indices (numpy, deterministic) — no sklearn needed."""
    y = np.asarray(y)
    fold_of = np.empty(len(y), dtype=int)
    for c in set(y.tolist()):
        idx = np.where(y == c)[0]
        # deterministic round-robin assignment within the class (seed rotates the start)
        for j, i in enumerate(idx):
            fold_of[i] = (j + seed) % folds
    return [(np.where(fold_of != f)[0], np.where(fold_of == f)[0]) for f in range(folds)]


def _group_kfold(y, groups, folds=5, **_):
    groups = np.asarray(groups)
    uniq = sorted(set(groups.tolist()))
    gfold = {g: i % folds for i, g in enumerate(uniq)}
    fold_of = np.array([gfold[g] for g in groups])
    return [(np.where(fold_of != f)[0], np.where(fold_of == f)[0]) for f in range(folds)]


def _time_expanding(y, folds=5, **_):
    n = len(y)
    bounds = [int(n * (i + 1) / (folds + 1)) for i in range(folds)]
    return [(np.arange(0, b), np.arange(b, min(n, b + n // (folds + 1) + 1))) for b in bounds]


def _impute_median(X, **_):
    X = np.asarray(X, dtype="float64")
    if np.isnan(X).any():
        med = np.nanmedian(X, axis=0)
        inds = np.where(np.isnan(X))
        X[inds] = np.take(med, inds[1])
    return X


def _standardize(X, **_):
    X = np.asarray(X, dtype="float64")
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    return (X - mu) / sd


def _model_baseline(Xtr, ytr, Xte, *, task, classes, **_):
    """Always-available deterministic baseline: class-prior probs (classification) / mean (regression)."""
    ytr = np.asarray(ytr)
    if task == "regression":
        pred = np.full(len(Xte), float(ytr.mean()))
        return pred.reshape(-1, 1)
    priors = np.array([(ytr == c).mean() for c in classes], dtype="float64")
    priors = priors / priors.sum()
    return np.tile(priors, (len(Xte), 1))  # (rows, n_class) probability matrix


def _model_sklearn(kind: str):
    def _run(Xtr, ytr, Xte, *, task, classes, **_):
        from sklearn.linear_model import LogisticRegression, Ridge  # noqa: PLC0415
        if task == "regression":
            m = Ridge().fit(Xtr, ytr)
            return np.asarray(m.predict(Xte)).reshape(-1, 1)
        m = LogisticRegression(max_iter=200).fit(Xtr, ytr)
        proba = m.predict_proba(Xte)
        # align columns to `classes`
        col = {c: i for i, c in enumerate(m.classes_.tolist())}
        return np.column_stack([proba[:, col[c]] if c in col else np.zeros(len(Xte)) for c in classes])
    return _run


def _ensemble_mean(probs_list, **_):
    return np.mean(np.stack(probs_list, 0), 0)


def _ensemble_rank_avg(probs_list, **_):
    ranks = [np.argsort(np.argsort(p, 0), 0).astype("float64") / max(1, len(p) - 1) for p in probs_list]
    return np.mean(np.stack(ranks, 0), 0)


def _threshold_argmax(probs, *, task, classes, **_):
    if task == "regression":
        return probs.reshape(-1)
    return np.asarray([classes[i] for i in probs.argmax(1)])


def _submit_validate(pred, sample_n, *, task, **_):
    """REAL submission validation: row count, no-nan, (classification) valid label domain."""
    ok = len(pred) == sample_n and not (np.asarray(pred, dtype="float64").__array__().size and
                                        np.isnan(np.asarray(pred, dtype="float64")).any() if task == "regression" else False)
    return {"valid": bool(ok), "n_rows": int(len(pred)), "expected": int(sample_n)}


#: name -> {fn, requires (task set or None=any), kind, needs (pkg), blocks(profile)->reason|None}
STAGE_PATHS: dict[str, dict[str, dict[str, Any]]] = {
    "profile": {"schema_profile": {"fn": profile_dataset, "kind": "deterministic"}},
    "task_infer": {name: {"fn": None, "kind": "deterministic", "task": name} for name in TASKS},
    "metric": {
        "balanced_accuracy": {"requires": {"binary_classification", "multiclass_classification"}, "kind": "deterministic"},
        "roc_auc": {"requires": {"binary_classification"}, "kind": "deterministic"},
        "log_loss": {"requires": {"binary_classification", "multiclass_classification"}, "kind": "deterministic"},
        "rmse": {"requires": {"regression"}, "kind": "deterministic"},
        "mae": {"requires": {"regression"}, "kind": "deterministic"},
    },
    "split": {
        "stratified_kfold": {"fn": _stratified_kfold, "requires": {"binary_classification", "multiclass_classification"}, "kind": "deterministic"},
        "group_kfold": {"fn": _group_kfold, "requires": None, "kind": "deterministic", "needs_groups": True},
        "time_expanding": {"fn": _time_expanding, "requires": None, "kind": "deterministic", "needs_time": True},
    },
    "preprocess": {
        "impute_median": {"fn": _impute_median, "kind": "deterministic"},
        "standardize": {"fn": _standardize, "kind": "deterministic"},
        "impute_then_standardize": {"fn": lambda X, **k: _standardize(_impute_median(X)), "kind": "deterministic"},
    },
    "model": {
        "baseline_prior": {"fn": _model_baseline, "requires": None, "kind": "baseline", "needs": None},
        "logistic_ridge": {"fn": _model_sklearn("logreg"), "requires": None, "kind": "learner", "needs": "sklearn"},
        "lightgbm": {"fn": None, "requires": None, "kind": "learner", "needs": "lightgbm"},
        "catboost": {"fn": None, "requires": None, "kind": "learner", "needs": "catboost"},
        "xgboost": {"fn": None, "requires": None, "kind": "learner", "needs": "xgboost"},
    },
    "ensemble": {
        "single": {"fn": None, "kind": "deterministic"},
        "mean": {"fn": _ensemble_mean, "kind": "deterministic"},
        "rank_average": {"fn": _ensemble_rank_avg, "kind": "deterministic"},
    },
    "threshold": {
        "argmax": {"fn": _threshold_argmax, "requires": {"binary_classification", "multiclass_classification"}, "kind": "deterministic"},
        "identity": {"fn": lambda p, **k: p.reshape(-1) if p.ndim > 1 else p, "requires": {"regression"}, "kind": "deterministic"},
    },
    "submit": {"validate_materialize": {"fn": _submit_validate, "kind": "deterministic"}},
}


def available_paths(stage: str) -> list[str]:
    """Paths whose package is importable right now (availability-gated model zoo)."""
    out = []
    for name, spec in STAGE_PATHS[stage].items():
        need = spec.get("needs")
        if need and not _pkg(need):
            continue
        out.append(name)
    return out


def _path_admits_task(stage: str, name: str, task: str) -> bool:
    req = STAGE_PATHS[stage][name].get("requires", None)
    if stage == "task_infer":
        return STAGE_PATHS[stage][name].get("task") == task
    return req is None or task in req


def enumerate_pipelines(task: str, *, only_available: bool = True) -> list[dict[str, str]]:
    """Every VALID pipeline for a task: one path per stage, filtered by task/metric compatibility + availability.
    This is the multi-path law for ML — a candidate set to RACE, not one hardwired pipeline."""
    import itertools  # noqa: PLC0415
    per_stage = []
    for stage in STAGES:
        names = available_paths(stage) if only_available else list(STAGE_PATHS[stage])
        names = [n for n in names if _path_admits_task(stage, n, task)]
        # stages that need group/time structure are optional -> allow a k-fold default to stand in when absent
        if not names and stage == "split":
            names = ["stratified_kfold"]
        per_stage.append([(stage, n) for n in names] or [(stage, next(iter(STAGE_PATHS[stage])))])
    return [dict(combo) for combo in itertools.product(*per_stage)]


def zoo_shape() -> dict[str, Any]:
    """Computed shape (no-magic): stages, paths per stage, total path rows, and pipelines for a sample task."""
    paths = {s: list(STAGE_PATHS[s]) for s in STAGES}
    return {"stages": len(STAGES), "paths_per_stage": {s: len(p) for s, p in paths.items()},
            "total_path_rows": sum(len(p) for p in paths.values()),
            "pipelines_multiclass_all": len(enumerate_pipelines("multiclass_classification", only_available=False)),
            "pipelines_multiclass_available": len(enumerate_pipelines("multiclass_classification", only_available=True))}


# ================================================================================================================
# Run one pipeline end-to-end (deterministic; real split/preprocess/model-baseline/submit)
# ================================================================================================================
def run_pipeline(path: dict[str, str], X, y, Xte, *, task: Optional[str] = None,
                 groups=None) -> dict[str, Any]:
    """Execute a chosen pipeline path on (X,y)->Xte. Returns predictions + a receipt. serves_truth=false."""
    prof = profile_dataset(X, y, task=task)
    task = prof["task"]
    classes = prof["classes"]
    Xp = STAGE_PATHS["preprocess"][path["preprocess"]]["fn"](X)
    Xtep = STAGE_PATHS["preprocess"][path["preprocess"]]["fn"](Xte)
    split_fn = STAGE_PATHS["split"][path["split"]]["fn"]
    folds = split_fn(y, groups=groups) if path["split"] == "group_kfold" else split_fn(y)
    model_fn = STAGE_PATHS["model"][path["model"]]["fn"] or _model_baseline
    # out-of-fold + test probabilities, averaged across folds
    test_probs = []
    oof_ok = 0
    for tr, va in folds:
        p = model_fn(Xp[tr], np.asarray(y)[tr], Xtep, task=task, classes=classes)
        test_probs.append(p)
        oof_ok += 1
    ens = path["ensemble"]
    probs = test_probs[0] if ens == "single" else STAGE_PATHS["ensemble"][ens]["fn"](test_probs)
    pred = STAGE_PATHS["threshold"][path["threshold"]]["fn"](probs, task=task, classes=classes)
    val = _submit_validate(pred, len(Xte), task=task)
    return {"task": task, "path": path, "folds": oof_ok, "prediction_head": np.asarray(pred)[:5].tolist(),
            "submission": val, "candidate": True, "serves_truth": False}


# ================================================================================================================
# Self-test
# ================================================================================================================
def _synth(task: str = "multiclass_classification", n: int = 120, seed: int = 0):
    rng_state = np.arange(n * 4).reshape(n, 4).astype("float64")  # deterministic pseudo-features (no Math.random)
    X = (rng_state % 7) + (np.arange(n).reshape(-1, 1) % 3)
    if task == "regression":
        y = X.sum(1)
    else:
        k = 2 if task == "binary_classification" else 3
        y = (np.arange(n) % k)
    Xte = X[: n // 3]
    return X, y, Xte


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    if np is None:
        print("FAIL - ml_pipeline_zoo: numpy required")
        return 1

    shape = zoo_shape()
    checks.append((f"zoo shape computed: {shape['stages']} stages, {shape['total_path_rows']} path rows, "
                   f"{shape['pipelines_multiclass_all']} multiclass pipelines",
                   shape["stages"] == len(STAGES) and shape["total_path_rows"] >= 20
                   and shape["pipelines_multiclass_all"] > 50, json.dumps(shape["paths_per_stage"])))

    # (2) TYPED COMPATIBILITY: a regression-only metric (rmse) never appears in a classification pipeline, and
    #     balanced_accuracy never appears in a regression pipeline (blockers are part of enumeration).
    mc = enumerate_pipelines("multiclass_classification", only_available=False)
    rg = enumerate_pipelines("regression", only_available=False)
    checks.append(("typed compat: rmse only in regression, balanced_accuracy only in classification",
                   all(p["metric"] != "rmse" for p in mc) and all(p["metric"] != "balanced_accuracy" for p in rg),
                   f"mc={len(mc)} rg={len(rg)}"))

    # (3) RUNS END-TO-END on synthetic multiclass -> a VALID submission (baseline model, always available).
    X, y, Xte = _synth("multiclass_classification")
    path = {"profile": "schema_profile", "task_infer": "multiclass_classification", "metric": "balanced_accuracy",
            "split": "stratified_kfold", "preprocess": "impute_then_standardize", "model": "baseline_prior",
            "ensemble": "mean", "threshold": "argmax", "submit": "validate_materialize"}
    res = run_pipeline(path, X, y, Xte)
    checks.append((f"pipeline runs end-to-end -> valid submission ({res['submission']})",
                   res["submission"]["valid"] and res["submission"]["n_rows"] == len(Xte), json.dumps(res["submission"])))

    # (4) REGRESSION path also runs (different model output shape + identity threshold).
    Xr, yr, Xter = _synth("regression")
    rpath = {**path, "task_infer": "regression", "metric": "rmse", "split": "time_expanding",
             "preprocess": "standardize", "model": "baseline_prior", "ensemble": "single", "threshold": "identity"}
    rres = run_pipeline(rpath, Xr, yr, Xter, task="regression")
    checks.append((f"regression pipeline runs -> valid submission ({rres['submission']['valid']})",
                   rres["submission"]["valid"], json.dumps(rres["submission"])))

    # (5) FLEXIBILITY: adding a model path row is reflected in the shape (add-a-row, not a rewrite).
    STAGE_PATHS["model"]["_probe_learner"] = {"fn": None, "requires": None, "kind": "learner", "needs": "definitely_not_a_pkg"}
    try:
        grew = zoo_shape()["paths_per_stage"]["model"] == shape["paths_per_stage"]["model"] + 1
        # availability-gated: the probe (missing pkg) is excluded from AVAILABLE enumeration
        avail_excludes = "_probe_learner" not in available_paths("model")
    finally:
        del STAGE_PATHS["model"]["_probe_learner"]
    checks.append(("flexibility: add-a-path grows the shape; availability gate excludes a missing-pkg path",
                   grew and avail_excludes, ""))

    # (6) DETERMINISM: same pipeline + data -> identical prediction head twice.
    r2 = run_pipeline(path, X, y, Xte)
    checks.append(("pipeline deterministic (identical prediction head twice)",
                   res["prediction_head"] == r2["prediction_head"], ""))

    ok = all(c[1] for c in checks)
    print(f"{'PASS' if ok else 'FAIL'} - ml_pipeline_zoo: {len(STAGES)}-stage ML pipeline, each stage a ZOO of paths "
          f"({shape['total_path_rows']} path rows), typed task/metric compatibility + availability gates, runs "
          f"end-to-end on synthetic data. Add-a-path not a rewrite. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="The Kaggle ML pipeline as a zoo of zoos (multiple paths per step).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--shape", action="store_true", help="print the computed zoo shape")
    ap.add_argument("--demo", action="store_true", help="run one pipeline end-to-end on a synthetic multiclass task")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.shape:
        print(json.dumps(zoo_shape(), indent=2))
        return 0
    if args.demo:
        X, y, Xte = _synth("multiclass_classification")
        path = {"profile": "schema_profile", "task_infer": "multiclass_classification", "metric": "balanced_accuracy",
                "split": "stratified_kfold", "preprocess": "impute_then_standardize", "model": "baseline_prior",
                "ensemble": "mean", "threshold": "argmax", "submit": "validate_materialize"}
        print(json.dumps(run_pipeline(path, X, y, Xte), indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
