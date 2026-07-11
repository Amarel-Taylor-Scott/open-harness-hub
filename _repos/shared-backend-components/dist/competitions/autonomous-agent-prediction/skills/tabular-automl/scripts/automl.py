#!/usr/bin/env python3
"""tabular-automl — a robust, generic, MULTI-PATH self-tuning binary-classification pipeline for the Kaggle
Autonomous Agent Prediction competition. It runs INSIDE the sandbox (debited against time, NOT LLM tokens),
so the agent gets a strong AUC baseline for ~zero token spend and only uses the model to orchestrate + select.

Multi-path self-tuning (the graph made concrete): it trains SEVERAL model families, scores each by
stratified-k-fold out-of-fold AUC (the fair comparator), and BLENDS the top performers by rank-averaging their
probabilities — a portfolio of paths raced on the same data, the champion(s) compiled into the submission.
Everything is sklearn/pandas/numpy only (the standard Kaggle CPU environment), robust to messy columns, and
falls back gracefully so it always emits a valid submission.

    python automl.py --train train.csv --test test.csv --sample sample_submission.csv --out submission.csv
    python automl.py            # auto-discovers train.csv/test.csv/sample_submission.csv in the cwd/./input
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.ensemble import (  # noqa: E402
    ExtraTreesClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier, RandomForestClassifier,
)
from sklearn.impute import SimpleImputer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

_RANDOM_STATE = 42
_MAX_OHE_CARDINALITY = 20  # one-hot only low-cardinality categoricals; the rest get frequency/ordinal encoding


def _find(name_options: list[str]) -> Path | None:
    for base in (Path("."), Path("input"), Path("/kaggle/input"), Path("data")):
        for opt in name_options:
            for p in list(base.glob(opt)) + list(base.rglob(opt)):
                if p.is_file():
                    return p
    return None


def _discover() -> dict[str, Path | None]:
    return {"train": _find(["train.csv", "*train*.csv"]),
            "test": _find(["test.csv", "*test*.csv"]),
            "sample": _find(["sample_submission.csv", "*sample*sub*.csv", "*submission*.csv"])}


def _detect_columns(train: pd.DataFrame, test: pd.DataFrame, sample: pd.DataFrame) -> tuple[str, str]:
    """Return (id_col, target_col). The id col is sample_submission's first column; the target is
    sample_submission's OTHER column (or the train column absent from test)."""
    id_col = sample.columns[0]
    target_col = None
    # the prediction column named in the sample submission
    for c in sample.columns[1:]:
        if c in train.columns:
            target_col = c
            break
    if target_col is None:
        # the column in train but not test (excluding the id), preferring a binary one
        candidates = [c for c in train.columns if c not in test.columns and c != id_col]
        binlike = [c for c in candidates if train[c].nunique(dropna=True) <= 2]
        target_col = (binlike or candidates or [sample.columns[-1]])[0]
    return id_col, target_col


def _build_features(train: pd.DataFrame, test: pd.DataFrame, id_col: str, target_col: str):
    """Numeric passthrough + NaN impute; categoricals -> one-hot (low card) or frequency encoding (high card).
    Returns aligned (X_train, X_test, y). Deterministic; no leakage (encodings fit on train)."""
    drop = {id_col, target_col}
    feats = [c for c in train.columns if c not in drop]
    tr = train[feats].copy()
    te = test[[c for c in feats if c in test.columns]].copy()
    for c in feats:
        if c not in te.columns:
            te[c] = np.nan
    te = te[feats]

    num_cols = [c for c in feats if pd.api.types.is_numeric_dtype(tr[c])]
    cat_cols = [c for c in feats if c not in num_cols]

    frames_tr, frames_te = [], []
    if num_cols:
        imp = SimpleImputer(strategy="median")
        frames_tr.append(pd.DataFrame(imp.fit_transform(tr[num_cols]), columns=num_cols, index=tr.index))
        frames_te.append(pd.DataFrame(imp.transform(te[num_cols]), columns=num_cols, index=te.index))
    for c in cat_cols:
        tr[c] = tr[c].astype("string").fillna("__nan__")
        te[c] = te[c].astype("string").fillna("__nan__")
        card = tr[c].nunique()
        if card <= _MAX_OHE_CARDINALITY:
            cats = sorted(tr[c].unique().tolist())
            for v in cats:
                frames_tr.append(pd.DataFrame({f"{c}__{v}": (tr[c] == v).astype(float).values}, index=tr.index))
                frames_te.append(pd.DataFrame({f"{c}__{v}": (te[c] == v).astype(float).values}, index=te.index))
        else:  # frequency encoding for high-cardinality categoricals
            freq = tr[c].value_counts(normalize=True)
            frames_tr.append(pd.DataFrame({f"{c}__freq": tr[c].map(freq).fillna(0.0).values}, index=tr.index))
            frames_te.append(pd.DataFrame({f"{c}__freq": te[c].map(freq).fillna(0.0).values}, index=te.index))
    X_train = pd.concat(frames_tr, axis=1) if frames_tr else pd.DataFrame(index=tr.index)
    X_test = pd.concat(frames_te, axis=1) if frames_te else pd.DataFrame(index=te.index)
    X_test = X_test.reindex(columns=X_train.columns, fill_value=0.0)

    y_raw = train[target_col]
    if y_raw.dtype == object or str(y_raw.dtype) == "string":
        # map the two classes to 0/1 (the lexicographically-larger label = positive, deterministic)
        classes = sorted(y_raw.dropna().unique().tolist())
        mapping = {classes[0]: 0, classes[-1]: 1}
        y = y_raw.map(mapping).fillna(0).astype(int).values
    else:
        y = (pd.to_numeric(y_raw, errors="coerce").fillna(0) > 0).astype(int).values \
            if y_raw.nunique() > 2 else pd.to_numeric(y_raw, errors="coerce").fillna(0).astype(int).values
    return X_train.values.astype(np.float32), X_test.values.astype(np.float32), y


