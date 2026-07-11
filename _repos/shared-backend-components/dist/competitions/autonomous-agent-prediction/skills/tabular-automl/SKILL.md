---
name: tabular-automl
description: >
  A robust, general, multi-path self-tuning AutoML pipeline for tabular binary classification. Auto-discovers
  train/test/sample_submission, engineers features (NaN imputation, categorical encoding), races five
  complementary model families by stratified-k-fold out-of-fold AUC, and rank-blends the top three into a
  valid submission.csv. Runs entirely in the sandbox on CPU with sklearn/pandas/numpy — no LLM tokens.
---

# tabular-automl

The heavy lifting for this competition. Call it and read its JSON report; it does the ML so the agent doesn't
have to spend tokens deriving it.

## Run it

```bash
python skills/tabular-automl/scripts/automl.py --out submission.csv
# optional overrides:
python skills/tabular-automl/scripts/automl.py --train train.csv --test test.csv \
    --sample sample_submission.csv --out submission.csv --folds 8
```

If `--train/--test/--sample` are omitted it auto-discovers them (cwd, `./input/`, `/kaggle/input/`, `./data/`).

## What it does (multi-path, self-tuning)

1. **Detect** the id column (first column of `sample_submission.csv`) and the target column (the prediction
   column named there, or the train column absent from test).
2. **Engineer features** — median-impute numerics; one-hot encode low-cardinality categoricals, frequency-
   encode high-cardinality ones; align train/test columns (no leakage — encodings fit on train only).
3. **Race a portfolio** of five complementary models on the SAME stratified folds:
   `HistGradientBoosting` · `GradientBoosting` · `RandomForest` · `ExtraTrees` · `LogisticRegression`.
   Each is scored by **out-of-fold AUC** — the fair comparator.
4. **Blend** the top three paths by **rank-averaging** their test probabilities (robust to differing
   probability scales) and write `submission.csv` in the sample-submission format.
5. **Never crash the submission** — a failing model is dropped; if all fail, it emits the class prior.

## Output

Prints a JSON report: detected id/target, feature count, per-model CV AUC, the blended paths, and the
submission path. Use the per-model CV AUC to reason about model fit and as a tie-breaker when public scores
are close.

## Why this design wins the budget

Reusing this tested pipeline (a reusable *primitive*) instead of regenerating ML code every run keeps token
spend near zero and makes each submission reliable — the difference between a frugal agent that submits many
strong entries and one that burns its $2 budget writing brittle code.
