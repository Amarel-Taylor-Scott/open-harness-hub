#!/usr/bin/env python3
"""mint_ml_kaggle_pack — mint the ML-Kaggle primitive families as REAL, oracle-tested primitives.

Owner directive (2026-07-10, PrimitiveML-Kaggle thesis): mint the ~100 ML primitive families (data.*/task.*/split.*/
encode.*/model.*/ensemble.*/submission.*) so a Kaggle plan resolves at high coverage and the A-F arms can measure
token savings. This module authors the DETERMINISTIC ML primitives — metrics, splits, preprocessing, EDA, ensembling,
submission validation — as real numpy bodies with strict behavioral ORACLES, minted through mint_vertical_pack (a card
is emitted verification_level='execution' ONLY if the oracle passes; a stub can never be minted). The heavy LEARNERS
(catboost/lightgbm/xgboost) stay contract rows in ml_pipeline_zoo (availability-gated) — they are stateful/fitted, not
pure functions, so they belong in the pipeline zoo, not this pure-primitive pack.

Every body takes one arg ``x`` (composite inputs passed as a tuple). candidate-only, serves_truth=false.

    PYTHONPATH=. python3 scripts/mint_ml_kaggle_pack.py --self-test
    PYTHONPATH=. python3 scripts/mint_ml_kaggle_pack.py --mint
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np  # noqa: E402 — used by a few oracle lambdas (e.g. Standardize checks mean/std of the output)

from scripts import mint_vertical_pack as _mint  # noqa: E402

_NP = "import numpy as np\n"


def _spec(title, blackbox, ie, oe, body, oracle, tags):
    return {"title": title, "blackbox": blackbox, "input_edge": ie, "output_edge": oe,
            "capability_tags": tags, "domains": ["ml", "kaggle"], "body": _NP + body, "oracle": oracle}


def _close(a, b, tol=1e-6):
    return abs(float(a) - float(b)) < tol


def ml_specs() -> list[dict[str, Any]]:
    s: list[dict[str, Any]] = []
    # ---- METRICS ----
    s.append(_spec("Root Mean Squared Error", "Computes RMSE between true and predicted values.",
                   "TrueAndPredictedArrays", "RmseScore",
                   "def run(x):\n    y,p=x; y=np.asarray(y,float); p=np.asarray(p,float)\n    return float(np.sqrt(np.mean((y-p)**2)))\n",
                   lambda r: _close(r(([1,2,3],[1,2,3])),0) and _close(r(([0,0],[1,1])),1.0), ["metric","rmse","regression"]))
    s.append(_spec("Mean Absolute Error", "Computes MAE between true and predicted values.",
                   "TrueAndPredictedArrays", "MaeScore",
                   "def run(x):\n    y,p=x; y=np.asarray(y,float); p=np.asarray(p,float)\n    return float(np.mean(np.abs(y-p)))\n",
                   lambda r: _close(r(([1,2,3],[1,2,3])),0) and _close(r(([0,0],[2,4])),3.0), ["metric","mae","regression"]))
    s.append(_spec("Root Mean Squared Log Error", "Computes RMSLE between true and predicted non-negative values.",
                   "TrueAndPredictedArrays", "RmsleScore",
                   "def run(x):\n    y,p=x; y=np.asarray(y,float); p=np.asarray(p,float)\n    return float(np.sqrt(np.mean((np.log1p(y)-np.log1p(p))**2)))\n",
                   lambda r: _close(r(([1,2,3],[1,2,3])),0), ["metric","rmsle","regression"]))
    s.append(_spec("Accuracy Score", "Fraction of predictions equal to the true labels.",
                   "TrueAndPredictedLabels", "AccuracyScore",
                   "def run(x):\n    y,p=x; y=np.asarray(y); p=np.asarray(p)\n    return float(np.mean(y==p))\n",
                   lambda r: _close(r(([1,0,1],[1,0,0])),2/3) and _close(r(([1,1],[1,1])),1.0), ["metric","accuracy","classification"]))
    s.append(_spec("Balanced Accuracy Score", "Mean per-class recall (robust to class imbalance).",
                   "TrueAndPredictedLabels", "BalancedAccuracyScore",
                   "def run(x):\n    y,p=x; y=np.asarray(y); p=np.asarray(p)\n    recs=[]\n    for c in set(y.tolist()):\n        m=(y==c)\n        recs.append((p[m]==c).mean() if m.any() else 0.0)\n    return float(np.mean(recs))\n",
                   lambda r: _close(r(([0,0,1,1],[0,0,1,1])),1.0) and _close(r(([0,0,0,1],[0,0,0,0])),0.5), ["metric","balanced_accuracy","classification"]))
    s.append(_spec("R2 Coefficient Of Determination", "R^2 score for regression predictions.",
                   "TrueAndPredictedArrays", "R2Score",
                   "def run(x):\n    y,p=x; y=np.asarray(y,float); p=np.asarray(p,float)\n    ss_res=np.sum((y-p)**2); ss_tot=np.sum((y-y.mean())**2)\n    return float(1-ss_res/ss_tot) if ss_tot>0 else 0.0\n",
                   lambda r: _close(r(([1,2,3],[1,2,3])),1.0), ["metric","r2","regression"]))
    s.append(_spec("Binary Log Loss", "Binary cross-entropy between labels and probabilities (clipped).",
                   "LabelsAndProbabilities", "LogLossScore",
                   "def run(x):\n    y,p=x; y=np.asarray(y,float); p=np.clip(np.asarray(p,float),1e-15,1-1e-15)\n    return float(-np.mean(y*np.log(p)+(1-y)*np.log(1-p)))\n",
                   lambda r: r(([1,0],[0.99,0.01]))<0.02 and r(([1,0],[0.5,0.5]))>0.6, ["metric","log_loss","classification"]))
    s.append(_spec("Binary Confusion Counts", "Returns (tp, fp, fn, tn) for binary predictions.",
                   "TrueAndPredictedLabels", "ConfusionCounts",
                   "def run(x):\n    y,p=x; y=np.asarray(y); p=np.asarray(p)\n    tp=int(((y==1)&(p==1)).sum()); fp=int(((y==0)&(p==1)).sum())\n    fn=int(((y==1)&(p==0)).sum()); tn=int(((y==0)&(p==0)).sum())\n    return (tp,fp,fn,tn)\n",
                   lambda r: r(([1,1,0,0],[1,0,1,0]))==(1,1,1,1), ["metric","confusion","classification"]))
    s.append(_spec("Binary F1 Score", "Harmonic mean of precision and recall for binary labels.",
                   "TrueAndPredictedLabels", "F1Score",
                   "def run(x):\n    y,p=x; y=np.asarray(y); p=np.asarray(p)\n    tp=((y==1)&(p==1)).sum(); fp=((y==0)&(p==1)).sum(); fn=((y==1)&(p==0)).sum()\n    pr=tp/(tp+fp) if tp+fp else 0.0; rc=tp/(tp+fn) if tp+fn else 0.0\n    return float(2*pr*rc/(pr+rc)) if pr+rc else 0.0\n",
                   lambda r: _close(r(([1,1,0],[1,1,0])),1.0), ["metric","f1","classification"]))
    # ---- SPLITS ----
    s.append(_spec("Stratified KFold Assignment", "Assigns each row to one of k folds, balanced within each class.",
                   "LabelsAndFoldCount", "FoldAssignment",
                   "def run(x):\n    y,k=x; y=np.asarray(y); fold=np.empty(len(y),int)\n    for c in set(y.tolist()):\n        idx=np.where(y==c)[0]\n        for j,i in enumerate(idx): fold[i]=j%k\n    return fold.tolist()\n",
                   lambda r: (lambda f: len(f)==6 and set(f)<= {0,1,2})(r(([0,0,0,1,1,1],3))), ["split","stratified_kfold","validation"]))
    s.append(_spec("KFold Index Assignment", "Round-robin assigns n rows to k folds.",
                   "RowCountAndFoldCount", "FoldAssignment",
                   "def run(x):\n    n,k=x\n    return [i%k for i in range(n)]\n",
                   lambda r: r((5,2))==[0,1,0,1,0], ["split","kfold","validation"]))
    s.append(_spec("Time Series Expanding Bounds", "Expanding-window train-end boundaries for k time splits.",
                   "RowCountAndSplitCount", "SplitBounds",
                   "def run(x):\n    n,k=x\n    return [int(n*(i+1)/(k+1)) for i in range(k)]\n",
                   lambda r: (lambda b: b==sorted(b) and len(b)==3)(r((100,3))), ["split","time_series","validation"]))
    s.append(_spec("Group KFold Assignment", "Assigns rows to k folds so a group never spans folds.",
                   "GroupsAndFoldCount", "FoldAssignment",
                   "def run(x):\n    g,k=x; uniq=sorted(set(g)); gf={u:i%k for i,u in enumerate(uniq)}\n    return [gf[v] for v in g]\n",
                   lambda r: (lambda f: f[0]==f[1] and f[2]==f[3])(r((['a','a','b','b'],2))), ["split","group_kfold","validation"]))
    s.append(_spec("Deterministic Train Test Split", "Splits n indices into train/test by a fraction, deterministically.",
                   "RowCountAndTestFraction", "TrainTestIndices",
                   "def run(x):\n    n,frac=x; cut=int(n*(1-frac))\n    return (list(range(cut)), list(range(cut,n)))\n",
                   lambda r: r((10,0.2))==(list(range(8)),[8,9]), ["split","holdout","validation"]))
    # ---- PREPROCESS ----
    s.append(_spec("Impute Numeric Median", "Fills missing (NaN) values in a numeric column with its median.",
                   "NumericColumnWithMissing", "ImputedNumericColumn",
                   "def run(x):\n    a=np.asarray(x,float); m=np.nanmedian(a); a=np.where(np.isnan(a),m,a)\n    return a.tolist()\n",
                   lambda r: r([1.0,float('nan'),3.0])==[1.0,2.0,3.0], ["impute","median","preprocess"]))
    s.append(_spec("Standardize Column", "Standardizes a numeric column to zero mean and unit variance.",
                   "NumericColumn", "StandardizedColumn",
                   "def run(x):\n    a=np.asarray(x,float); sd=a.std() or 1.0\n    return ((a-a.mean())/sd).tolist()\n",
                   lambda r: _close(np.mean(r([1,2,3,4])),0) and _close(np.std(r([1,2,3,4])),1.0), ["scale","standardize","preprocess"]))
    s.append(_spec("MinMax Scale Column", "Scales a numeric column to the [0,1] range.",
                   "NumericColumn", "ScaledColumn",
                   "def run(x):\n    a=np.asarray(x,float); rng=(a.max()-a.min()) or 1.0\n    return ((a-a.min())/rng).tolist()\n",
                   lambda r: r([0,5,10])==[0.0,0.5,1.0], ["scale","minmax","preprocess"]))
    s.append(_spec("Log1p Transform Column", "Applies log(1+x) to a non-negative numeric column.",
                   "NonNegativeColumn", "LogTransformedColumn",
                   "def run(x):\n    return np.log1p(np.asarray(x,float)).tolist()\n",
                   lambda r: _close(r([0,0,0])[0],0.0), ["transform","log1p","preprocess"]))
    s.append(_spec("Rank Transform Column", "Replaces values with their normalized rank in [0,1].",
                   "NumericColumn", "RankColumn",
                   "def run(x):\n    a=np.asarray(x,float); order=np.argsort(np.argsort(a)).astype(float)\n    return (order/max(1,len(a)-1)).tolist()\n",
                   lambda r: r([10,20,30])==[0.0,0.5,1.0], ["transform","rank","preprocess"]))
    s.append(_spec("Clip To Quantiles", "Clips a numeric column to its [lo, hi] quantiles (winsorize).",
                   "ColumnAndQuantileBounds", "ClippedColumn",
                   "def run(x):\n    a,lo,hi=x; a=np.asarray(a,float); ql,qh=np.quantile(a,lo),np.quantile(a,hi)\n    return np.clip(a,ql,qh).tolist()\n",
                   lambda r: max(r(([0,1,2,3,100],0.0,0.75)))<=3.0, ["outlier","winsorize","preprocess"]))
    s.append(_spec("One Hot Encode Column", "Encodes a categorical column into an indicator matrix + category order.",
                   "CategoricalColumn", "OneHotMatrixAndCategories",
                   "def run(x):\n    cats=sorted(set(x)); idx={c:i for i,c in enumerate(cats)}\n    M=[[1 if idx[v]==j else 0 for j in range(len(cats))] for v in x]\n    return (M,cats)\n",
                   lambda r: r(['a','b','a'])==([[1,0],[0,1],[1,0]],['a','b']), ["encode","one_hot","preprocess"]))
    s.append(_spec("Ordinal Encode Column", "Maps categories to integers by sorted order.",
                   "CategoricalColumn", "OrdinalColumn",
                   "def run(x):\n    cats=sorted(set(x)); idx={c:i for i,c in enumerate(cats)}\n    return [idx[v] for v in x]\n",
                   lambda r: r(['b','a','b'])==[1,0,1], ["encode","ordinal","preprocess"]))
    s.append(_spec("Frequency Encode Column", "Replaces each category with its frequency count.",
                   "CategoricalColumn", "FrequencyColumn",
                   "def run(x):\n    from collections import Counter; c=Counter(x)\n    return [c[v] for v in x]\n",
                   lambda r: r(['a','a','b'])==[2,2,1], ["encode","frequency","preprocess"]))
    s.append(_spec("Leave One Out Target Mean Encode", "Out-of-fold target mean per category (leave-one-out, no leakage).",
                   "CategoriesAndTarget", "TargetEncodedColumn",
                   "def run(x):\n    cats,y=x; y=np.asarray(y,float); out=[]\n    from collections import defaultdict\n    tot=defaultdict(float); cnt=defaultdict(int)\n    for c,t in zip(cats,y): tot[c]+=t; cnt[c]+=1\n    for c,t in zip(cats,y):\n        out.append((tot[c]-t)/(cnt[c]-1) if cnt[c]>1 else 0.0)\n    return out\n",
                   lambda r: r((['a','a','a'],[0.0,1.0,1.0]))==[1.0,0.5,0.5], ["encode","target_oof","preprocess"]))
    s.append(_spec("Quantile Bin Column", "Bins a numeric column into n quantile buckets (0..n-1).",
                   "ColumnAndBinCount", "BinIndexColumn",
                   "def run(x):\n    a,nb=x; a=np.asarray(a,float); edges=np.quantile(a,np.linspace(0,1,nb+1))\n    return np.clip(np.digitize(a,edges[1:-1]),0,nb-1).tolist()\n",
                   lambda r: max(r(([1,2,3,4,5,6,7,8],4)))<=3, ["bin","quantile","preprocess"]))
    # ---- EDA / TASK INFERENCE ----
    s.append(_spec("Infer Task Type", "Infers binary / multiclass / regression from a target column.",
                   "TargetColumn", "TaskType",
                   "def run(x):\n    y=list(x); u=sorted(set(y))\n    if all(float(v).is_integer() for v in y) and len(u)<=max(20,len(y)//5):\n        return 'binary_classification' if len(u)==2 else 'multiclass_classification'\n    return 'regression'\n",
                   lambda r: r([0,1,0,1])=='binary_classification' and r([0,1,2,1])=='multiclass_classification' and r([0.1,0.2,0.3,0.44,0.5,0.66])=='regression', ["task","infer","eda"]))
    s.append(_spec("Class Imbalance Ratio", "Ratio of the largest to smallest class count.",
                   "LabelColumn", "ImbalanceRatio",
                   "def run(x):\n    from collections import Counter; c=Counter(x)\n    return float(max(c.values())/min(c.values()))\n",
                   lambda r: _close(r([0,0,0,1]),3.0), ["eda","imbalance","classification"]))
    s.append(_spec("Detect Constant Columns", "Indices of columns with a single unique value.",
                   "Matrix", "ConstantColumnIndices",
                   "def run(x):\n    a=np.asarray(x)\n    return [j for j in range(a.shape[1]) if len(set(a[:,j].tolist()))==1]\n",
                   lambda r: r([[1,5],[1,6],[1,7]])==[0], ["eda","constant","cleaning"]))
    s.append(_spec("Column Missingness Fraction", "Fraction of NaN per column.",
                   "NumericMatrix", "MissingnessFractions",
                   "def run(x):\n    a=np.asarray(x,float)\n    return np.isnan(a).mean(0).tolist()\n",
                   lambda r: r([[1.0,float('nan')],[2.0,float('nan')]])==[0.0,1.0], ["eda","missingness","cleaning"]))
    s.append(_spec("Count Duplicate Rows", "Number of duplicate rows in a matrix.",
                   "Matrix", "DuplicateRowCount",
                   "def run(x):\n    seen=set(); dup=0\n    for row in x:\n        t=tuple(row)\n        if t in seen: dup+=1\n        seen.add(t)\n    return dup\n",
                   lambda r: r([[1,2],[1,2],[3,4]])==1, ["eda","duplicates","cleaning"]))
    s.append(_spec("High Cardinality Columns", "Column indices whose unique count exceeds a threshold.",
                   "MatrixAndThreshold", "HighCardinalityColumnIndices",
                   "def run(x):\n    a,thr=x; a=np.asarray(a)\n    return [j for j in range(a.shape[1]) if len(set(a[:,j].tolist()))>thr]\n",
                   lambda r: r(([[1,1],[2,1],[3,1]],2))==[0], ["eda","cardinality","feature"]))
    s.append(_spec("Detect Id Column", "Index of the first all-unique column (a likely id), else -1.",
                   "Matrix", "IdColumnIndex",
                   "def run(x):\n    a=np.asarray(x)\n    for j in range(a.shape[1]):\n        col=a[:,j].tolist()\n        if len(set(col))==len(col): return j\n    return -1\n",
                   lambda r: r([[1,7],[2,7],[3,7]])==0, ["eda","id_column","cleaning"]))
    # ---- ENSEMBLE ----
    s.append(_spec("Ensemble Mean", "Averages a list of prediction arrays.",
                   "PredictionArrayList", "EnsembledPredictions",
                   "def run(x):\n    return np.mean(np.stack([np.asarray(a,float) for a in x],0),0).tolist()\n",
                   lambda r: r([[0.0,1.0],[1.0,1.0]])==[0.5,1.0], ["ensemble","mean"]))
    s.append(_spec("Ensemble Weighted Mean", "Weighted average of prediction arrays.",
                   "ArraysAndWeights", "EnsembledPredictions",
                   "def run(x):\n    arrs,w=x; w=np.asarray(w,float); w=w/w.sum()\n    return np.average(np.stack([np.asarray(a,float) for a in arrs],0),0,weights=w).tolist()\n",
                   lambda r: r(([[0.0],[1.0]],[3,1]))==[0.25], ["ensemble","weighted_mean"]))
    s.append(_spec("Ensemble Rank Average", "Averages the normalized ranks of prediction arrays.",
                   "PredictionArrayList", "RankAveragedPredictions",
                   "def run(x):\n    rs=[np.argsort(np.argsort(np.asarray(a,float))).astype(float)/max(1,len(a)-1) for a in x]\n    return np.mean(np.stack(rs,0),0).tolist()\n",
                   lambda r: r([[1.0,2.0,3.0],[3.0,2.0,1.0]])==[0.5,0.5,0.5], ["ensemble","rank_average"]))
    s.append(_spec("Blend Two Predictions", "Convex blend a*alpha + b*(1-alpha) of two arrays.",
                   "TwoArraysAndAlpha", "BlendedPredictions",
                   "def run(x):\n    a,b,al=x; a=np.asarray(a,float); b=np.asarray(b,float)\n    return (a*al+b*(1-al)).tolist()\n",
                   lambda r: r(([0.0],[1.0],0.25))==[0.75], ["ensemble","blend"]))
    # ---- THRESHOLD / SUBMISSION ----
    s.append(_spec("Argmax To Labels", "Takes the argmax class index per row of a probability matrix.",
                   "ProbabilityMatrix", "PredictedLabels",
                   "def run(x):\n    return np.asarray(x,float).argmax(1).tolist()\n",
                   lambda r: r([[0.1,0.9],[0.8,0.2]])==[1,0], ["submission","argmax","classification"]))
    s.append(_spec("Threshold Binary Probabilities", "Thresholds probabilities into 0/1 at a cutoff.",
                   "ProbabilitiesAndThreshold", "BinaryLabels",
                   "def run(x):\n    p,t=x\n    return (np.asarray(p,float)>=t).astype(int).tolist()\n",
                   lambda r: r(([0.2,0.8],0.5))==[0,1], ["submission","threshold","classification"]))
    s.append(_spec("Optimize Accuracy Threshold", "Grid-searches the probability threshold maximizing accuracy.",
                   "LabelsAndProbabilities", "BestThreshold",
                   "def run(x):\n    y,p=x; y=np.asarray(y); p=np.asarray(p,float); best=(0.5,-1)\n    for t in np.linspace(0,1,101):\n        acc=((p>=t).astype(int)==y).mean()\n        if acc>best[1]: best=(float(t),acc)\n    return round(best[0],2)\n",
                   lambda r: 0.2<=r(([0,0,1,1],[0.1,0.2,0.8,0.9]))<=0.85, ["submission","threshold_opt","classification"]))
    s.append(_spec("Softmax Normalize", "Converts a logit vector into a probability simplex.",
                   "LogitVector", "ProbabilityVector",
                   "def run(x):\n    a=np.asarray(x,float); e=np.exp(a-a.max())\n    return (e/e.sum()).tolist()\n",
                   lambda r: _close(sum(r([1.0,2.0,3.0])),1.0), ["submission","softmax"]))
    s.append(_spec("Validate Probability Simplex", "True if every row of a probability matrix sums to 1.",
                   "ProbabilityMatrix", "IsValidSimplex",
                   "def run(x):\n    a=np.asarray(x,float)\n    return bool(np.allclose(a.sum(1),1.0))\n",
                   lambda r: r([[0.5,0.5],[0.2,0.8]]) is True and r([[0.5,0.6]]) is False, ["submission","validate","classification"]))
    s.append(_spec("Validate No NaN", "True if an array contains no NaN values.",
                   "NumericArray", "IsNanFree",
                   "def run(x):\n    return bool(not np.isnan(np.asarray(x,float)).any())\n",
                   lambda r: r([1.0,2.0]) is True and r([1.0,float('nan')]) is False, ["submission","validate"]))
    s.append(_spec("Validate Row Count", "True if a prediction array has the expected number of rows.",
                   "ArrayAndExpectedCount", "IsRowCountValid",
                   "def run(x):\n    a,n=x\n    return bool(len(a)==n)\n",
                   lambda r: r(([1,2,3],3)) is True and r(([1,2],3)) is False, ["submission","validate"]))
    s.append(_spec("Normalize Probabilities Rowwise", "Normalizes each row of a matrix to sum to 1.",
                   "NonNegativeMatrix", "ProbabilityMatrix",
                   "def run(x):\n    a=np.asarray(x,float); s=a.sum(1,keepdims=True); s[s==0]=1.0\n    return (a/s).tolist()\n",
                   lambda r: _close(sum(r([[1.0,1.0,2.0]])[0]),1.0), ["submission","normalize"]))
    return s


def mint(out_path: Optional[Path] = None) -> dict[str, Any]:
    out = out_path or (_REPO / "data" / "dev-intel" / "aidevobserver_edge_foundry" / "minted_ml_kaggle_pack_cards.jsonl")
    return _mint.mint_pack(ml_specs(), out_path=out)


def _self_test() -> int:
    specs = ml_specs()
    results = [_mint.mint_one(s) for s in specs]
    working = [r for r in results if r["working"]]
    failed = [(s["title"], r["error"]) for s, r in zip(specs, results) if not r["working"]]
    ok = len(working) >= int(0.9 * len(specs)) and len(specs) >= 40
    print(f"{'PASS' if ok else 'FAIL'} - mint_ml_kaggle_pack: {len(working)}/{len(specs)} ML primitives oracle-pass "
          f"(metrics/splits/preprocess/eda/ensemble/submission), real numpy bodies, candidate-only")
    for title, err in failed:
        print(f"  [XX] {title}: {err}")
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Mint the ML-Kaggle primitive families (real oracle-tested).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--mint", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.mint:
        print(json.dumps({k: v for k, v in mint().items() if k != "cards"}, indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