def _model_zoo() -> dict:
    """The PATH PORTFOLIO — a small set of complementary model families raced on the same folds."""
    return {
        "hist_gbm": HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06, max_depth=None,
                                                   l2_regularization=1.0, random_state=_RANDOM_STATE),
        "gbm": GradientBoostingClassifier(n_estimators=250, learning_rate=0.05, max_depth=3,
                                          subsample=0.9, random_state=_RANDOM_STATE),
        "rf": RandomForestClassifier(n_estimators=400, max_depth=None, min_samples_leaf=2, n_jobs=-1,
                                     random_state=_RANDOM_STATE),
        "extra_trees": ExtraTreesClassifier(n_estimators=500, min_samples_leaf=2, n_jobs=-1,
                                            random_state=_RANDOM_STATE),
        "logreg": Pipeline([("scale", StandardScaler()),
                            ("clf", LogisticRegression(max_iter=2000, C=0.5))]),
    }


def _cv_score(model, X, y, folds: int):
    """Out-of-fold AUC + the OOF probability vector (fair comparator across the zoo)."""
    oof = np.zeros(len(y))
    skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=_RANDOM_STATE)
    for tr_idx, va_idx in skf.split(X, y):
        m = _clone(model)
        m.fit(X[tr_idx], y[tr_idx])
        oof[va_idx] = _proba(m, X[va_idx])
    return roc_auc_score(y, oof), oof


def _clone(model):
    from sklearn.base import clone
    return clone(model)


def _proba(model, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    d = model.decision_function(X)
    return (d - d.min()) / (d.max() - d.min() + 1e-9)


def _rank_avg(prob_list: list[np.ndarray]) -> np.ndarray:
    """Rank-average probabilities — robust to models on different probability scales (a strong simple blend)."""
    ranks = [pd.Series(p).rank(pct=True).values for p in prob_list]
    return np.mean(ranks, axis=0)


def run(train_p: Path, test_p: Path, sample_p: Path, out_p: Path, folds: int = 5) -> dict:
    train = pd.read_csv(train_p)
    test = pd.read_csv(test_p)
    sample = pd.read_csv(sample_p)
    id_col, target_col = _detect_columns(train, test, sample)
    X, Xt, y = _build_features(train, test, id_col, target_col)

    n_pos = int(y.sum())
    folds = max(2, min(folds, n_pos, len(y) - n_pos)) if 0 < n_pos < len(y) else 2
    results = {}
    test_probs = {}
    for name, model in _model_zoo().items():
        try:
            auc, _oof = _cv_score(model, X, y, folds)
            full = _clone(model)
            full.fit(X, y)
            test_probs[name] = _proba(full, Xt)
            results[name] = round(float(auc), 5)
        except Exception as exc:  # noqa: BLE001 — a failing path is dropped, never crashes the submission
            results[name] = f"failed: {str(exc)[:60]}"

    ranked = sorted(((v, k) for k, v in results.items() if isinstance(v, float)), reverse=True)
    if not ranked:  # ultimate fallback: predict the class prior
        pred = np.full(len(Xt), y.mean())
        chosen = ["prior_fallback"]
    else:
        top = [k for _v, k in ranked[:3]]  # blend the top-3 paths by rank-average (robust)
        pred = _rank_avg([test_probs[k] for k in top])
        chosen = top

    sub = sample.copy()
    pred_col = sub.columns[-1] if len(sub.columns) > 1 else target_col
    # align predictions to the sample submission's id order
    if id_col in test.columns and id_col in sub.columns:
        pred_by_id = dict(zip(test[id_col].values, pred))
        sub[pred_col] = sub[id_col].map(pred_by_id).fillna(float(np.mean(pred))).values
    else:
        sub[pred_col] = pred[:len(sub)] if len(pred) >= len(sub) else np.pad(pred, (0, len(sub) - len(pred)),
                                                                             constant_values=float(np.mean(pred)))
    sub.to_csv(out_p, index=False)
    return {"id_col": id_col, "target_col": target_col, "n_train": len(train), "n_test": len(test),
            "n_features": X.shape[1], "folds": folds, "cv_auc_by_model": results,
            "blended_paths": chosen, "submission": str(out_p), "rows": len(sub)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--train"); ap.add_argument("--test"); ap.add_argument("--sample")
    ap.add_argument("--out", default="submission.csv"); ap.add_argument("--folds", type=int, default=5)
    args = ap.parse_args(argv)
    d = _discover()
    train_p = Path(args.train) if args.train else d["train"]
    test_p = Path(args.test) if args.test else d["test"]
    sample_p = Path(args.sample) if args.sample else d["sample"]
    if not (train_p and test_p and sample_p):
        print(json.dumps({"error": "could not locate train/test/sample_submission", "discovered":
                          {k: str(v) for k, v in d.items()}}))
        return 2
    report = run(train_p, test_p, sample_p, Path(args.out), folds=args.folds)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
